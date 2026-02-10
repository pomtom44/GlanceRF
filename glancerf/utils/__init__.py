"""
Shared utilities for GlanceRF.
"""

from glancerf.utils.utils import get_local_ip
from glancerf.utils.time_utils import get_current_time
from glancerf.utils.view_utils import build_merged_cells_from_spans, build_grid_html
from glancerf.utils.aspect_ratio import (
    get_aspect_ratio_list,
    get_aspect_ratio_value,
    get_aspect_ratio_css,
    calculate_dimensions,
    get_closest_aspect_ratio,
    ASPECT_RATIOS,
)
from glancerf.utils.grid_layout import (
    get_grid_layout_list,
    get_grid_layouts_for_aspect_ratio,
    get_grid_layout_name,
    get_grid_layout_css,
    is_valid_grid_layout,
    get_grid_layout_preview_svg,
    GRID_LAYOUTS,
)
from glancerf.utils.rate_limit import (
    RateLimitExceeded,
    rate_limit_dependency,
    rate_limit_exceeded_handler,
)
from glancerf.utils.restart import trigger_restart

__all__ = [
    "get_local_ip",
    "get_current_time",
    "build_merged_cells_from_spans",
    "build_grid_html",
    "get_aspect_ratio_list",
    "get_aspect_ratio_value",
    "get_aspect_ratio_css",
    "calculate_dimensions",
    "get_closest_aspect_ratio",
    "ASPECT_RATIOS",
    "get_grid_layout_list",
    "get_grid_layouts_for_aspect_ratio",
    "get_grid_layout_name",
    "get_grid_layout_css",
    "is_valid_grid_layout",
    "get_grid_layout_preview_svg",
    "GRID_LAYOUTS",
    "RateLimitExceeded",
    "rate_limit_dependency",
    "rate_limit_exceeded_handler",
    "trigger_restart",
]
