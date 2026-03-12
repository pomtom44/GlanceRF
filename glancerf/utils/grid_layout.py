"""
Grid layout utilities for GlanceRF
Defines different layout options for arranging UI elements
"""

from typing import Dict, List, Optional, Tuple


# Available grid layouts: name -> description
GRID_LAYOUTS: Dict[str, str] = {
    "grid-2x2-equal": "2x2 Equal Grid",
    "grid-3x3-equal": "3x3 Equal Grid",
    "grid-3x3-map-tl": "3x3 Map Top-Left",
    "grid-3x3-map-tr": "3x3 Map Top-Right",
    "grid-3x3-map-bl": "3x3 Map Bottom-Left",
    "grid-3x3-map-br": "3x3 Map Bottom-Right",
    "grid-4x4-map-center": "4x4 Map Center",
    "grid-4x4-map-tl": "4x4 Map Top-Left",
    "grid-4x4-map-tr": "4x4 Map Top-Right",
    "sidebar-2-left": "2 Sidebars Left",
    "sidebar-2-right": "2 Sidebars Right",
    "sidebar-3-left": "3 Sidebars Left",
    "sidebar-3-right": "3 Sidebars Right",
    "sidebar-2-split": "2 Sidebars Split",
    "sidebar-3-split": "3 Sidebars Split",
}


def get_grid_layout_list() -> List[str]:
    """Get list of available grid layout names"""
    return list(GRID_LAYOUTS.keys())


def get_grid_layouts_for_aspect_ratio(aspect_ratio: str) -> List[str]:
    """
    Get grid layouts suitable for a given aspect ratio

    Args:
        aspect_ratio: Aspect ratio name (e.g., "16:9", "21:9")

    Returns:
        List of layout names suitable for the aspect ratio
    """
    wide_ratios = ["21:9", "32:9"]
    if aspect_ratio in wide_ratios:
        return [
            "sidebar-2-left",
            "sidebar-2-right",
            "sidebar-3-left",
            "sidebar-3-right",
            "sidebar-2-split",
            "sidebar-3-split",
        ]
    return [
        "grid-2x2-equal",
        "grid-3x3-equal",
        "grid-3x3-map-tl",
        "grid-3x3-map-tr",
        "grid-3x3-map-bl",
        "grid-3x3-map-br",
        "grid-4x4-map-center",
        "grid-4x4-map-tl",
        "grid-4x4-map-tr",
    ]


def get_grid_layout_name(layout_name: str) -> Optional[str]:
    """Get display name for a grid layout."""
    return GRID_LAYOUTS.get(layout_name)


def get_grid_layout_css(layout_name: str) -> Tuple[str, str]:
    """
    Generate CSS grid template and HTML structure for a grid layout.

    Returns:
        Tuple of (css_grid_template, html_structure)
    """
    if layout_name == "grid-2x2-equal":
        return (
            "grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 1fr);",
            '<div class="grid-cell"></div>' * 4
        )
    elif layout_name == "grid-3x3-equal":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell"></div>' * 9
        )
    elif layout_name == "grid-3x3-map-tl":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1 / 3; grid-row: 1 / 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'
        )
    elif layout_name == "grid-3x3-map-tr":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 1 / 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'
        )
    elif layout_name == "grid-3x3-map-bl":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 1 / 3; grid-row: 2 / 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'
        )
    elif layout_name == "grid-3x3-map-br":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 2 / 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'
        )
    elif layout_name == "grid-4x4-map-center":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 2 / 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'
        )
    elif layout_name == "grid-4x4-map-tl":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1 / 4; grid-row: 1 / 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'
        )
    elif layout_name == "grid-4x4-map-tr":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'
            + '<div class="grid-cell" style="grid-column: 2 / 5; grid-row: 1 / 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'
        )
    elif layout_name == "sidebar-2-left":
        return (
            "grid-template-columns: 1fr 2fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell"></div>' * 2 + '<div class="grid-cell" style="grid-row: 1 / 3;"></div>'
        )
    elif layout_name == "sidebar-2-right":
        return (
            "grid-template-columns: 2fr 1fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 3;"></div>' + '<div class="grid-cell"></div>' * 2
        )
    elif layout_name == "sidebar-3-left":
        return (
            "grid-template-columns: 1fr 3fr; grid-template-rows: 1fr 1fr 1fr;",
            '<div class="grid-cell"></div>' * 3 + '<div class="grid-cell" style="grid-row: 1 / 4;"></div>'
        )
    elif layout_name == "sidebar-3-right":
        return (
            "grid-template-columns: 3fr 1fr; grid-template-rows: 1fr 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 4;"></div>' + '<div class="grid-cell"></div>' * 3
        )
    elif layout_name == "sidebar-2-split":
        return (
            "grid-template-columns: 1fr 2fr 1fr; grid-template-rows: 1fr;",
            '<div class="grid-cell"></div>' * 3
        )
    elif layout_name == "sidebar-3-split":
        return (
            "grid-template-columns: 1fr 3fr 1fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 3;"></div>' * 2 + '<div class="grid-cell"></div>' * 2
        )
    else:
        return (
            "grid-template-columns: 1fr; grid-template-rows: 1fr;",
            '<div class="grid-cell"></div>'
        )


def is_valid_grid_layout(layout_name: str) -> bool:
    """Check if a grid layout name is valid."""
    return layout_name in GRID_LAYOUTS


def get_grid_layout_preview_svg(layout_name: str, width: int = 200, height: int = 150) -> str:
    """Generate SVG preview image for a grid layout."""
    grid_color = "#0f0"
    map_color = "#555"
    widget_color = "#555"
    svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#000" stroke="{grid_color}" stroke-width="1"/>')

    if layout_name == "grid-2x2-equal":
        cell_w, cell_h = width / 2, height / 2
        for i in range(2):
            for j in range(2):
                svg_parts.append(f'<rect x="{i*cell_w}" y="{j*cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    elif layout_name == "grid-3x3-equal":
        cell_w, cell_h = width / 3, height / 3
        for i in range(3):
            for j in range(3):
                svg_parts.append(f'<rect x="{i*cell_w}" y="{j*cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    elif layout_name == "grid-3x3-map-tl":
        map_w, map_h = width * 2 / 3, height * 2 / 3
        widget_w, widget_h = width / 3, height / 3
        svg_parts.append(f'<rect x="0" y="0" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    else:
        svg_parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')

    svg_parts.append('</svg>')
    return ''.join(svg_parts)
