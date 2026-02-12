"""Cache warmer for RSS module. Called by core when headless and module is active."""

import hashlib
from typing import Any

from glancerf.utils.cache import get_cache


async def warm(settings: dict, config: Any) -> None:
    """Fetch RSS feed and fill cache. No-op if rss_url empty. Same cache key as API."""
    url = (settings.get("rss_url") or "").strip()
    if not url:
        return
    try:
        from glancerf.modules.rss.api_routes import fetch_rss_feed, _RSS_CACHE_TTL

        out = await fetch_rss_feed(url)
        if out is not None:
            cache_key = "rss:" + hashlib.sha256(url.encode()).hexdigest()
            get_cache().set(cache_key, out, _RSS_CACHE_TTL)
    except Exception:
        pass
