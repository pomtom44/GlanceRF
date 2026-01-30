"""
Grid layout utilities for GlanceRF
Defines different layout options for arranging UI elements
"""

from typing import Dict, Optional


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


def get_grid_layout_list() -> list[str]:
    """Get list of available grid layout names"""
    return list(GRID_LAYOUTS.keys())


def get_grid_layouts_for_aspect_ratio(aspect_ratio: str) -> list[str]:
    """
    Get grid layouts suitable for a given aspect ratio
    
    Args:
        aspect_ratio: Aspect ratio name (e.g., "16:9", "21:9")
    
    Returns:
        List of layout names suitable for the aspect ratio
    """
    # Wide aspect ratios (21:9, 32:9) - show sidebar layouts
    wide_ratios = ["21:9", "32:9"]
    
    # Standard aspect ratios - show grid layouts
    if aspect_ratio in wide_ratios:
        return [
            "sidebar-2-left",
            "sidebar-2-right",
            "sidebar-3-left",
            "sidebar-3-right",
            "sidebar-2-split",
            "sidebar-3-split",
        ]
    else:
        # Standard aspect ratios (1:1, 4:3, 16:9, 16:10)
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
    """
    Get display name for a grid layout
    
    Args:
        layout_name: Grid layout name (e.g., "single")
    
    Returns:
        Display name or None if invalid
    """
    return GRID_LAYOUTS.get(layout_name)


