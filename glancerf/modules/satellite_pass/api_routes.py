"""
Register satellite_pass API routes. Called by core at startup if this module is present.
"""

import asyncio

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.logging_config import get_logger
from .satellite_service import get_satellite_list_cached, compute_passes

_log = get_logger("satellite_pass.api_routes")


def register_routes(app: FastAPI) -> None:
    """Register /api/satellite/list and /api/satellite/passes."""

    @app.get("/api/satellite/list")
    async def get_satellite_list():
        """Return list of trackable satellites from satellite_list.json (refreshed from CelesTrak if missing or older than ~24h)."""
        _log.debug("API: GET /api/satellite/list")
        try:
            result = await asyncio.to_thread(get_satellite_list_cached)
            return {"satellites": result}
        except Exception as e:
            _log.debug("Satellite list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch satellite list", "detail": str(e)},
                status_code=502,
            )

    @app.get("/api/satellite/passes")
    async def get_satellite_passes(
        norad_ids: str = Query(..., description="Comma-separated NORAD IDs"),
        lat: float = Query(..., ge=-90, le=90),
        lng: float = Query(..., ge=-180, le=180),
        alt: float = Query(0, ge=0, le=10000),
    ):
        """Return current position and next pass for each requested satellite."""
        _log.debug("API: GET /api/satellite/passes norad_ids=%s", norad_ids[:80])
        try:
            ids = [int(x.strip()) for x in norad_ids.split(",") if x.strip()]
        except ValueError:
            return JSONResponse(
                {"error": "norad_ids must be comma-separated integers"},
                status_code=400,
            )
        if not ids:
            return JSONResponse(
                {"error": "At least one NORAD ID required"},
                status_code=400,
            )
        if len(ids) > 20:
            return JSONResponse(
                {"error": "At most 20 NORAD IDs per request"},
                status_code=400,
            )
        try:
            sat_list = await asyncio.to_thread(get_satellite_list_cached)
            name_by_norad = {s["norad_id"]: s["name"] for s in (sat_list or []) if s.get("name")}
            result = await asyncio.to_thread(compute_passes, ids, lat, lng, alt, name_by_norad)
            return {"passes": result}
        except Exception as e:
            _log.debug("Satellite passes failed: %s", e)
            return JSONResponse(
                {"error": "Failed to compute passes", "detail": str(e)},
                status_code=502,
            )
