"""
Fetch ionospheric and tropospheric data for map overlay. Used to draw propagation
overlay from raw data (like aurora) instead of overlaying external images.

HF data source: KC2G (prop.kc2g.com) GIRO station data, same as referenced in
"Real-time propagation charts" at https://www.qsl.net/4x4xm/HF-Propagation.htm#RegMaps
- MUF 3000 km: ionosonde-derived MUF for 3000 km path (mufd)
- foF2 (NVIS): critical frequency for near-vertical incidence skywave
"""

import math
from typing import Any

import httpx

from glancerf.logging_config import get_logger

_log = get_logger("map.propagation_service")

_KC2G_STATIONS_JSON_URL = "https://prop.kc2g.com/api/stations.json"
_OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
_FETCH_TIMEOUT = 25
_TROPO_GRID_LAT = [-60, -30, 0, 30, 60]
_TROPO_GRID_LON = [-180, -135, -90, -45, 0, 45, 90, 135]


def _normalize_lon(lon: float) -> float:
    """Convert longitude to -180..180 if given in 0..360."""
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360
    return lon


def fetch_kc2g_stations() -> list[dict[str, Any]]:
    """Fetch KC2G stations JSON API and return list of station dicts with longitude, latitude, mufd, fof2."""
    try:
        with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(_KC2G_STATIONS_JSON_URL)
            resp.raise_for_status()
            raw = resp.json()
    except Exception as e:
        _log.debug("KC2G stations fetch failed: %s", e)
        return []
    if not isinstance(raw, list):
        _log.debug("KC2G stations response is not a list")
        return []
    stations: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        st = item.get("station")
        if not isinstance(st, dict):
            continue
        try:
            lat = float(st.get("latitude", 0))
            lon = float(st.get("longitude", 0))
        except (TypeError, ValueError):
            continue
        lon = _normalize_lon(lon)
        if lon < -180 or lon > 180 or lat < -90 or lat > 90:
            continue
        mufd: float | None = None
        fof2: float | None = None
        if item.get("mufd") is not None:
            try:
                mufd = float(item["mufd"])
            except (TypeError, ValueError):
                pass
        if item.get("fof2") is not None:
            try:
                fof2 = float(item["fof2"])
            except (TypeError, ValueError):
                pass
        stations.append({"longitude": lon, "latitude": lat, "mufd": mufd, "fof2": fof2})
    _log.debug("KC2G stations parsed: %d", len(stations))
    return stations


def _refractivity(t_c: float, rh_pct: float, p_hpa: float) -> float:
    """Surface refractivity N from temperature (C), relative humidity (%), pressure (hPa). ITU-R P.453."""
    if not (abs(t_c) < 100 and 0 <= rh_pct <= 100 and 500 < p_hpa < 1100):
        return 280.0
    t_k = t_c + 273.15
    es = 6.112 * math.exp(17.62 * t_c / (243.12 + t_c))
    e = (rh_pct / 100.0) * es
    n_dry = 77.6 * (p_hpa / t_k)
    n_wet = 4810.0 * (e / (t_k * t_k))
    return n_dry + n_wet


def fetch_tropo_grid() -> list[tuple[float, float, float]]:
    """Fetch weather for a coarse global grid and return list of (lon, lat, refractivity N)."""
    coords: list[tuple[float, float, float]] = []
    params = {
        "current": "temperature_2m,relative_humidity_2m,surface_pressure",
        "timezone": "UTC",
    }
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        for lat in _TROPO_GRID_LAT:
            for lon in _TROPO_GRID_LON:
                try:
                    resp = client.get(
                        _OPENMETEO_URL,
                        params={**params, "latitude": lat, "longitude": lon},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    cur = data.get("current") or {}
                    t = cur.get("temperature_2m")
                    rh = cur.get("relative_humidity_2m")
                    p = cur.get("surface_pressure")
                    if t is None or rh is None or p is None:
                        continue
                    n = _refractivity(float(t), float(rh), float(p))
                    coords.append((lon, lat, n))
                except Exception as e:
                    _log.debug("Open-Meteo point %s,%s failed: %s", lat, lon, e)
    _log.debug("Tropo grid points: %d", len(coords))
    return coords


def get_tropo_coordinates() -> dict[str, Any]:
    """
    Return tropo propagation data for overlay from weather-derived refractivity.
    Returns { "coordinates": [[lon, lat, N], ...], "valueLabel": "Tropo" }.
    """
    grid = fetch_tropo_grid()
    coords = [[lon, lat, n] for lon, lat, n in grid]
    return {"coordinates": coords, "valueLabel": "Tropo"}


def get_aprs_coordinates_from_cache(hours: float | None = None) -> dict[str, Any]:
    """
    Return VHF propagation overlay from local APRS cache DB (config_dir/cache/aprs.db).
    hours: optional override (1, 6, 12, 24); if None, uses config aprs_propagation_hours or default 6.
    """
    from .aprs_client import get_aprs_propagation_data_from_cache
    return get_aprs_propagation_data_from_cache(hours=hours)


def get_propagation_coordinates(source: str, hours: float | None = None) -> dict[str, Any]:
    """
    Return propagation data for overlay. source is 'kc2g_muf', 'kc2g_fof2', 'tropo', or 'vhf_aprs'.
    hours: optional, for vhf_aprs only (1, 6, 12, or 24). Returns { "coordinates": [...], "valueLabel": "..." }.
    """
    if source == "tropo":
        return get_tropo_coordinates()
    if source == "vhf_aprs":
        return get_aprs_coordinates_from_cache(hours=hours)
    stations = fetch_kc2g_stations()
    if source == "kc2g_muf":
        value_label = "MUF"
        coords = [
            [s["longitude"], s["latitude"], s["mufd"]]
            for s in stations
            if s.get("mufd") is not None
        ]
    elif source == "kc2g_fof2":
        value_label = "foF2"
        coords = [
            [s["longitude"], s["latitude"], s["fof2"]]
            for s in stations
            if s.get("fof2") is not None
        ]
    else:
        return {"coordinates": [], "valueLabel": ""}
    return {"coordinates": coords, "valueLabel": value_label}
