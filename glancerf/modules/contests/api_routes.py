"""
Register contests API routes. Called by core at startup if this module is present.
"""

import hashlib
import json
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from glancerf.utils.cache import get_cache
from .contest_service import get_contests_cached

_log = get_logger("contests.api_routes")

_DEFAULT_CREDITS = "WA7BNM; SSA (SE); RSGB (UK)"
_CACHE_TTL_SEC = 900


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
        cache_key = "contests:list:" + (",".join(sorted(enabled or [])) or "all")
        if custom:
            cache_key += ":" + hashlib.sha256(json.dumps(custom, sort_keys=True).encode()).hexdigest()[:16]
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = await asyncio.to_thread(
                get_contests_cached, enabled_sources=enabled, custom_sources=custom
            )
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            contest_active = any(
                (c.get("start_utc") or "") <= now <= (c.get("end_utc") or "")
                for c in (result or []) if isinstance(c, dict)
            )
            try:
                from glancerf.gpio import set_output
                set_output("contests", "contest_active", bool(contest_active))
            except Exception:
                pass
            out = {"contests": result, "credits": credits}
            cache.set(cache_key, out, _CACHE_TTL_SEC)
            return out
        except Exception as e:
            _log.debug("Contests list failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch contests", "detail": str(e)},
                status_code=502,
            )
