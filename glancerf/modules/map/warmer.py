"""Cache warmer for map module. Called by core when headless and module is active."""

import asyncio
from typing import Any

from glancerf.utils.cache import get_cache


async def warm(settings: dict, config: Any) -> None:
    """Warm propagation and APRS caches. Same cache keys as API."""
    source = (settings.get("propagation_source") or "").strip() or None
    hours_raw = settings.get("propagation_aprs_hours")
    hours = None
    if hours_raw is not None and hours_raw != "":
        try:
            hours = float(hours_raw)
        except (TypeError, ValueError):
            pass
    if source and source in ("kc2g_muf", "kc2g_fof2", "tropo", "vhf_aprs"):
        try:
            from glancerf.modules.map.propagation_service import get_propagation_coordinates
            from glancerf.modules.map.api_routes import _PROPAGATION_CACHE_TTL

            result = await asyncio.to_thread(get_propagation_coordinates, source, hours=hours)
            cache_key = f"map:propagation:{source}|{hours}"
            get_cache().set(cache_key, result, _PROPAGATION_CACHE_TTL)
        except Exception:
            pass
    try:
        from glancerf.modules.map.aprs_client import get_aprs_locations_from_cache
        from glancerf.modules.map.api_routes import _APRS_CACHE_TTL

        filter_str = (settings.get("aprs_filter") or "").strip() or None
        result = await asyncio.to_thread(get_aprs_locations_from_cache, hours=hours, filter_str=filter_str)
        cache_key = f"map:aprs:{hours}|{filter_str or ''}"
        get_cache().set(cache_key, result, _APRS_CACHE_TTL)
    except Exception:
        pass
