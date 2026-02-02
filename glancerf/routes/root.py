"""
Root (main clock) page route for GlanceRF
"""

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config
from glancerf.aspect_ratio import get_aspect_ratio_css
from glancerf.view_utils import build_merged_cells_from_spans, build_grid_html
from glancerf.views import render_main_page
from glancerf.modules import get_module_assets
from glancerf.logging_config import get_logger

_log = get_logger("root")


def register_root(app):
    """Register the root (main clock) page route."""

    @app.get("/")
    async def root(request: Request):
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
        if layout is None:
            _log.debug("root: no layout, redirect to layout")
            return RedirectResponse(url="/layout")

        aspect_ratio = current_config.get("aspect_ratio") or "16:9"
        grid_columns = current_config.get("grid_columns")
        grid_rows = current_config.get("grid_rows")

        # Fallback to 3x3 if not configured
        if grid_columns is None:
            grid_columns = 3
            current_config.set("grid_columns", 3)
        if grid_rows is None:
            grid_rows = 3
            current_config.set("grid_rows", 3)
        aspect_ratio_css = get_aspect_ratio_css(aspect_ratio)

        cell_spans = current_config.get("cell_spans") or {}
        merged_cells, _ = build_merged_cells_from_spans(cell_spans)
        grid_html = build_grid_html(
            layout, cell_spans, merged_cells, grid_columns, grid_rows
        )
        grid_css = f"grid-template-columns: repeat({grid_columns}, minmax(0, 1fr)); grid-template-rows: repeat({grid_rows}, minmax(0, 1fr));"
        module_css, module_js = get_module_assets(layout)
        module_settings = current_config.get("module_settings") or {}
        module_settings_json = json.dumps(module_settings)
        setup_callsign_json = json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = json.dumps(current_config.get("setup_location") or "")

        _log.debug("root: rendering main page grid=%sx%s", grid_columns, grid_rows)
        html_content = render_main_page(
            aspect_ratio_css=aspect_ratio_css,
            grid_css=grid_css,
            grid_html=grid_html,
            aspect_ratio=aspect_ratio,
            module_css=module_css,
            module_js=module_js,
            module_settings_json=module_settings_json,
            setup_callsign_json=setup_callsign_json,
            setup_location_json=setup_location_json,
        )
        return HTMLResponse(content=html_content)
