"""
Setup (first-run) routes for GlanceRF.
Template and static assets: glancerf/web/templates/setup/, glancerf/web/static/css/setup.css, glancerf/web/static/js/setup.js.
"""

import html as html_module
import json as _json
import re
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config, resize_layout_to_grid
from glancerf.logging_config import get_logger
from glancerf.rate_limit import rate_limit_dependency

_log = get_logger("setup_routes")
from glancerf.aspect_ratio import get_aspect_ratio_list
from glancerf.websocket_manager import ConnectionManager

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_SETUP_TEMPLATE_PATH = _WEB_DIR / "templates" / "setup" / "index.html"
_setup_template_cache = None


def _get_setup_template() -> str:
    """Load setup page HTML template from file (cached)."""
    global _setup_template_cache
    if _setup_template_cache is None:
        _setup_template_cache = _SETUP_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _setup_template_cache


def register_setup_routes(app: FastAPI, connection_manager: ConnectionManager):
    """Register setup page and form submission routes."""

    @app.get("/setup")
    async def setup_page():
        """First-run setup page"""
        # Get available options
        available_ratios = get_aspect_ratio_list()
    
        # Get current values from config (config file must exist, no defaults)
        current_config = get_config()
        current_ratio = current_config.get("aspect_ratio") or "16:9"
        current_orientation = current_config.get("orientation") or "landscape"
        current_columns = current_config.get("grid_columns")
        current_rows = current_config.get("grid_rows")
        max_grid_scale = current_config.get("max_grid_scale")
        if max_grid_scale is None:
            return HTMLResponse(
                content="<h1>Config Error</h1><p>max_grid_scale must be set in glancerf_config.json</p>",
                status_code=500
            )
        try:
            max_grid_scale = max(1, min(20, int(max_grid_scale)))
        except (TypeError, ValueError):
            return HTMLResponse(
                content="<h1>Config Error</h1><p>max_grid_scale must be an integer between 1 and 20</p>",
                status_code=500
            )
        current_callsign = current_config.get("setup_callsign") or ""
        current_location = current_config.get("setup_location") or ""
        current_update_mode = current_config.get("update_mode") or "auto"
        current_update_check_time = current_config.get("update_check_time") or "03:00"
        current_telemetry_enabled = current_config.get("telemetry_enabled")
        if current_telemetry_enabled is None:
            current_telemetry_enabled = True  # Default to enabled (opt-out)
        current_callsign_esc = html_module.escape(current_callsign)
        current_location_esc = html_module.escape(current_location)

        # Fallback to 3x3 if not configured; clamp to max_grid_scale
        if current_columns is None:
            current_columns = 3
            current_config.set("grid_columns", 3)
        else:
            current_columns = max(1, min(max_grid_scale, int(current_columns)))
        if current_rows is None:
            current_rows = 3
            current_config.set("grid_rows", 3)
        else:
            current_rows = max(1, min(max_grid_scale, int(current_rows)))
    
        # Build ratio options HTML
        ratio_options = ""
        for ratio in available_ratios:
            selected = "selected" if ratio == current_ratio else ""
            ratio_options += f'<option value="{ratio}" {selected}>{ratio}</option>'
    
        orientation_landscape_selected = ' selected' if current_orientation == 'landscape' else ''
        orientation_portrait_selected = ' selected' if current_orientation == 'portrait' else ''
        update_mode_none_selected = ' selected' if current_update_mode == 'none' else ''
        update_mode_notify_selected = ' selected' if current_update_mode == 'notify' else ''
        update_mode_auto_selected = ' selected' if current_update_mode == 'auto' else ''
        telemetry_enabled_selected = ' selected' if current_telemetry_enabled else ''
        telemetry_disabled_selected = ' selected' if not current_telemetry_enabled else ''
        setup_config_json = _json.dumps({"current_ratio": current_ratio, "current_orientation": current_orientation})
        html_content = _get_setup_template().format(
            ratio_options=ratio_options,
            orientation_landscape_selected=orientation_landscape_selected,
            orientation_portrait_selected=orientation_portrait_selected,
            current_columns=current_columns,
            current_rows=current_rows,
            max_grid_scale=max_grid_scale,
            current_callsign_esc=current_callsign_esc,
            current_location_esc=current_location_esc,
            update_mode_none_selected=update_mode_none_selected,
            update_mode_notify_selected=update_mode_notify_selected,
            update_mode_auto_selected=update_mode_auto_selected,
            current_update_check_time=current_update_check_time,
            telemetry_enabled_selected=telemetry_enabled_selected,
            telemetry_disabled_selected=telemetry_disabled_selected,
            current_ratio=current_ratio,
            current_orientation=current_orientation,
            setup_config_json=setup_config_json,
        )
        return HTMLResponse(content=html_content)


    @app.post("/setup")
    async def setup_submit(
        request: Request,
        _: None = Depends(rate_limit_dependency),
        aspect_ratio: str = Form(...),
        orientation: str = Form("landscape"),
        grid_columns: int = Form(...),
        grid_rows: int = Form(...),
        setup_callsign: str = Form(""),
        setup_location: str = Form(""),
        update_mode: str = Form("auto"),
        update_check_time: str = Form("03:00"),
        telemetry_enabled: str = Form("1"),
    ):
        """Handle setup form submission"""
        if aspect_ratio not in get_aspect_ratio_list():
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Invalid aspect ratio: {aspect_ratio}</p>",
                status_code=400
            )
        if orientation not in ("landscape", "portrait"):
            return HTMLResponse(
                content="<h1>Error</h1><p>Invalid orientation.</p>",
                status_code=400
            )
        config_instance = get_config()
        max_grid_scale = config_instance.get("max_grid_scale")
        if max_grid_scale is None:
            return HTMLResponse(
                content="<h1>Config Error</h1><p>max_grid_scale must be set in glancerf_config.json</p>",
                status_code=500
            )
        try:
            max_grid_scale = max(1, min(20, int(max_grid_scale)))
        except (TypeError, ValueError):
            return HTMLResponse(
                content="<h1>Config Error</h1><p>max_grid_scale must be an integer between 1 and 20</p>",
                status_code=500
            )
        if grid_columns < 1 or grid_columns > max_grid_scale:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Grid columns must be between 1 and {max_grid_scale}</p>",
                status_code=400
            )
        if grid_rows < 1 or grid_rows > max_grid_scale:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Grid rows must be between 1 and {max_grid_scale}</p>",
                status_code=400
            )
        if update_mode not in ("none", "notify", "auto"):
            update_mode = "none"
        if update_check_time and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", update_check_time.strip()):
            update_check_time = "03:00"
    
        # Update existing config file (config_instance already set above for max_grid_scale)
        # Check if this is actually a first run
        is_first_run = config_instance.get("first_run")
    
        # Store old values to detect changes
        old_aspect_ratio = config_instance.get("aspect_ratio")
    
        config_instance.set("aspect_ratio", aspect_ratio)
        config_instance.set("orientation", orientation)
        config_instance.set("grid_columns", grid_columns)
        config_instance.set("grid_rows", grid_rows)
        # Ensure layout dimensions match grid (fix mismatch after first-run setup or grid size change)
        current_layout = config_instance.get("layout") or []
        rows_ok = len(current_layout) == grid_rows
        cols_ok = (current_layout and len(current_layout[0]) == grid_columns) if current_layout else False
        if not (rows_ok and cols_ok):
            config_instance.set("layout", resize_layout_to_grid(current_layout, grid_columns, grid_rows))
        config_instance.set("setup_callsign", (setup_callsign or "").strip())
        config_instance.set("setup_location", (setup_location or "").strip())
        config_instance.set("update_mode", update_mode)
        config_instance.set("update_check_time", (update_check_time or "03:00").strip())
        
        # Handle telemetry_enabled (convert "1"/"0" string to boolean)
        telemetry_enabled_bool = telemetry_enabled == "1" if telemetry_enabled else True
        config_instance.set("telemetry_enabled", telemetry_enabled_bool)
    
        # Only set first_run to False if it was True (don't change it if user is just updating settings)
        if is_first_run:
            config_instance.set("first_run", False)
    
        # Broadcast config_update to browser and readonly clients (not desktop)
        # Desktop will reload from the redirect, so we don't need to notify it
        try:
            msg = {
                "type": "config_update",
                "data": {
                    "aspect_ratio": aspect_ratio,
                    "orientation": orientation,
                    "grid_columns": grid_columns,
                    "grid_rows": grid_rows,
                    "reload": True
                }
            }
            for connection in connection_manager.browser_connections:
                try:
                    await connection.send_json(msg)
                except Exception as e:
                    _log.debug("WebSocket send failed: %s", e)
            for connection in list(connection_manager.readonly_connections):
                try:
                    await connection.send_json(msg)
                except Exception as e:
                    _log.debug("WebSocket send failed (readonly): %s", e)
        except Exception as e:
            _log.debug("WebSocket broadcast failed: %s", e)
    
        # After setup, always go to layout page so user can assign modules to cells
        return RedirectResponse(url="/layout", status_code=303)

