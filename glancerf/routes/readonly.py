"""
Read-only root page for the secondary server (no WebSocket, no interactions)
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from glancerf.config import get_config
from glancerf.aspect_ratio import get_aspect_ratio_css
from glancerf.view_utils import build_merged_cells_from_spans, build_grid_html
from glancerf.views import render_readonly_page
from glancerf.modules import get_module_assets
from glancerf.logging_config import get_logger

_log = get_logger("readonly")


def register_readonly_routes(readonly_app: FastAPI):
    """Register the read-only root route on the given FastAPI app."""

    @readonly_app.get("/")
    async def readonly_root():
        """Read-only version of main page - no interactions allowed."""
        _log.debug("GET / (readonly)")
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            _log.debug("readonly: config not found")
            return HTMLResponse(
                content="<h1>Configuration not found</h1>", status_code=404
            )

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
        layout = current_config.get("layout")
        if layout is None:
            layout = [[""] * grid_columns for _ in range(grid_rows)]
        grid_html = build_grid_html(
            layout, cell_spans, merged_cells, grid_columns, grid_rows
        )
        grid_css = f"grid-template-columns: repeat({grid_columns}, minmax(0, 1fr)); grid-template-rows: repeat({grid_rows}, minmax(0, 1fr));"
        module_css, module_js = get_module_assets(layout)
        module_settings = current_config.get("module_settings") or {}
        module_settings_json = json.dumps(module_settings)
        setup_callsign_json = json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = json.dumps(current_config.get("setup_location") or "")

        main_port = current_config.get("port")
        if main_port is None or not isinstance(main_port, int):
            main_port = 8080
        _log.debug("readonly: grid=%sx%s main_port=%s", grid_columns, grid_rows, main_port)
        html_content = render_readonly_page(
            aspect_ratio_css=aspect_ratio_css,
            grid_css=grid_css,
            grid_html=grid_html,
            aspect_ratio=aspect_ratio,
            module_css=module_css,
            module_js=module_js,
            module_settings_json=module_settings_json,
            setup_callsign_json=setup_callsign_json,
            setup_location_json=setup_location_json,
            main_port=main_port,
        )
        return HTMLResponse(content=html_content)


def run_readonly_server(
    host: str = "0.0.0.0", port: int = 8081, quiet: bool = False
):
    """Run the read-only FastAPI server (no WebSocket, no interactions)."""
    readonly_app = FastAPI(title="GlanceRF (Read-Only)")
    register_readonly_routes(readonly_app)

    _web_static = Path(__file__).resolve().parent.parent / "web" / "static"
    if _web_static.is_dir():
        readonly_app.mount("/static", StaticFiles(directory=str(_web_static)), name="static")

    import uvicorn
    uvicorn.run(
        readonly_app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
