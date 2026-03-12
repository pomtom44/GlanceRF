"""
Register live_spots API routes. Triggers data fetch from sources and logs at debug level.
Probe endpoint returns raw and parsed data from each service to inspect what is available.
"""

import asyncio

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from .spots_service import fetch_all_sources, get_pskreporter_cached, probe_all_sources

_log = get_logger("live_spots.api_routes")


def register_routes(app: FastAPI) -> None:
    """Register GET /api/live_spots/test, /api/live_spots/probe, /api/live_spots/spots."""

    @app.get("/api/live_spots/test")
    async def test_pull():
        """Pull data from RBN, PSK Reporter, and DXWatch; log at debug level. Returns summary."""
        _log.debug("API: GET /api/live_spots/test")
        try:
            result = await asyncio.to_thread(fetch_all_sources)
            return {
                "ok": True,
                "sources": {
                    "rbn": [{"ok": r.get("ok"), "status": r.get("status"), "length": r.get("length")} for r in result["rbn"]],
                    "pskreporter": {"ok": result["pskreporter"].get("ok"), "status": result["pskreporter"].get("status"), "length": result["pskreporter"].get("length")},
                    "dxwatch": {"ok": result["dxwatch"].get("ok"), "status": result["dxwatch"].get("status"), "length": result["dxwatch"].get("length")},
                },
            }
        except Exception as e:
            _log.debug("live_spots test_pull failed: %s", e)
            return JSONResponse(
                {"ok": False, "error": str(e)},
                status_code=502,
            )

    @app.get("/api/live_spots/probe")
    async def probe_sources(
        psk_flow_seconds: int = Query(-3600, description="PSK Reporter: last N seconds (negative)"),
        psk_limit: int = Query(50, ge=1, le=500, description="PSK Reporter: max records"),
        psk_sender: str | None = Query(None, description="PSK Reporter: senderCallsign filter"),
        psk_receiver: str | None = Query(None, description="PSK Reporter: receiverCallsign filter"),
    ):
        """
        Probe RBN, PSK Reporter, and DXWatch; return status, raw preview, and parsed data
        so you can see what each service returns. Use for development and data discovery.
        """
        _log.debug("API: GET /api/live_spots/probe")
        try:
            result = await asyncio.to_thread(
                probe_all_sources,
                psk_flow_seconds=psk_flow_seconds,
                psk_limit=psk_limit,
                psk_sender=psk_sender or None,
                psk_receiver=psk_receiver or None,
            )
            return {"ok": True, "sources": result}
        except Exception as e:
            _log.debug("live_spots probe failed: %s", e)
            return JSONResponse(
                {"ok": False, "error": str(e)},
                status_code=502,
            )

    @app.get("/api/live_spots/spots")
    async def get_spots(
        filter_mode: str = Query("received", description="Received by or Sent by"),
        callsign_or_grid: str | None = Query("", description="Callsign or grid square"),
        age_mins: int = Query(60, ge=1, le=1440, description="Max age in minutes (table)"),
    ):
        """Return PSK Reporter spots from cache (or fetch and cache). Uses filter_mode and callsign_or_grid from config."""
        _log.debug("API: GET /api/live_spots/spots filter_mode=%s callsign_or_grid=%s", filter_mode, callsign_or_grid)
        value = (callsign_or_grid or "").strip()
        if not value:
            return {"ok": True, "spots": []}
        flow_seconds = -max(1, age_mins) * 60
        try:
            spots = await asyncio.to_thread(
                get_pskreporter_cached,
                filter_mode=filter_mode or "received",
                callsign_or_grid=value,
                flow_seconds=flow_seconds,
                rpt_limit=200,
            )
            return {"ok": True, "spots": spots or []}
        except Exception as e:
            _log.debug("live_spots spots failed: %s", e)
            return JSONResponse(
                {"ok": False, "error": str(e), "spots": []},
                status_code=502,
            )
