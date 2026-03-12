"""
Setup (first-run) routes for GlanceRF.
"""

import html as html_module
import json as _json
import re
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from typing import Optional

from glancerf.config import get_config, get_logger, resize_layout_to_grid
from glancerf.gpio import is_gpio_available
from glancerf.services import start_aprs_cache
from glancerf.web.menu_html import get_menu_html
from glancerf.utils import get_aspect_ratio_list, rate_limit_dependency
from glancerf.web import ConnectionManager

_log = get_logger("setup_routes")

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_SETUP_TEMPLATE_PATH = _WEB_DIR / "templates" / "setup" / "index.html"
_setup_template_cache = None


def _get_setup_template() -> str:
    """Load setup page HTML template from file (cached)."""
    global _setup_template_cache
    if _setup_template_cache is None and _SETUP_TEMPLATE_PATH.is_file():
        _setup_template_cache = _SETUP_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _setup_template_cache or ""


def register_setup_routes(app: FastAPI, connection_manager: Optional[ConnectionManager] = None):
    """Register setup page and form submission routes."""

    @app.get("/setup")
    async def setup_page():
        """First-run setup page."""
        _log.debug("GET /setup")
        available_ratios = get_aspect_ratio_list()
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")
        current_ratio = current_config.get("aspect_ratio") or "16:9"
        current_orientation = current_config.get("orientation") or "landscape"
        current_columns = current_config.get("grid_columns")
        current_rows = current_config.get("grid_rows")
        max_grid_scale = current_config.get("max_grid_scale")
        if max_grid_scale is None:
            max_grid_scale = 10
        try:
            max_grid_scale = max(1, min(20, int(max_grid_scale)))
        except (TypeError, ValueError):
            max_grid_scale = 10
        current_callsign = current_config.get("setup_callsign") or ""
        current_ssid = current_config.get("setup_ssid") or "01"
        current_location = current_config.get("setup_location") or ""
        current_aprs_cache_max_size_mb = current_config.get("aprs_cache_max_size_mb")
        if current_aprs_cache_max_size_mb is None or current_aprs_cache_max_size_mb == "":
            old_size = current_config.get("aprs_cache_max_size")
            if old_size is not None and old_size != "":
                try:
                    records = int(old_size)
                    current_aprs_cache_max_size_mb = max(100, min(10000, records * 150 // (1024 * 1024)))
                except (TypeError, ValueError):
                    current_aprs_cache_max_size_mb = 500
            else:
                current_aprs_cache_max_size_mb = 500
        try:
            current_aprs_cache_max_size_mb = max(100.0, min(10000.0, float(current_aprs_cache_max_size_mb)))
        except (TypeError, ValueError):
            current_aprs_cache_max_size_mb = 500
        current_aprs_cache_max_age_hours = current_config.get("aprs_cache_max_age_hours") or 168
        try:
            current_aprs_cache_max_age_hours = max(1, min(8760, float(current_aprs_cache_max_age_hours)))
        except (TypeError, ValueError):
            current_aprs_cache_max_age_hours = 168
        current_update_mode = current_config.get("update_mode") or "auto"
        current_update_check_time = current_config.get("update_check_time") or "03:00"
        current_telemetry_enabled = current_config.get("telemetry_enabled")
        if current_telemetry_enabled is None:
            current_telemetry_enabled = True
        current_callsign_esc = html_module.escape(current_callsign)
        current_ssid_esc = html_module.escape(current_ssid)
        current_location_esc = html_module.escape(current_location)

        if current_columns is not None:
            current_columns = max(1, min(max_grid_scale, int(current_columns)))
        if current_rows is not None:
            current_rows = max(1, min(max_grid_scale, int(current_rows)))
        # Form display only (not persisted until user submits)
        display_columns = current_columns if current_columns is not None else 3
        display_rows = current_rows if current_rows is not None else 3

        ratio_options = ""
        for ratio in available_ratios:
            selected = "selected" if ratio == current_ratio else ""
            ratio_options += f'<option value="{ratio}" {selected}>{ratio}</option>'

        orientation_landscape_selected = " selected" if current_orientation == "landscape" else ""
        orientation_portrait_selected = " selected" if current_orientation == "portrait" else ""
        update_mode_none_selected = " selected" if current_update_mode == "none" else ""
        update_mode_notify_selected = " selected" if current_update_mode == "notify" else ""
        update_mode_auto_selected = " selected" if current_update_mode == "auto" else ""
        telemetry_enabled_selected = " selected" if current_telemetry_enabled else ""
        telemetry_disabled_selected = " selected" if not current_telemetry_enabled else ""
        setup_config_json = _json.dumps({
            "current_ratio": current_ratio,
            "current_orientation": current_orientation,
        })
        setup_gpio_section = (
            '<p style="color:#ccc; font-size:14px; line-height:1.6; margin-bottom:16px;">'
            '<a href="/gpio" style="color:#0f0;">Configure GPIO</a> to assign module inputs and outputs to pins.'
            '</p>'
        ) if is_gpio_available() else (
            '<p style="color:#888; font-size:14px; line-height:1.6; margin-bottom:16px;">'
            'GPIO not supported and disabled on this system.</p>'
        )

        template = _get_setup_template()
        if not template:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Setup template not found: {_SETUP_TEMPLATE_PATH}</p>",
                status_code=500,
            )
        html_content = template.format(
            ratio_options=ratio_options,
            orientation_landscape_selected=orientation_landscape_selected,
            orientation_portrait_selected=orientation_portrait_selected,
            current_columns=display_columns,
            current_rows=display_rows,
            max_grid_scale=max_grid_scale,
            current_callsign_esc=current_callsign_esc,
            current_ssid_esc=current_ssid_esc,
            current_location_esc=current_location_esc,
            current_aprs_cache_max_size_mb=int(current_aprs_cache_max_size_mb),
            current_aprs_cache_max_age_hours=int(current_aprs_cache_max_age_hours),
            update_mode_none_selected=update_mode_none_selected,
            update_mode_notify_selected=update_mode_notify_selected,
            update_mode_auto_selected=update_mode_auto_selected,
            current_update_check_time=current_update_check_time,
            telemetry_enabled_selected=telemetry_enabled_selected,
            telemetry_disabled_selected=telemetry_disabled_selected,
            current_ratio=current_ratio,
            current_orientation=current_orientation,
            setup_config_json=setup_config_json,
            setup_gpio_section=setup_gpio_section,
        )
        cache_bust = str(int(time.time() * 1000))
        html_content = html_content.replace("__CACHE_BUST__", cache_bust)
        html_content = html_content.replace("__GLANCERF_MENU_PANEL__", get_menu_html())
        return HTMLResponse(content=html_content)

    @app.post("/setup")
    async def setup_submit(
        _: None = Depends(rate_limit_dependency),
        aspect_ratio: str = Form(...),
        orientation: str = Form("landscape"),
        grid_columns: int = Form(...),
        grid_rows: int = Form(...),
        setup_callsign: str = Form(""),
        setup_ssid: str = Form("01"),
        setup_location: str = Form(""),
        aprs_cache_max_size_mb: float = Form(500),
        aprs_cache_max_age_hours: float = Form(168),
        update_mode: str = Form("auto"),
        update_check_time: str = Form("03:00"),
        telemetry_enabled: str = Form("1"),
    ):
        """Handle setup form submission."""
        _log.debug("POST /setup")
        if aspect_ratio not in get_aspect_ratio_list():
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Invalid aspect ratio: {aspect_ratio}</p>",
                status_code=400,
            )
        if orientation not in ("landscape", "portrait"):
            return HTMLResponse(
                content="<h1>Error</h1><p>Invalid orientation.</p>",
                status_code=400,
            )
        config_instance = get_config()
        max_grid_scale = config_instance.get("max_grid_scale") or 10
        try:
            max_grid_scale = max(1, min(20, int(max_grid_scale)))
        except (TypeError, ValueError):
            max_grid_scale = 10
        if grid_columns < 1 or grid_columns > max_grid_scale:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Grid columns must be between 1 and {max_grid_scale}</p>",
                status_code=400,
            )
        if grid_rows < 1 or grid_rows > max_grid_scale:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Grid rows must be between 1 and {max_grid_scale}</p>",
                status_code=400,
            )
        if update_mode not in ("none", "notify", "auto"):
            update_mode = "none"
        if update_check_time and not re.match(r"^([01]?\d|2[0-3]):[0-5]\d$", update_check_time.strip()):
            update_check_time = "03:00"

        is_first_run = config_instance.get("first_run")

        config_instance.set("aspect_ratio", aspect_ratio)
        config_instance.set("orientation", orientation)
        config_instance.set("grid_columns", grid_columns)
        config_instance.set("grid_rows", grid_rows)
        current_layout = config_instance.get("layout") or []
        rows_ok = len(current_layout) == grid_rows
        cols_ok = (current_layout and len(current_layout[0]) == grid_columns) if current_layout else False
        if not (rows_ok and cols_ok):
            config_instance.set("layout", resize_layout_to_grid(current_layout, grid_columns, grid_rows))
        config_instance.set("setup_callsign", (setup_callsign or "").strip())
        ssid = (setup_ssid or "01").strip()
        if not ssid:
            ssid = "01"
        config_instance.set("setup_ssid", ssid)
        config_instance.set("setup_location", (setup_location or "").strip())
        config_instance.set("aprs_passcode", None)  # Always auto-compute from callsign
        try:
            aprs_mb = max(100.0, min(10000.0, float(aprs_cache_max_size_mb or 500)))
            config_instance.set("aprs_cache_max_size_mb", int(aprs_mb))
        except (TypeError, ValueError):
            config_instance.set("aprs_cache_max_size_mb", 500)
        try:
            aprs_age = max(1.0, min(8760.0, float(aprs_cache_max_age_hours or 168)))
            config_instance.set("aprs_cache_max_age_hours", aprs_age)
        except (TypeError, ValueError):
            config_instance.set("aprs_cache_max_age_hours", 168)
        config_instance.set("update_mode", update_mode)
        config_instance.set("update_check_time", (update_check_time or "03:00").strip())
        telemetry_enabled_bool = telemetry_enabled == "1" if telemetry_enabled else True
        config_instance.set("telemetry_enabled", telemetry_enabled_bool)

        if is_first_run:
            config_instance.set("first_run", False)

        # Start APRS cache when setup is saved (covers first launch when callsign was just set)
        start_aprs_cache()

        redirect_url = "/layout" if is_first_run else "/"

        if connection_manager:
            try:
                await connection_manager.broadcast_config_update({
                    "aspect_ratio": aspect_ratio,
                    "orientation": orientation,
                    "grid_columns": grid_columns,
                    "grid_rows": grid_rows,
                    "reload": True,
                })
            except Exception as e:
                _log.debug("WebSocket broadcast_config_update failed: %s", e)

        _log.debug("setup: saved, redirecting to %s", redirect_url)
        return RedirectResponse(url=redirect_url, status_code=303)
