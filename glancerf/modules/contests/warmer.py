"""Cache warmer for contests module. Called by core when headless and module is active."""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from glancerf.utils.cache import get_cache


async def warm(settings: dict, config: Any) -> None:
    """Fetch contests and fill cache. No-op if not configured; same cache key as API."""
    enabled_raw = settings.get("enabled_sources")
    enabled = [s.strip() for s in (enabled_raw or "").split(",") if s.strip()] if enabled_raw else None
    custom_raw = settings.get("custom_sources")
    custom = None
    if custom_raw:
        try:
            if isinstance(custom_raw, str):
                custom = json.loads(custom_raw)
            elif isinstance(custom_raw, list):
                custom = custom_raw
            if not isinstance(custom, list):
                custom = None
        except (json.JSONDecodeError, TypeError):
            custom = None
    try:
        from glancerf.modules.contests.contest_service import get_contests_cached
        from glancerf.modules.contests.api_routes import _CACHE_TTL_SEC

        result = await asyncio.to_thread(
            get_contests_cached, enabled_sources=enabled, custom_sources=custom
        )
        cache_key = "contests:list:" + (",".join(sorted(enabled or [])) or "all")
        if custom:
            cache_key += ":" + hashlib.sha256(json.dumps(custom, sort_keys=True).encode()).hexdigest()[:16]
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
        credits = "; ".join(enabled) if enabled else "WA7BNM; SSA (SE); RSGB (UK)"
        if custom:
            custom_labels = [
                (c.get("label") or c.get("name") or "").strip() or "Custom"
                for c in custom
                if isinstance(c, dict) and (c.get("url") or c.get("URL"))
            ]
            if custom_labels:
                credits = (credits + "; " + "; ".join(custom_labels)) if credits else "; ".join(custom_labels)
        get_cache().set(cache_key, {"contests": result, "credits": credits}, _CACHE_TTL_SEC)
    except Exception:
        pass
