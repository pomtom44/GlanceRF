"""
Register satellite_pass API routes. List (names) and locations (sub-satellite positions from cache).
"""

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.config import get_config, get_logger
from glancerf.utils import get_effective_location
from .satellite_service import (
    get_satellite_list_cached,
    get_satellite_locations_cached,
    get_satellite_tracks_cached,
    get_next_pass_from_cache,
    parse_location_to_lat_lon,
)

_log = get_logger("satellite_pass.api_routes")


def register_routes(app: FastAPI) -> None:
    """Register /api/satellite/list, /api/satellite/locations, and /api/satellite/tracks."""

    @app.get("/api/satellite/list")
    async def get_satellite_list():
        """Return list of ham/amateur satellites from cache, or from CelesTrak if cache expired/missing."""
        try:
            result = await asyncio.to_thread(get_satellite_list_cached)
            return {"satellites": result}
        except Exception as e:
            _log.debug("api satellite/list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch satellite list", "detail": str(e)},
                status_code=502,
            )

    @app.get("/api/satellite/locations")
    async def get_satellite_locations():
        """Return sub-satellite positions, velocities (deg/s), and per-NORAD position_updated_utc from cache for client-side estimation."""
        _log.debug("api satellite/locations: request")
        try:
            positions, velocities, updated_utc, position_updated_utc = await asyncio.to_thread(get_satellite_locations_cached)
            out = {
                "positions": {str(norad): [lat, lon] for norad, (lat, lon) in positions.items()},
                "velocities": {str(norad): [vlat, vlon] for norad, (vlat, vlon) in velocities.items()},
                "updated_utc": updated_utc or "",
                "position_updated_utc": {str(norad): ts for norad, ts in position_updated_utc.items()},
            }
            _log.debug("api satellite/locations: returned %d positions", len(positions))
            return out
        except Exception as e:
            _log.debug("api satellite/locations failed: %s", e)
            return JSONResponse(
                {"error": "Failed to get satellite locations", "detail": str(e)},
                status_code=502,
            )

    @app.get("/api/satellite/tracks")
    async def get_satellite_tracks():
        """Return ground tracks (tail 30 min, lead 90 min) per NORAD from cache. Refreshed every 10 min."""
        try:
            tracks, updated_utc = await asyncio.to_thread(get_satellite_tracks_cached)
            out = {
                "tracks": {
                    str(norad): {"tail": [[p[0], p[1]] for p in tail], "lead": [[p[0], p[1]] for p in lead]}
                    for norad, (tail, lead) in tracks.items()
                },
                "updated_utc": updated_utc or "",
            }
            return out
        except Exception as e:
            _log.debug("api satellite/tracks failed: %s", e)
            return JSONResponse(
                {"error": "Failed to get satellite tracks", "detail": str(e)},
                status_code=502,
            )

    @app.get("/api/satellite/next_pass")
    async def get_next_pass(lat: float | None = None, lon: float | None = None, location: str | None = None):
        """Return next pass times from cache for a location. Use query lat/lon, or location (gridsquare or lat,lon), or effective location (GPS or config)."""
        try:
            obs_lat, obs_lon = None, None
            if lat is not None and lon is not None:
                obs_lat, obs_lon = float(lat), float(lon)
            elif location and location.strip():
                ll = parse_location_to_lat_lon(location.strip())
                if ll is not None:
                    obs_lat, obs_lon = ll
            if obs_lat is None or obs_lon is None:
                config = get_config()
                ll = get_effective_location(config)
                if ll is not None:
                    obs_lat, obs_lon = ll
            if obs_lat is None or obs_lon is None:
                return {
                    "text": "No location set. Use Setup default location (grid square or lat,lon), or pass ?lat=&lon= or ?location= to this API.",
                    "tracks_updated_utc": "",
                    "next_pass": None,
                    "passes": [],
                }
            result = await asyncio.to_thread(get_next_pass_from_cache, obs_lat, obs_lon)
            return result
        except Exception as e:
            _log.debug("api satellite/next_pass failed: %s", e)
            return JSONResponse(
                {"error": "Failed to get next pass", "detail": str(e), "text": "", "next_pass": None, "passes": []},
                status_code=502,
            )
