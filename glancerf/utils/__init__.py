"""
Shared utilities for GlanceRF.
"""

from glancerf.utils.aspect_ratio import (
    get_aspect_ratio_css,
    get_aspect_ratio_list,
    get_aspect_ratio_value,
    calculate_dimensions,
    get_closest_aspect_ratio,
)
from glancerf.utils.cache import TTLCache, get_cache, cache_key
from glancerf.utils.rate_limit import (
    RateLimitExceeded,
    rate_limit_dependency,
    rate_limit_exceeded_handler,
)
from glancerf.utils.restart import trigger_restart
from glancerf.utils.time_utils import get_current_time
from glancerf.utils.utils import get_local_ip
from glancerf.utils.view_utils import build_merged_cells_from_spans, build_grid_html
from glancerf.utils.location import parse_location, get_effective_location, get_effective_location_string
from glancerf.utils.numpy_fallback import try_numpy_baseline_fallback
from glancerf.utils.grid_layout import (
    GRID_LAYOUTS,
    get_grid_layout_list,
    get_grid_layouts_for_aspect_ratio,
    get_grid_layout_name,
    get_grid_layout_css,
    is_valid_grid_layout,
    get_grid_layout_preview_svg,
)

__all__ = [
    "get_current_time",
    "get_local_ip",
    "get_cache",
    "cache_key",
    "TTLCache",
    "trigger_restart",
    "RateLimitExceeded",
    "rate_limit_dependency",
    "rate_limit_exceeded_handler",
    "get_aspect_ratio_css",
    "get_aspect_ratio_list",
    "get_aspect_ratio_value",
    "calculate_dimensions",
    "get_closest_aspect_ratio",
    "build_merged_cells_from_spans",
    "build_grid_html",
    "parse_location",
    "get_effective_location",
    "get_effective_location_string",
    "try_numpy_baseline_fallback",
    "GRID_LAYOUTS",
    "get_grid_layout_list",
    "get_grid_layouts_for_aspect_ratio",
    "get_grid_layout_name",
    "get_grid_layout_css",
    "is_valid_grid_layout",
    "get_grid_layout_preview_svg",
]
