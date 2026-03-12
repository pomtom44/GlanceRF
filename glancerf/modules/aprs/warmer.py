"""Cache warmer for APRS module. Warms map:aprs cache so list loads fast when headless."""

import asyncio
from typing import Any

from glancerf.utils.cache import get_cache


async def warm(settings: dict, config: Any) -> None:
    """Warm APRS locations cache. Same cache key as /api/map/aprs-locations."""
    hours = 6
    try:
        h = float(settings.get("hours") or 6)
        if 0.25 <= h <= 168:
            hours = h
    except (TypeError, ValueError):
        pass
    filter_str = (settings.get("aprs_filter") or "").strip() or None
    try:
        from glancerf.modules.map.aprs_client import get_aprs_locations_from_cache
        from glancerf.modules.map.api_routes import _APRS_CACHE_TTL

        result = await asyncio.to_thread(get_aprs_locations_from_cache, hours=hours, filter_str=filter_str)
        cache_key = f"map:aprs:{hours}|{filter_str or ''}"
        get_cache().set(cache_key, result, _APRS_CACHE_TTL)
    except Exception:
        pass
