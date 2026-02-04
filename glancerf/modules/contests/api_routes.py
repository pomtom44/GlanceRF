"""
Register contests API routes. Called by core at startup if this module is present.
"""

import json
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.logging_config import get_logger
from .contest_service import get_contests_cached

_log = get_logger("contests.api_routes")

_DEFAULT_CREDITS = "WA7BNM; SSA (SE); RSGB (UK)"


def register_routes(app: FastAPI) -> None:
    """Register GET /api/contests/list."""

    @app.get("/api/contests/list")
    async def get_contests_list(sources: str | None = None, custom_sources: str | None = None):
        """Return list of contests. sources: comma-separated built-in source IDs. custom_sources: JSON array of {url, type, label}."""
        _log.debug("API: GET /api/contests/list")
        if sources is None:
            enabled = None
        else:
            enabled = [s.strip() for s in sources.split(",") if s.strip()]
        credits = "; ".join(enabled) if enabled else _DEFAULT_CREDITS
        custom = None
        if custom_sources and custom_sources.strip():
            try:
                custom = json.loads(custom_sources)
                if not isinstance(custom, list):
                    custom = None
            except (json.JSONDecodeError, TypeError):
                custom = None
        if custom:
            custom_labels = []
            for c in custom:
                if isinstance(c, dict) and (c.get("url") or c.get("URL")):
                    custom_labels.append((c.get("label") or c.get("name") or "").strip() or "Custom")
            if custom_labels:
                credits = credits + "; " + "; ".join(custom_labels) if credits else "; ".join(custom_labels)
        try:
            result = await asyncio.to_thread(
                get_contests_cached, enabled_sources=enabled, custom_sources=custom
            )
            return {
                "contests": result,
                "credits": credits,
            }
        except Exception as e:
            _log.debug("Contests list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch contests", "detail": str(e)},
                status_code=502,
            )
