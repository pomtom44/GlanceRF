"""
Satellite list (names) from CelesTrak (stations + amateur). Same cache check as test_satellite_list.py:
cache valid 6 hours; if missing or expired, fetch from API. Error logging on timeouts.

Background loop: fetches sub-satellite locations from SatChecker (1 req/s), logs and updates cache file.
"""

import json
import math
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from glancerf.config import get_config, get_logger

try:
    from skyfield.api import load, wgs84, EarthSatellite
    _SKYFIELD_AVAILABLE = True
except ImportError:
    _SKYFIELD_AVAILABLE = False

_log = get_logger("satellite_pass.satellite_service")


def get_active_norad_set() -> set[int]:
    """Return NORAD ids that have at least one of show_passes, show_on_map, show_traces true in any satellite_pass cell. If none active, returns empty set (no locations/tracks fetched)."""
    config = get_config()
    layout = config.get("layout") or []
    if not isinstance(layout, list):
        return set()
    module_settings = config.get("module_settings") or {}
    if not isinstance(module_settings, dict):
        module_settings = {}
    active: set[int] = set()
    for row_idx, row in enumerate(layout):
        if not isinstance(row, list):
            continue
        for col_idx, cell_value in enumerate(row):
            if (cell_value or "").strip() != "satellite_pass":
                continue
            cell_key = f"{row_idx}_{col_idx}"
            settings = module_settings.get(cell_key)
            if not isinstance(settings, dict):
                continue
            raw = settings.get("sat_satellites")
            if not raw or not isinstance(raw, str):
                continue
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if not isinstance(data, dict):
                continue
            for norad_str, entry in data.items():
                if not isinstance(entry, dict):
                    continue
                try:
                    norad = int(norad_str)
                except (ValueError, TypeError):
                    continue
                if entry.get("show_passes") or entry.get("show_on_map") or entry.get("show_traces"):
                    active.add(norad)
    return active

_CELESTRAK_GP = "https://celestrak.org/NORAD/elements/gp.php"
_SATELLITE_LIST_GROUPS = ("stations", "amateur")
_CELESTRAK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://celestrak.org/",
}
_SATELLITE_LIST_TIMEOUT = 20
_SATELLITE_LIST_FILENAME = "satellite_list.json"
SATELLITE_LIST_CACHE_MAX_AGE_SECONDS = 6 * 3600  # 6 hours, same as test_satellite_list.py

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def _get_satellite_list_path() -> Path:
    """Path to satellite_list.json (same as test_satellite_list.py)."""
    return _PROJECT_DIR / "cache" / _SATELLITE_LIST_FILENAME


def _load_satellite_list_from_file() -> tuple[list[dict[str, Any]] | None, str | None]:
    """Load cache file. Returns (list of {norad_id, name}, updated_utc) or (None, None)."""
    path = _get_satellite_list_path()
    if not path.is_file():
        _log.debug("satellite list cache: file missing %s", path)
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        _log.debug("satellite list cache: load failed %s", e)
        return None, None
    if not isinstance(data, dict):
        _log.debug("satellite list cache: invalid format (not dict)")
        return None, None
    updated_utc = data.get("updated_utc") if isinstance(data.get("updated_utc"), str) else None
    satellites = data.get("satellites")
    if not isinstance(satellites, list):
        _log.debug("satellite list cache: no satellites list, updated_utc=%s", updated_utc or "(none)")
        return None, updated_utc
    out: list[dict[str, Any]] = []
    for s in satellites:
        if isinstance(s, dict) and isinstance(s.get("norad_id"), (int, float)) and s.get("name"):
            out.append({"norad_id": int(s["norad_id"]), "name": str(s["name"]).strip()})
    _log.debug("satellite list cache: loaded %d satellites from file, updated_utc=%s", len(out) if out else 0, updated_utc or "(none)")
    return (out if out else None), updated_utc


def _is_list_cache_fresh(updated_utc_str: str | None) -> bool:
    """True if updated_utc is within 6 hours (same as test_satellite_list.py)."""
    if not updated_utc_str or not updated_utc_str.strip():
        return False
    try:
        dt = datetime.fromisoformat(updated_utc_str.replace("Z", "+00:00"))
        age_sec = datetime.now(timezone.utc).timestamp() - dt.timestamp()
        return 0 <= age_sec < SATELLITE_LIST_CACHE_MAX_AGE_SECONDS
    except (ValueError, TypeError):
        return False


