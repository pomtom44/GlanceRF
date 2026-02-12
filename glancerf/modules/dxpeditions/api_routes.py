"""
Register dxpeditions API routes. Called by core at startup if this module is present.
"""

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from glancerf.utils.cache import get_cache
from .dxpedition_service import get_dxpeditions_cached

_log = get_logger("dxpeditions.api_routes")

_DEFAULT_CREDITS = "NG3K ADXO; NG3K RSS; DXCAL (danplanet.com)"
_CACHE_TTL_SEC = 900


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
        cache_key = "dxpeditions:list:" + (",".join(sorted(enabled or [])) or "all")
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = await asyncio.to_thread(get_dxpeditions_cached, enabled_sources=enabled)
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            active = any(
                (d.get("start_utc") or "") <= now <= (d.get("end_utc") or "")
                for d in (result or []) if isinstance(d, dict)
            )
            try:
                from glancerf.gpio import set_output
                set_output("dxpeditions", "alert", bool(active))
            except Exception:
                pass
            out = {"dxpeditions": result, "credits": credits}
            cache.set(cache_key, out, _CACHE_TTL_SEC)
            return out
        except Exception as e:
            _log.debug("DXpeditions list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch DXpeditions", "detail": str(e)},
                status_code=502,
            )
