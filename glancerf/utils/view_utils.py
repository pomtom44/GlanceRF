"""
Shared view utilities for GlanceRF
Grid building and span logic for main and readonly pages.
Cell appearance (color, inner HTML) comes from the module dict; no special handling per type.
"""

import html as html_module
from typing import Any, Dict, Optional, Set, Tuple

from glancerf.modules import get_module_by_id


def build_merged_cells_from_spans(cell_spans: Dict[str, Any]) -> Tuple[Set[Tuple[int, int]], Dict]:
    """
    From cell_spans config, compute merged_cells set and primary_cells dict.
    Used when generating grid HTML so merged cells are skipped and primary cells get span styles.
    """
    merged_cells: Set[Tuple[int, int]] = set()
    primary_cells: Dict = {}
    for key, span_info in (cell_spans or {}).items():
        try:
            parts = key.split("_")
            if len(parts) != 2:
                continue
            row, col = int(parts[0]), int(parts[1])
        except (ValueError, AttributeError):
            continue
        colspan = span_info.get("colspan", 1)
        rowspan = span_info.get("rowspan", 1)
        primary_cells[(row, col)] = {"colspan": colspan, "rowspan": rowspan}
        for r in range(row, row + rowspan):
            for c in range(col, col + colspan):
                if r != row or c != col:
                    merged_cells.add((r, c))
    return merged_cells, primary_cells


def build_grid_html(
    layout: list,
    cell_spans: Dict[str, Any],
    merged_cells: Set[Tuple[int, int]],
    grid_columns: int,
    grid_rows: int,
    module_settings: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate grid cells HTML from layout and cell_spans. Each cell uses its module (color, inner_html).
    If module_settings[cell_key].show_title is True (default), a module title is rendered; if False,
    the title is omitted so the content scales to fill the cell."""
    settings = module_settings or {}
    grid_html = ""
    for row in range(grid_rows):
        for col in range(grid_columns):
            if (row, col) in merged_cells:
                continue
            cell_value = (
                layout[row][col]
                if row < len(layout) and col < len(layout[row])
                else ""
            )
            module = get_module_by_id(cell_value)
            cell_color = (module or {}).get("color", "#111")
            inner = (module or {}).get("inner_html", "")
            cell_key = f"{row}_{col}"
            cell_settings = settings.get(cell_key) or {}
            show_title = cell_settings.get("show_title", True)
            if show_title in (False, "false", "0", 0):
                show_title = False
            else:
                show_title = True
            module_name = (module or {}).get("name", "") if (show_title and cell_value) else ""
            if show_title and module_name:
                title_escaped = html_module.escape(module_name, quote=True)
                inner = (
                    f'<div class="glancerf-cell-inner">'
                    f'<div class="glancerf-module-title">{title_escaped}</div>'
                    f'<div class="glancerf-module-content">{inner}</div>'
                    f"</div>"
                )
            else:
                inner = (
                    f'<div class="glancerf-cell-inner">'
                    f'<div class="glancerf-module-content">{inner}</div>'
                    f"</div>"
                )
            span_key = f"{row}_{col}"
            span_info = (cell_spans or {}).get(span_key, {})
            colspan = span_info.get("colspan", 1)
            rowspan = span_info.get("rowspan", 1)
            style = (
                f"background-color: {cell_color}; "
                f"grid-column: span {colspan}; grid-row: span {rowspan};"
            )
            raw = (cell_value or "") if isinstance(cell_value, str) else ""
            safe_id = "".join(c for c in raw if c.isalnum() or c in "_-").replace(" ", "-").strip("-") or ""
            cell_class = f"grid-cell grid-cell-{safe_id}" if safe_id else "grid-cell"
            grid_html += (
                f'<div class="{cell_class}" data-row="{row}" data-col="{col}" style="{style}">{inner}</div>'
            )
    return grid_html
