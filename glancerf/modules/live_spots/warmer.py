"""Cache warmer for live_spots module. Called by core when headless and module is active."""

import asyncio
from typing import Any


async def warm(settings: dict, config: Any) -> None:
    """Warm PSK Reporter cache for configured callsign/grid. No-op if callsign_or_grid empty."""
    callsign_or_grid = (settings.get("callsign_or_grid") or "").strip()
    if not callsign_or_grid:
        return
    filter_mode = (settings.get("filter_mode") or "received").strip().lower()
    age_mins = 60
    try:
        age_raw = settings.get("age_mins")
        if age_raw is not None and age_raw != "":
            age_mins = max(1, min(1440, int(age_raw)))
    except (TypeError, ValueError):
        pass
    flow_seconds = -age_mins * 60
    try:
        from glancerf.modules.live_spots.spots_service import get_pskreporter_cached

        await asyncio.to_thread(
            get_pskreporter_cached,
            filter_mode=filter_mode,
            callsign_or_grid=callsign_or_grid,
            flow_seconds=flow_seconds,
            rpt_limit=200,
        )
    except Exception:
        pass
