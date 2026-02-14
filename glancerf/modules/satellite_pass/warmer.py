"""Cache warmer for satellite_pass module. Called by core when headless and module is active."""

import asyncio
from typing import Any


async def warm(settings: dict, config: Any) -> None:
    """
    Ensure satellite list cache is populated. Uses same cache TTL as get_satellite_list_cached()
    (satellite_service.SATELLITE_LIST_CACHE_MAX_AGE_SECONDS): if satellite_list.json is missing
    or older than that, fetches from CelesTrak (stations + amateur) and saves; otherwise returns from file.
    Idempotent.
    """
    try:
        from glancerf.modules.satellite_pass.satellite_service import get_satellite_list_cached

        await asyncio.to_thread(get_satellite_list_cached)
    except Exception:
        pass
