"""
Satellite list and pass prediction using CelesTrak TLEs and Skyfield.
Module-owned; no core imports except logging and config (for list path and pruning).
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from skyfield.api import EarthSatellite, load, wgs84

from glancerf.logging_config import get_logger

_log = get_logger("satellite_pass.satellite_service")

_CELESTRAK_GP = "https://celestrak.org/NORAD/elements/gp.php"
_SATELLITE_LIST_GROUPS = ("stations", "amateur")
_SATELLITE_LIST_TIMEOUT = 20
_TLE_TIMEOUT = 15
_PASS_SEARCH_DAYS = 2
_MIN_ELEVATION_DEG = 0.5
_SATELLITE_LIST_FILENAME = "satellite_list.json"
_LIST_MAX_AGE_SECONDS = 86400  # 24 hours
_MODULE_ID_SATELLITE_PASS = "satellite_pass"
_SETTING_SELECTED_SATELLITES = "selected_satellites"

_ts = None
_eph = None


def _get_timescale_and_ephemeris():
    global _ts, _eph
    if _ts is None:
        _ts = load.timescale()
    if _eph is None:
        try:
            _eph = load("de421.bsp")
        except Exception as e:
            _log.debug("Skyfield de421 load failed, using built-in: %s", e)
            _eph = load("de421.bsp")  # may fail; caller handles
    return _ts, _eph


def fetch_satellite_list() -> list[dict[str, Any]]:
    """
    Fetch list of trackable satellites from CelesTrak (stations + amateur).
    Returns list of {"norad_id": int, "name": str}, sorted by name.
    """
    seen: set[int] = set()
    result: list[dict[str, Any]] = []
    with httpx.Client(timeout=_SATELLITE_LIST_TIMEOUT) as client:
        for group in _SATELLITE_LIST_GROUPS:
            try:
                r = client.get(
                    _CELESTRAK_GP,
                    params={"GROUP": group, "FORMAT": "json"},
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                _log.debug("CelesTrak fetch %s failed: %s", group, e)
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
    return result


def _get_satellite_list_path() -> Path:
    """Path to satellite_list.json (same directory as main config)."""
    from glancerf.config import get_config
    return get_config().config_dir / _SATELLITE_LIST_FILENAME


def _load_satellite_list_from_file() -> list[dict[str, Any]] | None:
    """Load satellite list from JSON file. Returns list of {norad_id, name} or None if missing/invalid."""
    path = _get_satellite_list_path()
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        _log.debug("satellite_list.json load failed: %s", e)
        return None
    satellites = data.get("satellites") if isinstance(data, dict) else None
    if not isinstance(satellites, list):
        return None
    out: list[dict[str, Any]] = []
    for s in satellites:
        if isinstance(s, dict) and isinstance(s.get("norad_id"), (int, float)) and s.get("name"):
            out.append({"norad_id": int(s["norad_id"]), "name": str(s["name"]).strip()})
    return out if out else None


def _save_satellite_list_to_file(satellites: list[dict[str, Any]]) -> None:
    """Save satellite list to JSON file with updated_utc."""
    path = _get_satellite_list_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "satellites": satellites,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    _log.debug("Saved satellite list to %s (%d entries)", path, len(satellites))


def _prune_config_selected_satellites(valid_norad_ids: set[int]) -> None:
    """
    Remove from main config any selected_satellites (for satellite_pass cells) that reference
    NORAD IDs no longer in valid_norad_ids. Saves config if changed.
    """
    from glancerf.config import get_config
    config = get_config()
    layout = config.get("layout") or []
    if not isinstance(layout, list):
        return
    module_settings = dict(config.get("module_settings") or {})
    changed = False
    for row_idx, row in enumerate(layout):
        if not isinstance(row, list):
            continue
        for col_idx, cell_value in enumerate(row):
            if cell_value != _MODULE_ID_SATELLITE_PASS:
                continue
            cell_key = f"{row_idx}_{col_idx}"
            cell_settings = module_settings.get(cell_key) or {}
            raw = cell_settings.get(_SETTING_SELECTED_SATELLITES, "[]")
            try:
                selected = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(selected, list):
                    selected = []
                selected = [int(x) for x in selected if isinstance(x, (int, float))]
            except (TypeError, ValueError):
                selected = []
            pruned = [x for x in selected if x in valid_norad_ids]
            if pruned != selected:
                module_settings[cell_key] = {
                    **(module_settings.get(cell_key) or {}),
                    _SETTING_SELECTED_SATELLITES: json.dumps(pruned),
                }
                changed = True
    if changed:
        config.set("module_settings", module_settings)
        _log.debug("Pruned selected_satellites in config for removed satellites")


def get_satellite_list_cached() -> list[dict[str, Any]]:
    """
    Return the trackable satellite list. Uses satellite_list.json in the config directory.
    On first run or if the file is missing or older than ~24 hours, fetches from CelesTrak,
    saves to JSON, prunes config (removes selected NORAD IDs no longer in the list), then returns.
    Otherwise loads from the JSON file.
    """
    path = _get_satellite_list_path()
    now = datetime.now(timezone.utc).timestamp()
    need_refresh = True
    if path.is_file():
        try:
            mtime = os.path.getmtime(path)
            if (now - mtime) < _LIST_MAX_AGE_SECONDS:
                loaded = _load_satellite_list_from_file()
                if loaded:
                    return loaded
        except OSError:
            pass
    list_from_api = fetch_satellite_list()
    if not list_from_api:
        fallback = _load_satellite_list_from_file()
        return fallback or []
    _save_satellite_list_to_file(list_from_api)
    valid_ids = {s["norad_id"] for s in list_from_api}
    _prune_config_selected_satellites(valid_ids)
    return list_from_api


def fetch_tle(norad_id: int) -> tuple[str, str] | None:
    """Fetch TLE for one satellite from CelesTrak. Returns (line1, line2) or None."""
    try:
        with httpx.Client(timeout=_TLE_TIMEOUT) as client:
            r = client.get(
                _CELESTRAK_GP,
                params={"CATNR": norad_id, "FORMAT": "tle"},
            )
            r.raise_for_status()
            text = r.text.strip()
    except Exception as e:
        _log.debug("TLE fetch for NORAD %s failed: %s", norad_id, e)
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 2 and lines[0].startswith("1 ") and lines[1].startswith("2 "):
        return lines[0], lines[1]
    if len(lines) >= 3 and lines[1].startswith("1 ") and lines[2].startswith("2 "):
        return lines[1], lines[2]
    return None


def compute_pass(
    norad_id: int,
    name: str,
    lat_deg: float,
    lon_deg: float,
    alt_m: float = 0.0,
) -> dict[str, Any] | None:
    """
    Compute current position and next pass for one satellite.
    Returns dict with name, norad_id, current {az, el, up}, next_pass {rise_utc, set_utc, rise_az, set_az, max_el, duration_sec}, or None on error.
    """
    tle = fetch_tle(norad_id)
    if not tle:
        return None
    ts, eph = _get_timescale_and_ephemeris()
    try:
        sat = EarthSatellite(tle[0], tle[1], name, ts)
    except Exception as e:
        _log.debug("Skyfield EarthSatellite for %s failed: %s", norad_id, e)
        return None
    earth = eph["earth"]
    topos = wgs84.latlon(lat_deg, lon_deg, elevation_m=alt_m)
    observer = earth + topos
    t_now = ts.now()

    # Current position
    try:
        astro = observer.at(t_now).observe(sat)
        alt, az, _ = astro.apparent().altaz()
        el_deg = alt.degrees
        az_deg = az.degrees
    except Exception:
        el_deg = -90
        az_deg = 0
    up = el_deg >= _MIN_ELEVATION_DEG

    # Next pass (rise/set in next _PASS_SEARCH_DAYS). find_events expects
    # a raw topos (same center as satellite), not earth+topos.
    utc_now = t_now.utc_datetime()
    t1 = ts.from_datetime(utc_now + timedelta(days=_PASS_SEARCH_DAYS))
    try:
        event_times, events = sat.find_events(
            topos, t_now, t1, altitude_degrees=_MIN_ELEVATION_DEG
        )
    except Exception as e:
        _log.debug("find_events for %s failed: %s", norad_id, e)
        event_times = []
        events = []

    # events: 0=rise, 1=culminate, 2=set. We want first rise and next set after it.
    rise_utc = None
    set_utc = None
    rise_az = None
    set_az = None
    max_el = None
    duration_sec = 0
    n_ev = len(event_times)
    i = 0
    while i < n_ev:
        if events[i] == 0:  # rise
            t_rise = event_times[i]
            try:
                astro = observer.at(t_rise).observe(sat)
                alt, az, _ = astro.apparent().altaz()
                rise_az = round(az.degrees, 1)
            except Exception:
                pass
            max_el_val = -90
            j = i + 1
            while j < n_ev:
                if events[j] == 1:
                    try:
                        astro = observer.at(event_times[j]).observe(sat)
                        alt, _, _ = astro.apparent().altaz()
                        max_el_val = max(max_el_val, alt.degrees)
                    except Exception:
                        pass
                if events[j] == 2:  # set
                    t_set = event_times[j]
                    try:
                        astro = observer.at(t_set).observe(sat)
                        alt, az, _ = astro.apparent().altaz()
                        set_az = round(az.degrees, 1)
                    except Exception:
                        pass
                    if max_el_val <= -90:
                        try:
                            t_mid = event_times[(i + j) // 2]
                            astro = observer.at(t_mid).observe(sat)
                            alt, _, _ = astro.apparent().altaz()
                            max_el_val = alt.degrees
                        except Exception:
                            pass
                    rise_utc = t_rise.utc_datetime().isoformat() + "Z"
                    set_utc = t_set.utc_datetime().isoformat() + "Z"
                    max_el = round(max_el_val, 1) if max_el_val > -90 else None
                    duration_sec = int(
                        (t_set.utc_datetime() - t_rise.utc_datetime()).total_seconds()
                    )
                    break
                j += 1
            if rise_utc is not None:
                break
        i += 1

    next_pass = None
    if rise_utc and set_utc:
        next_pass = {
            "rise_utc": rise_utc,
            "set_utc": set_utc,
            "rise_az": rise_az,
            "set_az": set_az,
            "max_el": max_el,
            "duration_sec": duration_sec,
        }

    return {
        "norad_id": norad_id,
        "name": name,
        "current": {
            "az": round(az_deg, 1),
            "el": round(el_deg, 1),
            "up": up,
        },
        "next_pass": next_pass,
    }


def compute_passes(
    norad_ids: list[int],
    lat_deg: float,
    lon_deg: float,
    alt_m: float = 0.0,
    name_by_norad: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Compute pass info for multiple satellites. name_by_norad can be used to pass names
    without refetching the list; otherwise names come from the first result.
    """
    name_by_norad = name_by_norad or {}
    results = []
    for nid in norad_ids:
        name = name_by_norad.get(nid) or str(nid)
        one = compute_pass(nid, name, lat_deg, lon_deg, alt_m)
        if one is not None:
            results.append(one)
    return results
