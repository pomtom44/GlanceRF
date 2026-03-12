"""
Aspect ratio utilities for GlanceRF.
"""

from typing import Dict, List, Optional, Tuple

ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "1:1": (1, 1),
    "4:3": (4, 3),
    "16:9": (16, 9),
    "16:10": (16, 10),
    "21:9": (21, 9),
    "32:9": (32, 9),
}


def get_aspect_ratio_list() -> List[str]:
    """Get list of available aspect ratio names."""
    return list(ASPECT_RATIOS.keys())


def get_aspect_ratio_value(ratio_name: str) -> Optional[Tuple[int, int]]:
    """Get (width, height) tuple from ratio name."""
    return ASPECT_RATIOS.get(ratio_name)


def get_aspect_ratio_css(ratio_name: str) -> str:
    """Get CSS aspect-ratio property value (e.g. '16 / 9')."""
    ratio = get_aspect_ratio_value(ratio_name)
    if not ratio:
        ratio = ASPECT_RATIOS["16:9"]
    return f"{ratio[0]} / {ratio[1]}"


def calculate_dimensions(
    ratio_name: str,
    max_width: int,
    max_height: int,
    orientation: str = "landscape",
) -> tuple:
    """Calculate dimensions for a given aspect ratio that fits within max bounds."""
    ratio = get_aspect_ratio_value(ratio_name)
    if not ratio:
        ratio = ASPECT_RATIOS["16:9"]
    width_ratio, height_ratio = ratio
    if orientation == "portrait":
        width_ratio, height_ratio = height_ratio, width_ratio
    width = max_width
    height = int(width * height_ratio / width_ratio)
    if height > max_height:
        height = max_height
        width = int(height * width_ratio / height_ratio)
    return (width, height)


def get_closest_aspect_ratio(width: int, height: int) -> str:
    """Return the predefined aspect ratio name closest to width/height."""
    if width <= 0 or height <= 0:
        return "16:9"
    actual_ratio = width / height
    best_name = "16:9"
    best_diff = float("inf")
    for name, (w, h) in ASPECT_RATIOS.items():
        target = w / h
        diff = abs(actual_ratio - target)
        if diff < best_diff:
            best_diff = diff
            best_name = name
    return best_name
