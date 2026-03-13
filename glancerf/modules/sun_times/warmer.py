"""Cache warmer for sun_times module. Called by core when headless and module is active."""

import asyncio
from typing import Any

from glancerf.utils.cache import get_cache
from glancerf.utils.location import get_effective_location, parse_location


async def warm(settings: dict, config: Any) -> None:
    """Compute sun up/down and fill cache. No-op if location not set or invalid."""
    loc_str = (settings.get("location") or "").strip()
    coords = parse_location(loc_str) if loc_str else get_effective_location(config)
    if coords is None:
        return
    lat, lng = coords
    try:
        from glancerf.modules.sun_times.api_routes import _sun_up_at_location, _SUN_STATUS_CACHE_TTL

        sun_up = await asyncio.to_thread(_sun_up_at_location, lat, lng)
        try:
            from glancerf.gpio import set_output
            set_output("sun_times", "sun_up", sun_up)
        except Exception:
            pass
        cache_key = f"sun_times:status:{lat}|{lng}"
        get_cache().set(cache_key, {"sun_up": sun_up}, _SUN_STATUS_CACHE_TTL)
    except Exception:
        pass
