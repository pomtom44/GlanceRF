"""
Layout configurator routes for GlanceRF.
Template and static assets: glancerf/web/templates/layout/, glancerf/web/static/css/layout.css, glancerf/web/static/js/layout.js.
"""

import json as _json
import re
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from glancerf.config import get_config
from glancerf.view_utils import build_merged_cells_from_spans
from glancerf.modules import get_modules, get_module_by_id, get_module_ids
from glancerf.rate_limit import rate_limit_dependency
from glancerf.websocket_manager import ConnectionManager

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_LAYOUT_TEMPLATE_PATH = _WEB_DIR / "templates" / "layout" / "index.html"
_layout_template_cache = None


def _get_layout_template() -> str:
    """Load layout page HTML template from file (cached)."""
    global _layout_template_cache
    if _layout_template_cache is None:
        _layout_template_cache = _LAYOUT_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _layout_template_cache


def register_layout_routes(app: FastAPI, connection_manager: ConnectionManager):
    """Register layout configurator routes."""

    @app.get("/layout")
    async def layout_configurator():
        """Layout configurator page - configure what displays in each grid cell"""
        # Reload config on each request
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")
    
        # Get grid dimensions from config (with fallback defaults)
        grid_columns = current_config.get("grid_columns")
        grid_rows = current_config.get("grid_rows")
        # Fallback to 3x3 if not configured
        if grid_columns is None:
            grid_columns = 3
            current_config.set("grid_columns", 3)
        if grid_rows is None:
            grid_rows = 3
            current_config.set("grid_rows", 3)

        # Get existing layout or create empty one
        layout = current_config.get("layout")
        if layout is None:
            # Create empty layout (2D array)
            layout = [[""] * grid_columns for _ in range(grid_rows)]
        else:
            # Truncate layout to match current grid dimensions
            # Ensure layout has correct number of rows
            while len(layout) > grid_rows:
                layout.pop()
            while len(layout) < grid_rows:
                layout.append([""] * grid_columns)
        
            # Ensure each row has correct number of columns
            for row in layout:
                while len(row) > grid_columns:
                    row.pop()
                while len(row) < grid_columns:
                    row.append("")
    
        # Get cell spans if they exist
        cell_spans = current_config.get("cell_spans")
        if cell_spans is None:
            cell_spans = {}
        else:
            # Filter out cell spans that are outside the new grid bounds
            filtered_spans = {}
            for key, span_info in cell_spans.items():
                try:
                    row, col = map(int, key.split('_'))
                    colspan = span_info.get("colspan", 1)
                    rowspan = span_info.get("rowspan", 1)
                    # Check if the span is within bounds
                    if (row >= 0 and row < grid_rows and 
                        col >= 0 and col < grid_columns and
                        row + rowspan <= grid_rows and
                        col + colspan <= grid_columns):
                        filtered_spans[key] = span_info
                except (ValueError, KeyError):
                    # Skip invalid span entries
                    continue
            cell_spans = filtered_spans
    
        # Generate grid CSS
        grid_css = f"grid-template-columns: repeat({grid_columns}, 1fr); grid-template-rows: repeat({grid_rows}, 1fr);"

        merged_cells, primary_cells = build_merged_cells_from_spans(cell_spans)

        # Generate grid HTML with dropdowns and expand/contract buttons
        grid_html = ""
        cell_index = 0
        for row in range(grid_rows):
            for col in range(grid_columns):
                # Get span information for this cell (if it's a primary cell)
                span_key = f"{row}_{col}"
                span_info = cell_spans.get(span_key, {})
                colspan = span_info.get("colspan", 1) if (row, col) in primary_cells else 1
                rowspan = span_info.get("rowspan", 1) if (row, col) in primary_cells else 1
            
                # Get cell value (only primary cells have values, merged cells are empty)
                if (row, col) in merged_cells:
                    cell_value = ""
                else:
                    cell_value = layout[row][col] if row < len(layout) and col < len(layout[row]) else ""
                module = get_module_by_id(cell_value)
                cell_bg_color = (module or {}).get("color", "#111")
                options_html = "".join(
                    f'<option value="{m["id"]}" {"selected" if cell_value == m["id"] else ""}>{m["name"]}</option>'
                    for m in get_modules()
                )
                grid_html += f'''
                <div class="grid-cell" data-row="{row}" data-col="{col}" data-colspan="{colspan}" data-rowspan="{rowspan}" style="background-color: {cell_bg_color};">
                    <select class="cell-widget-select" data-row="{row}" data-col="{col}" name="cell_{row}_{col}">
                        {options_html}
                    </select>
                    <div class="cell-module-settings"></div>
                    <div class="cell-controls">
                        <button class="expand-btn expand-right" data-row="{row}" data-col="{col}" data-direction="right" title="Expand Right">→</button>
                        <button class="expand-btn expand-down" data-row="{row}" data-col="{col}" data-direction="down" title="Expand Down">↓</button>
                        <button class="contract-btn contract-left" data-row="{row}" data-col="{col}" data-direction="left" title="Contract Left" style="display: none;">←</button>
                        <button class="contract-btn contract-top" data-row="{row}" data-col="{col}" data-direction="top" title="Contract Top" style="display: none;">↑</button>
                    </div>
                </div>
                '''
                cell_index += 1

        # Per-cell module settings: config keyed by "row_col"; migrate legacy (module-id keyed) to by-cell
        raw_module_settings = current_config.get("module_settings") or {}
        module_settings_by_cell = {}
        cell_key_re = re.compile(r"^\d+_\d+$")
        if raw_module_settings and any(cell_key_re.match(str(k)) for k in raw_module_settings.keys()):
            module_settings_by_cell = raw_module_settings
        else:
            # Legacy: keys are module ids; distribute to every cell that has that module
            for r in range(grid_rows):
                for c in range(grid_columns):
                    if r < len(layout) and c < len(layout[r]):
                        cell_value = layout[r][c] or ""
                        if cell_value and raw_module_settings.get(cell_value):
                            key = f"{r}_{c}"
                            module_settings_by_cell[key] = raw_module_settings[cell_value]
        # Schema: module_id -> list of setting dicts (for JS to build in-cell UI)
        modules_settings_schema = {}
        for m in get_modules():
            if m.get("settings"):
                modules_settings_schema[m["id"]] = m["settings"]
        module_settings_by_cell_json = _json.dumps(module_settings_by_cell)
        modules_settings_schema_json = _json.dumps(modules_settings_schema)
        setup_callsign_json = _json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = _json.dumps(current_config.get("setup_location") or "")

        html_content = _get_layout_template()
        html_content = html_content.replace("__GRID_CSS__", grid_css)
        html_content = html_content.replace("__GRID_HTML__", grid_html)
        html_content = html_content.replace("__GRID_COLUMNS__", str(grid_columns))
        html_content = html_content.replace("__GRID_ROWS__", str(grid_rows))
        html_content = html_content.replace("__MODULE_SETTINGS_BY_CELL_JSON__", module_settings_by_cell_json)
        html_content = html_content.replace("__MODULES_SETTINGS_SCHEMA_JSON__", modules_settings_schema_json)
        html_content = html_content.replace("__SETUP_CALLSIGN_JSON__", setup_callsign_json)
        html_content = html_content.replace("__SETUP_LOCATION_JSON__", setup_location_json)

        return HTMLResponse(content=html_content)

    @app.post("/layout")
    async def layout_save(request: Request, _: None = Depends(rate_limit_dependency)):
        """Save layout configuration"""
        try:
            data = await request.json()
            layout = data.get("layout")
            spans = data.get("spans", {})
            module_settings = data.get("module_settings")

            if layout is None:
                return JSONResponse({"error": "Layout data missing"}, status_code=400)

            if not isinstance(layout, list):
                return JSONResponse({"error": "Invalid layout format"}, status_code=400)

            current_config = get_config()
            grid_columns = current_config.get("grid_columns")
            grid_rows = current_config.get("grid_rows")
            if grid_columns is None or grid_rows is None:
                return JSONResponse(
                    {"error": "Grid dimensions not configured (grid_columns, grid_rows)"},
                    status_code=400,
                )
            try:
                grid_columns = int(grid_columns)
                grid_rows = int(grid_rows)
            except (TypeError, ValueError):
                return JSONResponse(
                    {"error": "Grid dimensions must be integers"},
                    status_code=400,
                )
            if grid_columns < 1 or grid_rows < 1:
                return JSONResponse(
                    {"error": "Grid dimensions must be at least 1"},
                    status_code=400,
                )

            if len(layout) != grid_rows:
                return JSONResponse(
                    {"error": f"Layout must have {grid_rows} rows, got {len(layout)}"},
                    status_code=400,
                )

            valid_module_ids = set(get_module_ids())
            for r, row in enumerate(layout):
                if not isinstance(row, list):
                    return JSONResponse(
                        {"error": f"Row {r} is not a list"},
                        status_code=400,
                    )
                if len(row) != grid_columns:
                    return JSONResponse(
                        {"error": f"Row {r} must have {grid_columns} columns, got {len(row)}"},
                        status_code=400,
                    )
                for c, cell_value in enumerate(row):
                    if not isinstance(cell_value, str):
                        return JSONResponse(
                            {"error": f"Cell ({r},{c}) must be a string"},
                            status_code=400,
                        )
                    if cell_value and cell_value not in valid_module_ids:
                        return JSONResponse(
                            {"error": f"Unknown module id at ({r},{c}): {cell_value!r}"},
                            status_code=400,
                        )

            if spans is not None and not isinstance(spans, dict):
                return JSONResponse({"error": "Spans must be an object"}, status_code=400)

            if spans:
                for key, span_info in spans.items():
                    try:
                        parts = key.split("_")
                        if len(parts) != 2:
                            return JSONResponse(
                                {"error": f"Invalid span key: {key!r} (expected row_col)"},
                                status_code=400,
                            )
                        row, col = int(parts[0]), int(parts[1])
                    except (ValueError, AttributeError):
                        return JSONResponse(
                            {"error": f"Invalid span key: {key!r}"},
                            status_code=400,
                        )
                    if row < 0 or row >= grid_rows or col < 0 or col >= grid_columns:
                        return JSONResponse(
                            {"error": f"Span key {key} is outside grid (0-{grid_rows-1} rows, 0-{grid_columns-1} cols)"},
                            status_code=400,
                        )
                    if not isinstance(span_info, dict):
                        return JSONResponse(
                            {"error": f"Span {key} value must be an object"},
                            status_code=400,
                        )
                    colspan = span_info.get("colspan", 1)
                    rowspan = span_info.get("rowspan", 1)
                    try:
                        colspan = int(colspan)
                        rowspan = int(rowspan)
                    except (TypeError, ValueError):
                        return JSONResponse(
                            {"error": f"Span {key} colspan/rowspan must be integers"},
                            status_code=400,
                        )
                    if colspan < 1 or rowspan < 1:
                        return JSONResponse(
                            {"error": f"Span {key} colspan and rowspan must be at least 1"},
                            status_code=400,
                        )
                    if col + colspan > grid_columns or row + rowspan > grid_rows:
                        return JSONResponse(
                            {"error": f"Span {key} (colspan={colspan}, rowspan={rowspan}) goes outside grid"},
                            status_code=400,
                        )

            current_config.set("layout", layout)
            current_config.set("cell_spans", spans or {})
            if module_settings is not None and isinstance(module_settings, dict):
                current_config.set("module_settings", module_settings)

            # Notify all clients (desktop + browsers) so they reload with new layout
            try:
                msg = {"type": "config_update", "data": {"reload": True}}
                if connection_manager.desktop_connection:
                    try:
                        await connection_manager.desktop_connection.send_json(msg)
                    except Exception:
                        connection_manager.desktop_connection = None
                for conn in list(connection_manager.browser_connections):
                    try:
                        await conn.send_json(msg)
                    except Exception:
                        pass
            except Exception:
                pass
        
            return JSONResponse({"success": True})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
