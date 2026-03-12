"""
Sun times status for GPIO. Optional API: returns sun up/down and updates sun_up LED.
Uses Skyfield for sun elevation at a location.
"""

import asyncio
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from glancerf.utils.cache import get_cache

_log = get_logger("sun_times.api_routes")

_SUN_STATUS_CACHE_TTL = 60

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
_DE421_PATH = _PROJECT_DIR / "cache" / "de421.bsp"


def _sun_up_at_location(lat: float, lng: float) -> bool:
    """Return True if sun is above horizon at the given location (degrees). Uses Skyfield."""
    try:
        from skyfield.api import load, wgs84
        ts = load.timescale()
        path = str(_DE421_PATH) if _DE421_PATH.is_file() else "de421.bsp"
        eph = load(path)
        sun = eph["sun"]
        earth = eph["earth"]
        t = ts.now()
        topos = wgs84.latlon(lat, lng)
        observer = earth + topos
        astro = observer.at(t).observe(sun).apparent()
        alt, _, _ = astro.altaz()
        return float(alt.degrees) > 0
    except Exception as e:
        _log.debug("sun_times sun_up failed: %s", e)
        return False


def register_routes(app: FastAPI) -> None:
    """Register GET /api/sun_times/status. Updates sun_up GPIO output when called."""

    @app.get("/api/sun_times/status")
    async def sun_times_status(
        lat: float = Query(..., ge=-90, le=90),
        lng: float = Query(..., ge=-180, le=180),
    ):
        """Return whether sun is above horizon at the given location. Also updates the sun_up GPIO output."""
        cache_key = f"sun_times:status:{lat}|{lng}"
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            try:
                from glancerf.gpio import set_output
                set_output("sun_times", "sun_up", cached.get("sun_up", False))
            except Exception:
                pass
            return cached
        try:
            sun_up = await asyncio.to_thread(_sun_up_at_location, lat, lng)
            try:
                from glancerf.gpio import set_output
                set_output("sun_times", "sun_up", sun_up)
            except Exception:
                pass
            out = {"sun_up": sun_up}
            cache.set(cache_key, out, _SUN_STATUS_CACHE_TTL)
            return out
        except Exception as e:
            _log.debug("sun_times status failed: %s", e)
            return JSONResponse(
                {"error": "Failed to compute sun position", "detail": str(e)},
                status_code=502,
            )
