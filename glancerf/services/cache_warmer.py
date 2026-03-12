"""
Background cache warmer for GlanceRF.
Periodically runs each active module's warmer.warm(settings, config) so caches
stay warm when headless (no browser/desktop connected).

Modules opt in via MODULE["cache_warmer"] = True and provide warmer.py with:
    async def warm(settings: dict, config: Any) -> None

No core changes needed when adding new cacheable modules.
"""

import asyncio
from typing import Any

from glancerf.config import get_config, get_logger

_log = get_logger("cache_warmer")

_INTERVAL_SEC = 300
_START_DELAY_SEC = 30

_task: asyncio.Task | None = None


def _active_cells_with_settings(config: Any) -> list:
    """Return list of (module_id, cell_settings, cell_key) for each non-empty cell.
    Includes map_overlay_layout modules when map is in the layout (with empty settings)."""
    layout = config.get("layout") or []
    if not isinstance(layout, list):
        return []
    module_settings = config.get("module_settings") or {}
    if not isinstance(module_settings, dict):
        module_settings = {}
    result = []
    ids_in_layout = set()
    for row_idx, row in enumerate(layout):
        if not isinstance(row, list):
            continue
        for col_idx, cell_value in enumerate(row):
            if not isinstance(cell_value, str) or not cell_value.strip():
                continue
            mid = cell_value.strip()
            ids_in_layout.add(mid)
            cell_key = f"{row_idx}_{col_idx}"
            settings = module_settings.get(cell_key)
            if not isinstance(settings, dict):
                settings = {}
            result.append((mid, settings, cell_key))
    if "map" in ids_in_layout:
        map_overlay = config.get("map_overlay_layout") or []
        if isinstance(map_overlay, list):
            for i, mid in enumerate(map_overlay):
                if mid and isinstance(mid, str):
                    mid = mid.strip()
                    if mid and mid not in ids_in_layout:
                        result.append((mid, {}, f"map_overlay_{i}"))
    return result


async def _run_cycle() -> None:
    try:
        config = get_config()
    except (FileNotFoundError, IOError) as e:
        _log.debug("cache_warmer: cycle skip (config load failed): %s", e)
        return
    try:
        from glancerf.modules import get_module_warmer
    except ImportError:
        _log.debug("cache_warmer: get_module_warmer not available")
        return
    cells = _active_cells_with_settings(config)
    to_warm = []
    for mid, s, ck in cells:
        w = get_module_warmer(mid)
        if w is not None:
            to_warm.append((mid, s, ck, w))
    _log.debug("cache_warmer: cycle started, %d cells, %d with warmer", len(cells), len(to_warm))
    for module_id, settings, cell_key, warmer in to_warm:
        _log.debug("cache_warmer: warming %s (cell %s)", module_id, cell_key)
        try:
            await warmer(settings, config)
            _log.debug("cache_warmer: %s (cell %s) done", module_id, cell_key)
        except Exception as e:
            _log.debug("cache_warmer: %s (cell %s) error: %s", module_id, cell_key, e)
    _log.debug("cache_warmer: cycle finished")


async def _loop() -> None:
    await asyncio.sleep(_START_DELAY_SEC)
    _log.debug("cache_warmer: background loop started")
    while True:
        try:
            await _run_cycle()
        except asyncio.CancelledError:
            break
        except Exception as e:
            _log.debug("cache_warmer: cycle error: %s", e)
        await asyncio.sleep(_INTERVAL_SEC)


def start_cache_warmer() -> None:
    """Start the cache warmer background task."""
    global _task
    if _task is not None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        _log.debug("cache_warmer: no running loop, skip start")
        return
    _task = loop.create_task(_loop())
    _log.debug("cache_warmer: started")


def stop_cache_warmer() -> None:
    """Stop the cache warmer background task."""
    global _task
    if _task is None:
        return
    _task.cancel()
    _task = None
    _log.debug("cache_warmer: stopped")
