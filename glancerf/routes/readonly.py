"""
Read-only server for GlanceRF.
Separate server on readonly_port with no WebSocket or interactive features.
Serves full clock display; connects to main server WebSocket for config_update reload.
"""

import json
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from glancerf.config import get_config, get_logger
from glancerf.web.menu_html import get_menu_html
from glancerf.modules import get_module_assets, get_modules
from glancerf.utils import build_merged_cells_from_spans, build_grid_html, get_aspect_ratio_css
from glancerf.views import render_readonly_page

_log = get_logger("readonly")

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def _get_logo_path():
    """Return path to logo.png."""
    p = _PROJECT_DIR / "logos" / "logo.png"
    if p.is_file():
        return p
    p = _PROJECT_DIR.parent / "logo.png"
    return p if p.is_file() else None


def register_readonly_routes(readonly_app: FastAPI) -> None:
    """Register read-only root route on the given FastAPI app."""

    @readonly_app.get("/logo.png", include_in_schema=False)
    def _serve_logo():
        path = _get_logo_path()
        if path is not None:
            return FileResponse(str(path), media_type="image/png")
        return Response(status_code=404)

    @readonly_app.get("/api/ready")
    async def readonly_ready():
        """Readiness check for startup verification."""
        return {"ready": True}

    @readonly_app.get("/")
    async def readonly_root(request: Request):
        """Read-only version of main page - full clock display, no interactions."""
        _log.debug("GET / (readonly)")
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            _log.debug("readonly: config not found")
            return HTMLResponse(
                content="<h1>Configuration not found</h1><p>Run setup first.</p>",
                status_code=404,
            )

        if current_config.get("first_run"):
            return HTMLResponse(
                content="<h1>Setup required</h1><p>Complete setup at the main interface first.</p>",
                status_code=200,
            )

        layout = current_config.get("layout")
        grid_columns = current_config.get("grid_columns")
        grid_rows = current_config.get("grid_rows")
        aspect_ratio = current_config.get("aspect_ratio")
        if layout is None or grid_columns is None or grid_rows is None or not aspect_ratio:
            return HTMLResponse(
                content="<h1>Configuration incomplete</h1><p>Complete setup at the main interface.</p>",
                status_code=200,
            )
        if not layout or not layout[0]:
            return HTMLResponse(
                content="<h1>Layout empty</h1><p>Configure layout at the main interface.</p>",
                status_code=200,
            )

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
        modules_settings_schema = {}
        show_title = {"id": "show_title", "label": "Show module title", "type": "checkbox", "default": True}
        for m in get_modules():
            mid = m.get("id", "")
            if mid:
                modules_settings_schema[mid] = [show_title] + list(m.get("settings") or [])
        module_css, module_js = get_module_assets(layout, map_overlay_layout=map_overlay_layout)
        module_settings_json = json.dumps(module_settings)
        modules_settings_schema_json = json.dumps(modules_settings_schema)
        map_overlay_modules_json = json.dumps(list(overlay_modules))
        map_overlay_layout_json = json.dumps(map_overlay_layout)
        setup_callsign_json = json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = json.dumps(current_config.get("setup_location") or "")

        main_port = current_config.get("port")
        if main_port is None or not isinstance(main_port, int):
            main_port = 8080

        hostname = request.url.hostname or "127.0.0.1"
        scheme = request.url.scheme or "http"
        main_base_url = f"{scheme}://{hostname}:{main_port}"

        _log.debug("readonly: grid=%sx%s main_port=%s", grid_columns, grid_rows, main_port)
        cache_bust = str(int(time.time() * 1000))
        html_content = render_readonly_page(
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
            main_port=main_port,
            main_base_url=main_base_url,
            cache_bust=cache_bust,
        )
        html_content = html_content.replace("__GLANCERF_MENU_PANEL__", get_menu_html(main_base_url))
        return HTMLResponse(content=html_content)


def run_readonly_server(host: str = "0.0.0.0", port: int = 8081, quiet: bool = False) -> None:
    """Run the read-only FastAPI server (no WebSocket, no interactions)."""
    app = FastAPI(title="GlanceRF (Read-Only)")
    register_readonly_routes(app)

    _web_static = _WEB_DIR / "static"
    if _web_static.is_dir():
        app.mount("/static", StaticFiles(directory=str(_web_static)), name="static")

    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
