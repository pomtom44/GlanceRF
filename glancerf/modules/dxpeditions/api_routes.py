"""
Register dxpeditions API routes. Called by core at startup if this module is present.
"""

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.logging_config import get_logger
from .dxpedition_service import get_dxpeditions_cached

_log = get_logger("dxpeditions.api_routes")

_DEFAULT_CREDITS = "NG3K ADXO; NG3K RSS; DXCAL (danplanet.com)"


def register_routes(app: FastAPI) -> None:
    """Register GET /api/dxpeditions/list."""

    @app.get("/api/dxpeditions/list")
    async def get_dxpeditions_list(sources: str | None = None):
        """Return list of DXpeditions. Optional query param sources: comma-separated source IDs to enable."""
        _log.debug("API: GET /api/dxpeditions/list")
        if sources is None:
            enabled = None
        else:
            enabled = [s.strip() for s in sources.split(",") if s.strip()]
        credits = "; ".join(enabled) if enabled else _DEFAULT_CREDITS
        try:
            result = await asyncio.to_thread(get_dxpeditions_cached, enabled_sources=enabled)
            return {
                "dxpeditions": result,
                "credits": credits,
            }
        except Exception as e:
            _log.debug("DXpeditions list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch DXpeditions", "detail": str(e)},
                status_code=502,
            )
