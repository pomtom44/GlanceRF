"""
Root (main clock) page route for GlanceRF.
"""

import json
import time

from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config, get_logger
from glancerf.web.menu_html import get_menu_html
from glancerf.modules import get_module_assets, get_modules
from glancerf.utils import build_merged_cells_from_spans, build_grid_html, get_aspect_ratio_css, get_effective_location_string
from glancerf.views import render_main_page

_log = get_logger("root")


def register_root(app):
    """Register the root (main clock) page route."""

    @app.get("/")
    async def root():
        """Serve the main HTML page or redirect to setup."""
        _log.debug("GET / (main)")
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            _log.debug("root: config not found, redirect to setup")
            return RedirectResponse(url="/setup")

        if current_config.get("first_run"):
            _log.debug("root: first_run=true, redirect to setup")
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout")
        grid_columns = current_config.get("grid_columns")
        grid_rows = current_config.get("grid_rows")
        aspect_ratio = current_config.get("aspect_ratio")
        if layout is None:
            _log.debug("root: no layout, redirect to layout")
            return RedirectResponse(url="/layout")
        if grid_columns is None or grid_rows is None or not aspect_ratio:
            _log.debug("root: config incomplete, redirect to setup")
            return RedirectResponse(url="/setup")
        aspect_ratio_css = get_aspect_ratio_css(aspect_ratio)

        cell_spans = current_config.get("cell_spans") or {}
        merged_cells, _ = build_merged_cells_from_spans(cell_spans)
        module_settings = current_config.get("module_settings") or {}
        has_any_module = any(
            (cell or "").strip()
            for row in layout
            for cell in (row if isinstance(row, (list, tuple)) else [])
        )
        if not has_any_module:
            grid_html = (
                '<div class="empty-state-message">'
                'Press <kbd>M</kbd> to get started loading modules in</div>'
            )
            grid_css = "display: flex; align-items: center; justify-content: center; min-height: 100%;"
        else:
            grid_html = build_grid_html(
                layout,
                cell_spans,
                merged_cells,
                grid_columns,
                grid_rows,
                module_settings=module_settings,
            )
            grid_css = f"grid-template-columns: repeat({grid_columns}, minmax(0, 1fr)); grid-template-rows: repeat({grid_rows}, minmax(0, 1fr));"
        map_overlay_layout = current_config.get("map_overlay_layout") or []
        if not isinstance(map_overlay_layout, list):
            map_overlay_layout = []
        map_overlay_layout = [m for m in map_overlay_layout if m and isinstance(m, str)]
        # Include layout modules so APRS/satellite_pass in grid feed map overlay (dots/icons)
        overlay_modules = set(map_overlay_layout)
        if layout:
            for row in layout:
                if isinstance(row, (list, tuple)):
                    for cell in row:
                        if cell and isinstance(cell, str) and cell.strip():
                            overlay_modules.add(cell.strip())
        module_css, module_js = get_module_assets(layout, map_overlay_layout=map_overlay_layout)
        modules_settings_schema = {}
        show_title = {"id": "show_title", "label": "Show module title", "type": "checkbox", "default": True}
        for m in get_modules():
            mid = m.get("id", "")
            if mid:
                modules_settings_schema[mid] = [show_title] + list(m.get("settings") or [])
        module_settings_json = json.dumps(module_settings)
        modules_settings_schema_json = json.dumps(modules_settings_schema)
        map_overlay_modules_json = json.dumps(list(overlay_modules))
        map_overlay_layout_json = json.dumps(map_overlay_layout)
        setup_callsign_json = json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = json.dumps(get_effective_location_string(current_config))
        on_the_air_shortcut_json = json.dumps(current_config.get("on_the_air_shortcut") or "")

        _log.debug("root: rendering main page grid=%sx%s", grid_columns, grid_rows)
        cache_bust = str(int(time.time() * 1000))
        html_content = render_main_page(
            aspect_ratio_css=aspect_ratio_css,
            grid_css=grid_css,
            grid_html=grid_html,
            module_css=module_css,
            module_js=module_js,
            module_settings_json=module_settings_json,
            modules_settings_schema_json=modules_settings_schema_json,
            map_overlay_modules_json=map_overlay_modules_json,
            map_overlay_layout_json=map_overlay_layout_json,
            setup_callsign_json=setup_callsign_json,
            setup_location_json=setup_location_json,
            on_the_air_shortcut_json=on_the_air_shortcut_json,
            cache_bust=cache_bust,
        )
        html_content = html_content.replace("__GLANCERF_MENU_PANEL__", get_menu_html())
        return HTMLResponse(content=html_content)