def _fetch_satellite_list_from_celestrak() -> list[dict[str, Any]]:
    """Fetch list from CelesTrak (stations + amateur). Same request as test_satellite_list.py. Logs error on timeout."""
    seen: set[int] = set()
    result: list[dict[str, Any]] = []
    with httpx.Client(timeout=_SATELLITE_LIST_TIMEOUT) as client:
        for group in _SATELLITE_LIST_GROUPS:
            try:
                r = client.get(_CELESTRAK_GP, params={"GROUP": group, "FORMAT": "json"}, headers=_CELESTRAK_HEADERS)
                r.raise_for_status()
                data = r.json()
            except httpx.TimeoutException as e:
                _log.error("satellite list: CelesTrak timeout (GROUP=%s, timeout=%ss): %s", group, _SATELLITE_LIST_TIMEOUT, e)
                continue
            except httpx.ConnectError as e:
                _log.error("satellite list: CelesTrak connection error (GROUP=%s): %s", group, e)
                continue
            except httpx.HTTPStatusError as e:
                _log.debug("satellite list: CelesTrak fetch %s failed: %s", group, e)
                continue
            except Exception as e:
                _log.debug("satellite list: CelesTrak fetch %s failed: %s", group, e)
                continue
            if not isinstance(data, list):
                continue
            for obj in data:
                if not isinstance(obj, dict):
                    continue
                norad = obj.get("NORAD_CAT_ID")
                name = (obj.get("OBJECT_NAME") or "").strip()
                if norad is not None and name and int(norad) not in seen:
                    seen.add(int(norad))
                    result.append({"norad_id": int(norad), "name": name})
    result.sort(key=lambda x: (x["name"].upper(), x["norad_id"]))
    _log.debug("satellite list: fetched from CelesTrak, %d satellites", len(result))
    return result


def _save_satellite_list_to_file(satellites: list[dict[str, Any]]) -> None:
    """Save satellite list to cache with updated_utc (same format as test_satellite_list.py)."""
    path = _get_satellite_list_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "satellites": satellites,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    _log.debug("satellite list cache: updated. file=%s entries=%d", path, len(satellites))


def get_satellite_list_cached() -> list[dict[str, Any]]:
    """
    Same cache check as test_satellite_list.py:
    - If cache exists and updated_utc within 6 hours: use cache.
    - Else: fetch from CelesTrak (errors/timeouts logged), update cache, return.
    """
    path = _get_satellite_list_path()
    _log.debug("satellite list cache: path=%s exists=%s", path, path.is_file())

    loaded, updated_utc = _load_satellite_list_from_file()
    if loaded is not None and _is_list_cache_fresh(updated_utc):
        age_sec = None
        if updated_utc:
            try:
                dt = datetime.fromisoformat(updated_utc.replace("Z", "+00:00"))
                age_sec = datetime.now(timezone.utc).timestamp() - dt.timestamp()
            except (ValueError, TypeError):
                pass
        _log.debug("satellite list: from cache (valid, not older than 6 hours). count=%d updated_utc=%s age_sec=%s", len(loaded), updated_utc or "(none)", age_sec)
        return loaded

    reason = "data missing" if (loaded is None and not path.is_file()) else "data older than 6 hours"
    _log.debug("satellite list: updating cache (%s)...", reason)
    list_from_api = _fetch_satellite_list_from_celestrak()
    if not list_from_api:
        _log.debug("satellite list: CelesTrak unavailable. No cache update. Using existing data if any.")
        return loaded or []
    _save_satellite_list_to_file(list_from_api)
    _log.debug("satellite list: cache updated. Data from cache: count=%d", len(list_from_api))
    return list_from_api


# --- Satellite locations fetch loop (log + cache file) ---

_SATELLITE_LOCATIONS_FILENAME = "satellite_locations.json"
SATELLITE_LOCATIONS_CACHE_MAX_AGE_SECONDS = 5 * 60  # 5 min; if older when read, cache is cleared and empty returned
_SATCHECKER_RATE_LIMIT_SEC = 1.0
_SATCHECKER_EPHEMERIS_URL = "https://satchecker.cps.iau.org/ephemeris/catalog-number/"
_SATCHECKER_JDSTEP_URL = "https://satchecker.cps.iau.org/ephemeris/catalog-number-jdstep/"
_SATCHECKER_TIMEOUT = 25
_LOCATIONS_LOOP_PAUSE_SEC = 5  # short pause between passes so we keep looping and updating live positions

_SATELLITE_TRACKS_FILENAME = "satellite_tracks.json"
TRACKS_CACHE_MAX_AGE_SECONDS = 30 * 60  # 30 min; data from cache is valid for up to 30 min when reading
_TRACKS_LOOP_INTERVAL_SEC = 10 * 60  # overwrite cache every 10 min
_TRACKS_TAIL_MINUTES = 30  # past 30 min
_TRACKS_LEAD_MINUTES = 90  # future 90 min
_TRACKS_STEP_MINUTES = 2  # 2 min between points


def _utc_now_julian_date() -> float:
    return 2440587.5 + (datetime.now(timezone.utc).timestamp() / 86400.0)


def _gcrs_to_lat_lon(x_km: float, y_km: float, z_km: float) -> tuple[float, float] | tuple[None, None]:
    r = math.sqrt(x_km * x_km + y_km * y_km + z_km * z_km)
    if r < 1e-6:
        return (None, None)
    lat_rad = math.asin(z_km / r)
    lon_rad = math.atan2(y_km, x_km)
    return (math.degrees(lat_rad), math.degrees(lon_rad))