def get_grid_layout_css(layout_name: str) -> tuple[str, str]:
    """
    Generate CSS grid template and HTML structure for a grid layout
    
    Args:
        layout_name: Grid layout name
    
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
            '<div class="grid-cell" style="grid-column: 1 / 3; grid-row: 1 / 3;"></div>'  # Map (spans 2x2)
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'  # Top right
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 2;"></div>'  # Middle right
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'  # Bottom left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 3;"></div>'  # Bottom middle
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'  # Bottom right
        )
    elif layout_name == "grid-3x3-map-tr":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'  # Top left
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'  # Middle left
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 1 / 3;"></div>'  # Map (spans 2x2)
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'  # Bottom left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 3;"></div>'  # Bottom middle
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'  # Bottom right
        )
    elif layout_name == "grid-3x3-map-bl":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'  # Top left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'  # Top middle
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'  # Top right
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 2;"></div>'  # Middle right
            + '<div class="grid-cell" style="grid-column: 1 / 3; grid-row: 2 / 4;"></div>'  # Map (spans 2x2, columns 1-2, rows 2-3)
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 3;"></div>'  # Bottom right
        )
    elif layout_name == "grid-3x3-map-br":
        return (
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'  # Top left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'  # Top middle
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'  # Top right
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'  # Middle left
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 2 / 4;"></div>'  # Map (spans 2x2, columns 2-3, rows 2-3)
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'  # Bottom left
        )
    elif layout_name == "grid-4x4-map-center":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'  # Top left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 1;"></div>'  # Top middle-left
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 1;"></div>'  # Top middle-right
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 1;"></div>'  # Top right
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'  # Left row 2
            + '<div class="grid-cell" style="grid-column: 2 / 4; grid-row: 2 / 4;"></div>'  # Map center (spans 2x2, columns 2-3, rows 2-3)
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 2;"></div>'  # Right row 2
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'  # Left row 3
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 3;"></div>'  # Right row 3
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'  # Bottom left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'  # Bottom middle-left
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'  # Bottom middle-right
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'  # Bottom right
        )
    elif layout_name == "grid-4x4-map-tl":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1 / 4; grid-row: 1 / 4;"></div>'  # Map (spans 3x3)
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 1;"></div>'  # Right top
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 2;"></div>'  # Right middle-top
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 3;"></div>'  # Right middle-bottom
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'  # Bottom left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'  # Bottom middle-left
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'  # Bottom middle-right
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'  # Bottom right
        )
    elif layout_name == "grid-4x4-map-tr":
        return (
            "grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr);",
            '<div class="grid-cell" style="grid-column: 1; grid-row: 1;"></div>'  # Left top
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 2;"></div>'  # Left middle-top
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 3;"></div>'  # Left middle-bottom
            + '<div class="grid-cell" style="grid-column: 2 / 5; grid-row: 1 / 4;"></div>'  # Map (spans 3x3)
            + '<div class="grid-cell" style="grid-column: 1; grid-row: 4;"></div>'  # Bottom left
            + '<div class="grid-cell" style="grid-column: 2; grid-row: 4;"></div>'  # Bottom middle-left
            + '<div class="grid-cell" style="grid-column: 3; grid-row: 4;"></div>'  # Bottom middle-right
            + '<div class="grid-cell" style="grid-column: 4; grid-row: 4;"></div>'  # Bottom right
        )
    elif layout_name == "sidebar-2-left":
        return (
            "grid-template-columns: 1fr 2fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell"></div>' * 2  # Left sidebars
            + '<div class="grid-cell" style="grid-row: 1 / 3;"></div>'  # Main area
        )
    elif layout_name == "sidebar-2-right":
        return (
            "grid-template-columns: 2fr 1fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 3;"></div>'  # Main area
            + '<div class="grid-cell"></div>' * 2  # Right sidebars
        )
    elif layout_name == "sidebar-3-left":
        return (
            "grid-template-columns: 1fr 3fr; grid-template-rows: 1fr 1fr 1fr;",
            '<div class="grid-cell"></div>' * 3  # Left sidebars
            + '<div class="grid-cell" style="grid-row: 1 / 4;"></div>'  # Main area
        )
    elif layout_name == "sidebar-3-right":
        return (
            "grid-template-columns: 3fr 1fr; grid-template-rows: 1fr 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 4;"></div>'  # Main area
            + '<div class="grid-cell"></div>' * 3  # Right sidebars
        )
    elif layout_name == "sidebar-2-split":
        return (
            "grid-template-columns: 1fr 2fr 1fr; grid-template-rows: 1fr;",
            '<div class="grid-cell"></div>'  # Left sidebar
            + '<div class="grid-cell"></div>'  # Main area
            + '<div class="grid-cell"></div>'  # Right sidebar
        )
    elif layout_name == "sidebar-3-split":
        return (
            "grid-template-columns: 1fr 3fr 1fr; grid-template-rows: 1fr 1fr;",
            '<div class="grid-cell" style="grid-row: 1 / 3;"></div>'  # Left sidebar
            + '<div class="grid-cell" style="grid-row: 1 / 3;"></div>'  # Main area
            + '<div class="grid-cell"></div>' * 2  # Right sidebars
        )
    else:
        # Default: single cell
        return (
            "grid-template-columns: 1fr; grid-template-rows: 1fr;",
            '<div class="grid-cell"></div>'
        )


def is_valid_grid_layout(layout_name: str) -> bool:
    """
    Check if a grid layout name is valid
    
    Args:
        layout_name: Grid layout name to validate
    
    Returns:
        True if valid, False otherwise
    """
    return layout_name in GRID_LAYOUTS


def get_grid_layout_preview_svg(layout_name: str, width: int = 200, height: int = 150) -> str:
    """
    Generate SVG preview image for a grid layout
    
    Args:
        layout_name: Grid layout name
        width: SVG width in pixels
        height: SVG height in pixels
    
    Returns:
        SVG string for the preview
    """
    # Colors
    bg_color = "#000"
    grid_color = "#0f0"  # Green lines
    map_color = "#555"   # Grey squares (same as widgets)
    widget_color = "#555"  # Grey squares
    border_color = "#666"
    
    svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="{bg_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    if layout_name == "grid-2x2-equal":
        # 2x2 equal grid
        cell_w = width / 2
        cell_h = height / 2
        for i in range(2):
            for j in range(2):
                x = i * cell_w
                y = j * cell_h
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-3x3-equal":
        # 3x3 equal grid
        cell_w = width / 3
        cell_h = height / 3
        for i in range(3):
            for j in range(3):
                x = i * cell_w
                y = j * cell_h
                svg_parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-3x3-map-tl":
        # 3x3 with big map top-left (2x2), 2 small widgets
        map_w = width * 2 / 3
        map_h = height * 2 / 3
        widget_w = width / 3
        widget_h = height / 3
        
        # Big map top-left
        svg_parts.append(f'<rect x="0" y="0" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Small widgets
        svg_parts.append(f'<rect x="{map_w}" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-3x3-map-tr":
        # 3x3 with big map top-right (2x2), 2 small widgets
        map_w = width * 2 / 3
        map_h = height * 2 / 3
        widget_w = width / 3
        widget_h = height / 3
        
        # Small widgets top-left
        svg_parts.append(f'<rect x="0" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Big map top-right
        svg_parts.append(f'<rect x="{widget_w}" y="0" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Small widgets bottom
        svg_parts.append(f'<rect x="0" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="{map_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-3x3-map-bl":
        # 3x3 with big map bottom-left (2x2), 2 small widgets
        map_w = width * 2 / 3
        map_h = height * 2 / 3
        widget_w = width / 3
        widget_h = height / 3
        
        # Small widgets top
        svg_parts.append(f'<rect x="0" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Big map bottom-left
        svg_parts.append(f'<rect x="0" y="{widget_h}" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-3x3-map-br":
        # 3x3 with big map bottom-right (2x2), 2 small widgets
        map_w = width * 2 / 3
        map_h = height * 2 / 3
        widget_w = width / 3
        widget_h = height / 3
        
        # Small widgets top-left
        svg_parts.append(f'<rect x="0" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="0" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{widget_w}" y="{widget_h}" width="{widget_w}" height="{widget_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Big map bottom-right
        svg_parts.append(f'<rect x="{widget_w}" y="{widget_h}" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-4x4-map-center":
        # 4x4 with map in center, widgets on sides
        cell_w = width / 4
        cell_h = height / 4
        
        # Top row widgets
        svg_parts.append(f'<rect x="0" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w}" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*2}" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Middle row - widgets on sides, map in center
        svg_parts.append(f'<rect x="0" y="{cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w}" y="{cell_h}" width="{cell_w*2}" height="{cell_h*2}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="{cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Bottom row widgets
        svg_parts.append(f'<rect x="0" y="{cell_h*2}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="{cell_h*2}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{cell_h*3}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w}" y="{cell_h*3}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*2}" y="{cell_h*3}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="{cell_h*3}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-4x4-map-tl":
        # 4x4 with big map top-left (3x3), widgets around
        map_w = width * 3 / 4
        map_h = height * 3 / 4
        cell_w = width / 4
        cell_h = height / 4
        
        # Big map top-left
        svg_parts.append(f'<rect x="0" y="0" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Widgets on right side
        svg_parts.append(f'<rect x="{map_w}" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="{cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{map_w}" y="{cell_h*2}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Widgets on bottom
        svg_parts.append(f'<rect x="0" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*2}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "grid-4x4-map-tr":
        # 4x4 with big map top-right (3x3), widgets around
        map_w = width * 3 / 4
        map_h = height * 3 / 4
        cell_w = width / 4
        cell_h = height / 4
        
        # Widgets on left side
        svg_parts.append(f'<rect x="0" y="0" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{cell_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{cell_h*2}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Big map top-right
        svg_parts.append(f'<rect x="{cell_w}" y="0" width="{map_w}" height="{map_h}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Widgets on bottom
        svg_parts.append(f'<rect x="0" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*2}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{cell_w*3}" y="{map_h}" width="{cell_w}" height="{cell_h}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-2-left":
        # 2 sidebars on left, main area on right
        sidebar_w = width / 3
        main_w = width * 2 / 3
        
        # Left sidebars
        svg_parts.append(f'<rect x="0" y="0" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{height/2}" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Main area (map)
        svg_parts.append(f'<rect x="{sidebar_w}" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-2-right":
        # 2 sidebars on right, main area on left
        sidebar_w = width / 3
        main_w = width * 2 / 3
        
        # Main area (map)
        svg_parts.append(f'<rect x="0" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Right sidebars
        svg_parts.append(f'<rect x="{main_w}" y="0" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{main_w}" y="{height/2}" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-3-left":
        # 3 sidebars on left, main area on right
        sidebar_w = width / 4
        main_w = width * 3 / 4
        
        # Left sidebars
        svg_parts.append(f'<rect x="0" y="0" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{height/3}" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="0" y="{height*2/3}" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Main area (map)
        svg_parts.append(f'<rect x="{sidebar_w}" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-3-right":
        # 3 sidebars on right, main area on left
        sidebar_w = width / 4
        main_w = width * 3 / 4
        
        # Main area (map)
        svg_parts.append(f'<rect x="0" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Right sidebars
        svg_parts.append(f'<rect x="{main_w}" y="0" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{main_w}" y="{height/3}" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{main_w}" y="{height*2/3}" width="{sidebar_w}" height="{height/3}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-2-split":
        # 2 sidebars split (one left, one right), main area in center
        sidebar_w = width / 4
        main_w = width / 2
        
        # Left sidebar
        svg_parts.append(f'<rect x="0" y="0" width="{sidebar_w}" height="{height}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Main area (map)
        svg_parts.append(f'<rect x="{sidebar_w}" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Right sidebar
        svg_parts.append(f'<rect x="{sidebar_w + main_w}" y="0" width="{sidebar_w}" height="{height}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    elif layout_name == "sidebar-3-split":
        # 3 sidebars split (one left, two right), main area in center
        sidebar_w = width / 5
        main_w = width * 3 / 5
        
        # Left sidebar
        svg_parts.append(f'<rect x="0" y="0" width="{sidebar_w}" height="{height}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Main area (map)
        svg_parts.append(f'<rect x="{sidebar_w}" y="0" width="{main_w}" height="{height}" fill="{map_color}" stroke="{grid_color}" stroke-width="1"/>')
        
        # Right sidebars
        svg_parts.append(f'<rect x="{sidebar_w + main_w}" y="0" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
        svg_parts.append(f'<rect x="{sidebar_w + main_w}" y="{height/2}" width="{sidebar_w}" height="{height/2}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    else:
        # Default: single cell
        svg_parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{widget_color}" stroke="{grid_color}" stroke-width="1"/>')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)
