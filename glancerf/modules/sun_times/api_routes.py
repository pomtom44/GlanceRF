"""
Sun times status for GPIO. Optional API: returns sun up/down and updates sun_up LED.
Uses Skyfield (same as satellite_pass) for sun elevation at a location.
"""

import asyncio
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.config import get_logger

_log = get_logger("sun_times.api_routes")

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
_DE421_PATH = _PROJECT_DIR / "cache" / "de421.bsp"


def _sun_up_at_location(lat: float, lng: float) -> bool:
    """Return True if sun is above horizon at the given location (degrees). Uses Skyfield."""
    try:
        from skyfield.api import load, wgs84
        ts = load.timescale()
        eph = load(str(_DE421_PATH))
        sun = eph["sun"]
        earth = eph["earth"]
        t = ts.now()
        loc = wgs84.latlon(lat, lng)
        astro = loc.at(t).observe(sun).apparent()
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
        try:
            sun_up = await asyncio.to_thread(_sun_up_at_location, lat, lng)
            try:
                from glancerf.gpio import set_output
                set_output("sun_times", "sun_up", sun_up)
            except Exception:
                pass
            return {"sun_up": sun_up}
        except Exception as e:
            _log.debug("sun_times status failed: %s", e)
            return JSONResponse(
                {"error": "Failed to compute sun position", "detail": str(e)},
                status_code=502,
            )