def _fetch_satchecker_position(
    catalog: int,
    latitude: float = 0.0,
    longitude: float = 0.0,
    elevation: float = 0.0,
    julian_date: float | None = None,
) -> tuple[float, float] | tuple[None, None]:
    if julian_date is None:
        julian_date = _utc_now_julian_date()
    params = {
        "catalog": catalog,
        "latitude": latitude,
        "longitude": longitude,
        "elevation": elevation,
        "julian_date": julian_date,
        "min_altitude": -90,
    }
    try:
        with httpx.Client(timeout=_SATCHECKER_TIMEOUT) as client:
            r = client.get(_SATCHECKER_EPHEMERIS_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        _log.debug("satellite location: SatChecker NORAD %s failed: %s", catalog, e)
        return (None, None)
    if not isinstance(data, dict):
        return (None, None)
    fields = data.get("fields")
    data_list = data.get("data")
    if not isinstance(fields, list) or not isinstance(data_list, list) or len(data_list) < 1:
        return (None, None)
    try:
        idx = fields.index("satellite_gcrs_km")
    except ValueError:
        return (None, None)
    row = data_list[0]
    if not isinstance(row, (list, tuple)) or len(row) <= idx:
        return (None, None)
    vec = row[idx]
    if not isinstance(vec, (list, tuple)) or len(vec) < 3:
        return (None, None)
    x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
    lat, lon = _gcrs_to_lat_lon(x, y, z)
    return (lat, lon) if lat is not None else (None, None)


def _get_satellite_locations_path() -> Path:
    """Path to satellite_locations.json in project cache folder."""
    return _PROJECT_DIR / "cache" / _SATELLITE_LOCATIONS_FILENAME


def _normalize_lon_delta(delta_lon: float) -> float:
    """Normalize longitude difference to (-180, 180] for velocity."""
    while delta_lon > 180:
        delta_lon -= 360
    while delta_lon <= -180:
        delta_lon += 360
    return delta_lon


def _save_satellite_locations_to_file(
    positions: dict[int, tuple[float, float]],
    position_updated_utc: dict[int, str],
    velocities: dict[int, tuple[float, float]],
) -> None:
    """Save positions, per-norad timestamps and velocities to satellite_locations.json."""
    path = _get_satellite_locations_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "updated_utc": now_iso,
        "positions": {str(n): [round(lat, 4), round(lon, 4)] for n, (lat, lon) in positions.items()},
        "position_updated_utc": {str(n): t for n, t in position_updated_utc.items()},
        "velocities": {str(n): [round(vlat, 6), round(vlon, 6)] for n, (vlat, vlon) in velocities.items()},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    _log.debug("satellite locations cache: updated file=%s entries=%d", path, len(positions))


def _load_satellite_locations_from_file() -> tuple[
    dict[int, tuple[float, float]] | None,
    str | None,
    dict[int, str],
    dict[int, tuple[float, float]],
]:
    """Load from satellite_locations.json. Returns (positions, updated_utc, position_updated_utc_by_norad, velocities)."""
    path = _get_satellite_locations_path()
    if not path.is_file():
        return None, None, {}, {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None, None, {}, {}
    if not isinstance(data, dict):
        return None, None, {}, {}
    updated_utc = data.get("updated_utc") if isinstance(data.get("updated_utc"), str) else None
    raw = data.get("positions")
    if not isinstance(raw, dict):
        return None, updated_utc, {}, {}
    out: dict[int, tuple[float, float]] = {}
    for k, v in raw.items():
        try:
            norad = int(k)
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                lat, lon = float(v[0]), float(v[1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    out[norad] = (lat, lon)
        except (ValueError, TypeError):
            continue
    raw_utc = data.get("position_updated_utc")
    position_updated_utc: dict[int, str] = {}
    if isinstance(raw_utc, dict):
        for k, v in raw_utc.items():
            if isinstance(v, str) and v.strip():
                try:
                    position_updated_utc[int(k)] = v.strip()
                except (ValueError, TypeError):
                    pass
    raw_vel = data.get("velocities")
    velocities: dict[int, tuple[float, float]] = {}
    if isinstance(raw_vel, dict):
        for k, v in raw_vel.items():
            try:
                norad = int(k)
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    vlat, vlon = float(v[0]), float(v[1])
                    velocities[norad] = (vlat, vlon)
            except (ValueError, TypeError):
                pass
    return (out if out else None), updated_utc, position_updated_utc, velocities


def _is_locations_cache_stale(updated_utc_str: str | None) -> bool:
    """True if updated_utc is missing or older than SATELLITE_LOCATIONS_CACHE_MAX_AGE_SECONDS (5 min)."""
    if not updated_utc_str or not updated_utc_str.strip():
        return True
    try:
        dt = datetime.fromisoformat(updated_utc_str.replace("Z", "+00:00"))
        age_sec = datetime.now(timezone.utc).timestamp() - dt.timestamp()
        return age_sec < 0 or age_sec >= SATELLITE_LOCATIONS_CACHE_MAX_AGE_SECONDS
    except (ValueError, TypeError):
        return True


def get_satellite_locations_cached() -> tuple[
    dict[int, tuple[float, float]],
    dict[int, tuple[float, float]],
    str | None,
    dict[int, str],
]:
    """Return (positions, velocities, updated_utc, position_updated_utc) from cache. Only include positions updated within 5 min (per-satellite). position_updated_utc is per NORAD ISO UTC so the client can compute real cache age for estimation."""
    loaded, updated_utc, position_updated_utc, velocities = _load_satellite_locations_from_file()
    if loaded is None or not loaded:
        return {}, {}, None, {}
    now_ts = datetime.now(timezone.utc).timestamp()
    max_age = SATELLITE_LOCATIONS_CACHE_MAX_AGE_SECONDS
    fresh_positions: dict[int, tuple[float, float]] = {}
    fresh_velocities: dict[int, tuple[float, float]] = {}
    fresh_position_updated_utc: dict[int, str] = {}
    for norad, pos in loaded.items():
        ts_str = position_updated_utc.get(norad) if position_updated_utc else None
        if not ts_str or not ts_str.strip():
            continue
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            age_sec = now_ts - dt.timestamp()
            if age_sec < 0 or age_sec >= max_age:
                continue
        except (ValueError, TypeError):
            continue
        fresh_positions[norad] = pos
        if norad in velocities:
            fresh_velocities[norad] = velocities[norad]
        fresh_position_updated_utc[norad] = ts_str
    if not fresh_positions and loaded and (not updated_utc or _is_locations_cache_stale(updated_utc)):
        _log.debug("satellite locations cache: file or all per-satellite timestamps older than 5 min, returning empty")
    return fresh_positions, fresh_velocities, updated_utc if fresh_positions else None, fresh_position_updated_utc


def _fetch_locations_and_log() -> None:
    """Fetch one position at a time from SatChecker (1 req/s). Compute velocity from previous position; write cache after each success. Only fetches for NORADs that have at least one of show_passes/show_on_map/show_traces enabled."""
    active = get_active_norad_set()
    if not active:
        _log.debug("satellite locations fetch: no active satellites (enable Show Passes/On Map/Traces in settings), skip")
        return
    sat_list = get_satellite_list_cached()
    if not sat_list:
        _log.debug("satellite locations fetch: no list, skip")
        return
    sat_list = [s for s in sat_list if s.get("norad_id") in active]
    if not sat_list:
        return
    loaded, _, position_updated_utc, velocities = _load_satellite_locations_from_file()
    positions: dict[int, tuple[float, float]] = dict(loaded) if loaded else {}
    position_updated_utc = dict(position_updated_utc)
    velocities = dict(velocities)
    jd = _utc_now_julian_date()
    _log.debug("satellite locations fetch: started, %d satellites (~%d s at 1 req/s)", len(sat_list), len(sat_list))
    failed = 0
    now_utc = datetime.now(timezone.utc)
    for i, s in enumerate(sat_list):
        norad = s["norad_id"]
        name = (s.get("name") or "").strip() or str(norad)
        lat, lon = _fetch_satchecker_position(norad, 0.0, 0.0, 0.0, jd)
        if lat is not None and lon is not None:
            _log.debug("satellite location: NORAD %s %s lat=%.4f lon=%.4f", norad, name, lat, lon)
            now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            old = positions.get(norad)
            old_time_str = position_updated_utc.get(norad)
            if old is not None and old_time_str and old_time_str.strip():
                try:
                    old_dt = datetime.fromisoformat(old_time_str.replace("Z", "+00:00"))
                    dt_sec = (now_utc - old_dt).total_seconds()
                    if dt_sec > 0.5:
                        vlat = (lat - old[0]) / dt_sec
                        delta_lon = _normalize_lon_delta(lon - old[1])
                        vlon = delta_lon / dt_sec
                        velocities[norad] = (vlat, vlon)
                except (ValueError, TypeError):
                    pass
            positions[norad] = (lat, lon)
            position_updated_utc[norad] = now_iso
            if norad not in velocities:
                velocities[norad] = (0.0, 0.0)
            _save_satellite_locations_to_file(positions, position_updated_utc, velocities)
            now_utc = datetime.now(timezone.utc)
        else:
            failed += 1
        if i < len(sat_list) - 1:
            time.sleep(_SATCHECKER_RATE_LIMIT_SEC)
    _log.debug(
        "satellite locations fetch: pass finished, %d positions (%d failed - SatChecker has no/ephemeris for those NORAD IDs)",
        len(positions),
        failed,
    )


_locations_thread: threading.Thread | None = None
_locations_stop = threading.Event()


def _locations_loop() -> None:
    while True:
        try:
            _fetch_locations_and_log()
        except Exception as e:
            _log.debug("satellite locations fetch: error %s", e)
        if _locations_stop.wait(timeout=_LOCATIONS_LOOP_PAUSE_SEC):
            break


def start_satellite_locations_fetch_loop() -> None:
    """Start background thread that fetches satellite locations (SatChecker, 1 req/s), logs and updates cache file."""
    global _locations_thread
    if _locations_thread is not None and _locations_thread.is_alive():
        return
    _locations_stop.clear()
    _locations_thread = threading.Thread(target=_locations_loop, daemon=True)
    _locations_thread.start()
    _log.debug("satellite locations fetch loop: started (log + cache file)")


def stop_satellite_locations_fetch_loop() -> None:
    """Stop the satellite locations fetch loop."""
    global _locations_thread
    _locations_stop.set()
    if _locations_thread is not None:
        _locations_thread.join(timeout=2.0)
        _locations_thread = None
    _log.debug("satellite locations fetch loop: stopped")


# ---- Satellite tracks (ground track tail 30 min + lead 90 min), cache refreshed every 10 min ----

def _get_satellite_tracks_path() -> Path:
    """Path to satellite_tracks.json in project cache folder."""
    return _PROJECT_DIR / "cache" / _SATELLITE_TRACKS_FILENAME


def _fetch_satchecker_track(catalog: int) -> tuple[list[tuple[float, float]], list[tuple[float, float]]] | None:
    """Fetch ground track from SatChecker jdstep: tail (past 30 min) and lead (future 90 min). Returns (tail, lead) or None."""
    jd_now = _utc_now_julian_date()
    # 30 min = 30/1440 JD, 90 min = 90/1440 JD, 2 min step = 2/1440 JD
    startjd = jd_now - (_TRACKS_TAIL_MINUTES / 1440.0)
    stopjd = jd_now + (_TRACKS_LEAD_MINUTES / 1440.0)
    stepjd = _TRACKS_STEP_MINUTES / 1440.0
    params = {
        "catalog": catalog,
        "latitude": 0.0,
        "longitude": 0.0,
        "elevation": 0.0,
        "startjd": startjd,
        "stopjd": stopjd,
        "stepjd": stepjd,
        "min_altitude": -90,
    }
    try:
        with httpx.Client(timeout=_SATCHECKER_TIMEOUT) as client:
            r = client.get(_SATCHECKER_JDSTEP_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        _log.debug("satellite track: SatChecker NORAD %s failed: %s", catalog, e)
        return None
    if not isinstance(data, dict):
        return None
    fields = data.get("fields")
    data_list = data.get("data")
    if not isinstance(fields, list) or not isinstance(data_list, list):
        return None
    try:
        idx_gcrs = fields.index("satellite_gcrs_km")
        idx_jd = fields.index("julian_date")
    except ValueError:
        return None
    tail: list[tuple[float, float]] = []
    lead: list[tuple[float, float]] = []
    for row in data_list:
        if not isinstance(row, (list, tuple)) or len(row) <= max(idx_gcrs, idx_jd):
            continue
        vec = row[idx_gcrs]
        jd_val = row[idx_jd]
        if not isinstance(vec, (list, tuple)) or len(vec) < 3:
            continue
        try:
            x, y, z = float(vec[0]), float(vec[1]), float(vec[2])
            jd = float(jd_val)
        except (ValueError, TypeError):
            continue
        lat, lon = _gcrs_to_lat_lon(x, y, z)
        if lat is None:
            continue
        pt = (round(lat, 4), round(lon, 4))
        if jd <= jd_now:
            tail.append(pt)
        else:
            lead.append(pt)
    return (tail, lead)


def _save_satellite_tracks_to_file(tracks: dict[int, tuple[list[tuple[float, float]], list[tuple[float, float]]]]) -> None:
    """Save tracks to satellite_tracks.json. Value per norad: (tail, lead) as lists of [lat, lon]. Atomic write."""
    path = _get_satellite_tracks_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict[str, list[list[float]]]] = {}
    for norad, (tail_list, lead_list) in tracks.items():
        out[str(norad)] = {
            "tail": [[p[0], p[1]] for p in tail_list],
            "lead": [[p[0], p[1]] for p in lead_list],
        }
    data = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracks": out,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    _log.debug("satellite tracks cache: updated file=%s entries=%d", path, len(tracks))


def _load_satellite_tracks_from_file() -> tuple[dict[int, tuple[list[tuple[float, float]], list[tuple[float, float]]]] | None, str | None]:
    """Load tracks from satellite_tracks.json. Returns (tracks_dict, updated_utc) or (None, None)."""
    path = _get_satellite_tracks_path()
    if not path.is_file():
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    updated_utc = data.get("updated_utc") if isinstance(data.get("updated_utc"), str) else None
    raw = data.get("tracks")
    if not isinstance(raw, dict):
        return None, updated_utc
    out: dict[int, tuple[list[tuple[float, float]], list[tuple[float, float]]]] = {}
    for k, v in raw.items():
        try:
            norad = int(k)
            if not isinstance(v, dict):
                continue
            tail_raw = v.get("tail")
            lead_raw = v.get("lead")
            tail = []
            if isinstance(tail_raw, list):
                for p in tail_raw:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        tail.append((float(p[0]), float(p[1])))
            lead = []
            if isinstance(lead_raw, list):
                for p in lead_raw:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        lead.append((float(p[0]), float(p[1])))
            out[norad] = (tail, lead)
        except (ValueError, TypeError):
            continue
    return (out if out else None), updated_utc


def _is_tracks_cache_stale(updated_utc_str: str | None) -> bool:
    """True if updated_utc is missing or older than TRACKS_CACHE_MAX_AGE_SECONDS (30 min)."""
    if not updated_utc_str or not updated_utc_str.strip():
        return True
    try:
        dt = datetime.fromisoformat(updated_utc_str.replace("Z", "+00:00"))
        age_sec = datetime.now(timezone.utc).timestamp() - dt.timestamp()
        return age_sec < 0 or age_sec >= TRACKS_CACHE_MAX_AGE_SECONDS
    except (ValueError, TypeError):
        return True


def get_satellite_tracks_cached() -> tuple[dict[int, tuple[list[tuple[float, float]], list[tuple[float, float]]]], str | None]:
    """Return (tracks, updated_utc) from cache. Tracks only if cache is fresh (< 30 min); else empty."""
    loaded, updated_utc = _load_satellite_tracks_from_file()
    if loaded is not None and updated_utc and not _is_tracks_cache_stale(updated_utc):
        return loaded, updated_utc
    if loaded and _is_tracks_cache_stale(updated_utc):
        _log.debug("satellite tracks cache: older than 30 min, returning empty")
    return {}, None


_NEXT_PASS_TRACKS_STEP_MINUTES = 2


def _next_pass_gridsquare_to_lat_lon(grid: str) -> tuple[float, float] | None:
    """Convert Maidenhead gridsquare (4 or 6 char) to (lat, lon) in degrees. Returns None if invalid."""
    grid = (grid or "").strip().upper()
    if len(grid) < 4:
        return None
    if not re.match(r"^[A-R][A-R][0-9][0-9]([A-X][A-X])?$", grid):
        return None
    lon_deg = (ord(grid[0]) - 65) * 20 + int(grid[2]) * 2 - 180
    lat_deg = (ord(grid[1]) - 65) * 10 + int(grid[3]) - 90
    if len(grid) >= 6:
        lon_deg += (ord(grid[4]) - 65) * (2.0 / 24) + (2.0 / 24) / 2
        lat_deg += (ord(grid[5]) - 65) * (1.0 / 24) + (1.0 / 24) / 2
    return (lat_deg, lon_deg)


def parse_location_to_lat_lon(location_str: str) -> tuple[float, float] | None:
    """
    Parse setup_location-style string to (lat, lon).
    Accepts: gridsquare (4 or 6 char), or "lat,lon" (e.g. -43.5,172.6).
    Returns None if invalid or empty.
    """
    s = (location_str or "").strip()
    if not s:
        return None
    if re.match(r"^[A-Ra-r][A-Ra-r][0-9][0-9]([A-Xa-x][A-Xa-x])?$", s):
        return _next_pass_gridsquare_to_lat_lon(s)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            pass
    return None


def _next_pass_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in km between two (lat, lon) points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(min(1.0, a)))
    return r * c


_TLE_CACHE: dict[int, tuple[str, str, float]] = {}
_TLE_CACHE_MAX_AGE_SEC = 6 * 3600
_CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php"
_VISIBLE_PASS_MIN_EL_DEG = 10.0


def _skyfield_time_to_datetime(t: Any) -> datetime:
    """Convert Skyfield Time to Python datetime (handles numpy scalar)."""
    dt = t.utc_datetime()
    if hasattr(dt, "item"):
        dt = dt.item()
    if isinstance(dt, datetime):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if hasattr(dt, "timestamp"):
        return datetime.fromtimestamp(dt.timestamp(), tz=timezone.utc)
    try:
        return datetime.fromtimestamp(float(dt) / 1e9, tz=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def _fetch_tle(norad: int) -> tuple[str, str] | None:
    """Fetch TLE for NORAD from CelesTrak. Returns (line1, line2) or None. Caches in memory."""
    now = time.time()
    if norad in _TLE_CACHE:
        _, _, fetched_at = _TLE_CACHE[norad]
        if now - fetched_at < _TLE_CACHE_MAX_AGE_SEC:
            return (_TLE_CACHE[norad][0], _TLE_CACHE[norad][1])
    try:
        r = httpx.get(_CELESTRAK_TLE_URL, params={"CATNR": norad}, timeout=15.0)
        r.raise_for_status()
        lines = [s.strip() for s in r.text.strip().splitlines() if s.strip()]
        if len(lines) >= 3:
            line1, line2 = lines[1], lines[2]
            if line1.startswith("1 ") and line2.startswith("2 "):
                _TLE_CACHE[norad] = (line1, line2, now)
                return (line1, line2)
    except Exception as e:
        _log.debug("TLE fetch NORAD %s: %s", norad, e)
    return None


def _next_pass_visible(
    obs_lat: float,
    obs_lon: float,
) -> dict[str, Any] | None:
    """
    Compute next visible passes (rise above horizon) using TLE/Skyfield.
    Returns dict with text, next_pass, passes; or None if unavailable / no passes.
    """
    if not _SKYFIELD_AVAILABLE:
        return None
    active = get_active_norad_set()
    if not active:
        return None
    sat_list, _ = _load_satellite_list_from_file()
    if not sat_list:
        return None
    names_by_norad = {s["norad_id"]: s["name"] for s in sat_list}
    now = datetime.now(timezone.utc)
    results: list[tuple[datetime, datetime, int, str, float]] = []

    for norad in sorted(active):
        tle = _fetch_tle(norad)
        if not tle:
            continue
        line1, line2 = tle
        name = names_by_norad.get(norad) or ("NORAD %s" % norad)
        try:
            ts = load.timescale()
            sat = EarthSatellite(line1, line2, name, ts)
            observer = wgs84.latlon(obs_lat, obs_lon)
            t0 = ts.utc(now)
            t1 = ts.utc(now.year, now.month, now.day + 2, 0, 0, 0)
            times, events = sat.find_events(observer, t0, t1, altitude_degrees=_VISIBLE_PASS_MIN_EL_DEG)
            rise_time = None
            set_time = None
            for i, ev in enumerate(events):
                if ev == 0:
                    rise_time = times[i]
                    break
            if rise_time is None:
                continue
            for i, ev in enumerate(events):
                if ev == 2:
                    st = times[i]
                    if _skyfield_time_to_datetime(st) > _skyfield_time_to_datetime(rise_time):
                        set_time = st
                        break
            if set_time is None:
                continue
            diff = sat - observer
            range_km = float(diff.at(rise_time).distance().km)
            rise_dt = _skyfield_time_to_datetime(rise_time)
            set_dt = _skyfield_time_to_datetime(set_time)
            if set_dt <= rise_dt:
                continue
            results.append((rise_dt, set_dt, norad, name, range_km))
        except Exception as e:
            _log.debug("visible pass NORAD %s: %s", norad, e)
            continue

    if not results:
        return None
    results.sort(key=lambda x: x[0])
    lines = [
        "Next visible passes (rise above %s deg):" % _VISIBLE_PASS_MIN_EL_DEG,
        "-" * 60,
    ]
    for rise_dt, set_dt, norad, name, range_km in results[:15]:
        lines.append("%s  NORAD %-6s  %s  (%.0f km at rise)" % (rise_dt.strftime("%Y-%m-%d %H:%M UTC"), norad, name[:32], range_km))
    lines.append("-" * 60)
    soonest = results[0]
    rise_dt, set_dt, norad, name, range_km = soonest
    lines.append("Next pass: %s  %s (NORAD %s)" % (rise_dt.strftime("%Y-%m-%d %H:%M UTC"), name, norad))
    utc_str = rise_dt.strftime("%Y-%m-%d %H:%M UTC")
    return {
        "text": "\n".join(lines),
        "tracks_updated_utc": "",
        "next_pass": {
            "utc": utc_str,
            "norad": norad,
            "name": name,
            "km": round(range_km, 0),
        },
        "passes": [
            {"utc": r[0].strftime("%Y-%m-%d %H:%M UTC"), "norad": r[2], "name": r[3], "km": round(r[4], 0)}
            for r in results
        ],
    }


def get_next_pass_from_cache(
    obs_lat: float,
    obs_lon: float,
) -> dict[str, Any]:
    """
    Compute next pass times. Prefers visible passes (TLE/Skyfield: rise above horizon).
    Falls back to closest ground-track approach from cache when TLE data is unavailable.
    Returns dict with: text, tracks_updated_utc, next_pass, passes.
    """
    visible = _next_pass_visible(obs_lat, obs_lon)
    if visible and visible.get("next_pass") and visible.get("passes"):
        return visible

    out: dict[str, Any] = {
        "text": "",
        "tracks_updated_utc": "",
        "next_pass": None,
        "passes": [],
    }
    sat_list, _ = _load_satellite_list_from_file()
    tracks, tracks_updated_utc = _load_satellite_tracks_from_file()
    if not sat_list:
        out["text"] = "No satellite list in cache. Run the app or refresh to populate cache."
        return out
    if not tracks or not tracks_updated_utc:
        out["text"] = "No tracks in cache or missing updated_utc. Enable satellites and wait for tracks to populate."
        return out
    try:
        base_dt = datetime.fromisoformat(tracks_updated_utc.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        base_dt = datetime.now(timezone.utc)
    names_by_norad = {s["norad_id"]: s["name"] for s in sat_list}
    now_utc = datetime.now(timezone.utc)
    results: list[tuple[datetime, int, str, float]] = []
    for norad, (_, lead) in tracks.items():
        if not lead:
            continue
        best_idx = 0
        best_km = 1e9
        for i, (plat, plon) in enumerate(lead):
            km = _next_pass_haversine_km(obs_lat, obs_lon, plat, plon)
            if km < best_km:
                best_km = km
                best_idx = i
        pass_dt = base_dt + timedelta(minutes=best_idx * _NEXT_PASS_TRACKS_STEP_MINUTES)
        if pass_dt < now_utc:
            continue
        name = names_by_norad.get(norad) or ("NORAD %s" % norad)
        results.append((pass_dt, norad, name, best_km))
    results.sort(key=lambda x: x[0])
    lines = [
        "Tracks cache updated: %s" % tracks_updated_utc,
        "Next pass times (closest approach of sub-satellite point):",
        "-" * 60,
    ]
    if not results:
        lines.append("No future passes in cached lead window (lead is ~90 min from cache time).")
        out["text"] = "\n".join(lines)
        out["tracks_updated_utc"] = tracks_updated_utc
        return out
    for pass_dt, norad, name, km in results[:10]:
        lines.append("%s  NORAD %-6s  %s  (%.0f km)" % (pass_dt.strftime("%Y-%m-%d %H:%M UTC"), norad, name[:32], km))
    lines.append("-" * 60)
    soonest = results[0]
    lines.append("Next pass: %s  %s (NORAD %s)  %.0f km" % (
        soonest[0].strftime("%Y-%m-%d %H:%M UTC"), soonest[2], soonest[1], soonest[3]))
    out["text"] = "\n".join(lines)
    out["tracks_updated_utc"] = tracks_updated_utc
    out["next_pass"] = {
        "utc": soonest[0].strftime("%Y-%m-%d %H:%M UTC"),
        "norad": soonest[1],
        "name": soonest[2],
        "km": round(soonest[3], 0),
    }
    out["passes"] = [
        {"utc": dt.strftime("%Y-%m-%d %H:%M UTC"), "norad": n, "name": name, "km": round(km, 0)}
        for dt, n, name, km in results
    ]
    return out


def _fetch_tracks_and_log() -> None:
    """Loop through cache list, fetch tail+lead track for each sat (1 req/s), write cache after each so map can show tracks early. Only fetches for NORADs that have at least one of show_passes/show_on_map/show_traces enabled."""
    active = get_active_norad_set()
    if not active:
        _log.debug("satellite tracks fetch: no active satellites (enable Show Passes/On Map/Traces in settings), skip")
        return
    sat_list = get_satellite_list_cached()
    if not sat_list:
        _log.debug("satellite tracks fetch: no list, skip")
        return
    sat_list = [s for s in sat_list if s.get("norad_id") in active]
    if not sat_list:
        return
    _log.debug("satellite tracks fetch: started, %d satellites (~%d s at 1 req/s)", len(sat_list), len(sat_list))
    tracks: dict[int, tuple[list[tuple[float, float]], list[tuple[float, float]]]] = {}
    for i, s in enumerate(sat_list):
        norad = s["norad_id"]
        result = _fetch_satchecker_track(norad)
        if result is not None:
            tail, lead = result
            if tail or lead:
                tracks[norad] = (tail, lead)
                _save_satellite_tracks_to_file(tracks)
        if i < len(sat_list) - 1:
            time.sleep(_SATCHECKER_RATE_LIMIT_SEC)
    _log.debug("satellite tracks fetch: pass finished, %d tracks", len(tracks))


_tracks_thread: threading.Thread | None = None
_tracks_stop = threading.Event()


def _tracks_loop() -> None:
    """Run tracks fetch every 10 min (from start of each run)."""
    while True:
        start = time.monotonic()
        try:
            _fetch_tracks_and_log()
        except Exception as e:
            _log.debug("satellite tracks fetch: error %s", e)
        elapsed = time.monotonic() - start
        wait_sec = max(0.0, _TRACKS_LOOP_INTERVAL_SEC - elapsed)
        if _tracks_stop.wait(timeout=wait_sec):
            break


def start_satellite_tracks_fetch_loop() -> None:
    """Start background thread that fetches ground tracks (tail 30 min, lead 90 min) every 10 min."""
    global _tracks_thread
    if _tracks_thread is not None and _tracks_thread.is_alive():
        return
    _tracks_stop.clear()
    _tracks_thread = threading.Thread(target=_tracks_loop, daemon=True)
    _tracks_thread.start()
    _log.debug("satellite tracks fetch loop: started (refresh every 10 min)")


def stop_satellite_tracks_fetch_loop() -> None:
    """Stop the satellite tracks fetch loop."""
    global _tracks_thread
    _tracks_stop.set()
    if _tracks_thread is not None:
        _tracks_thread.join(timeout=2.0)
        _tracks_thread = None
    _log.debug("satellite tracks fetch loop: stopped")
