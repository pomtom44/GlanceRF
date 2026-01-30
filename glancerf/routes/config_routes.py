"""
Configuration management page routes for GlanceRF.
Template and static assets: glancerf/web/templates/config/, glancerf/web/static/css/config.css, glancerf/web/static/js/config.js.
"""

import html as html_module
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config
from glancerf.logging_config import get_logger
from glancerf.modules import get_module_by_id
from glancerf.rate_limit import rate_limit_dependency
from glancerf.view_utils import build_merged_cells_from_spans

_log = get_logger("config_routes")

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_CONFIG_TEMPLATE_PATH = _WEB_DIR / "templates" / "config" / "index.html"
_config_template_cache = None


def _get_config_template() -> str:
    """Load config page HTML template from file (cached)."""
    global _config_template_cache
    if _config_template_cache is None:
        _config_template_cache = _CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _config_template_cache


def _render_setting_input(setting: dict, cell_key: str, current_value: str, setting_id: str) -> str:
    """Render an input field for a module setting."""
    setting_type = setting.get("type", "text")
    setting_label = html_module.escape(setting.get("label", ""))
    input_id = f"{cell_key}_{setting_id}"
    input_name = f"{cell_key}_{setting_id}"
    
    if setting_type == "select":
        options = setting.get("options", [])
        options_html = ""
        for opt in options:
            opt_value = html_module.escape(str(opt.get("value", "")))
            opt_label = html_module.escape(str(opt.get("label", opt_value)))
            selected = "selected" if str(opt_value) == str(current_value) else ""
            options_html += f'<option value="{opt_value}" {selected}>{opt_label}</option>'
        
        return f"""
        <div class="setting-field">
            <label for="{input_id}">{setting_label}</label>
            <select id="{input_id}" name="{input_name}" class="setting-input">
                {options_html}
            </select>
        </div>
        """
    else:  # text, number, etc.
        return f"""
        <div class="setting-field">
            <label for="{input_id}">{setting_label}</label>
            <input type="{setting_type}" id="{input_id}" name="{input_name}" 
                   value="{html_module.escape(str(current_value))}" class="setting-input">
        </div>
        """


def register_config_routes(app: FastAPI, connection_manager=None):
    """Register configuration management routes."""

    @app.get("/config")
    async def config_page():
        """Configuration page - edit all module settings in one place."""
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout") or []
        grid_columns = current_config.get("grid_columns")
        grid_rows = current_config.get("grid_rows")
        cell_spans = current_config.get("cell_spans") or {}
        module_settings = current_config.get("module_settings") or {}
        
        if grid_columns is None or grid_rows is None:
            return HTMLResponse(
                content="<h1>Configuration Error</h1><p>Missing required configuration values</p>",
                status_code=500
            )
        
        merged_cells, primary_cells = build_merged_cells_from_spans(cell_spans)
        
        # Build list of all cells with modules and their settings
        config_sections = []
        cell_configs = {}
        
        for row_idx, row in enumerate(layout):
            for col_idx, module_id in enumerate(row):
                if not module_id:
                    continue
                
                # Skip if this cell is merged (not primary)
                if (row_idx, col_idx) not in primary_cells:
                    continue
                
                cell_key = f"{row_idx}_{col_idx}"
                module = get_module_by_id(module_id)
                if not module:
                    continue
                
                module_name = module.get("name", "Unknown")
                module_settings_list = module.get("settings", [])
                
                if module_settings_list:
                    # Get current settings for this cell
                    cell_settings = module_settings.get(cell_key, {})
                    
                    # Build settings HTML for this cell
                    settings_html = ""
                    for setting in module_settings_list:
                        setting_id = setting.get("id", "")
                        current_value = cell_settings.get(setting_id, setting.get("default", ""))
                        settings_html += _render_setting_input(setting, cell_key, current_value, setting_id)
                    
                    if settings_html:
                        config_sections.append({
                            "cell_key": cell_key,
                            "row": row_idx,
                            "col": col_idx,
                            "module_name": module_name,
                            "module_id": module_id,
                            "settings_html": settings_html
                        })
        
        # Build HTML
        sections_html = ""
        for section in config_sections:
            sections_html += f"""
            <div class="config-section">
                <div class="config-section-header">
                    <h3>{html_module.escape(section['module_name'])}</h3>
                    <span class="config-location">Cell: Row {section['row']}, Col {section['col']}</span>
                </div>
                <div class="config-settings">
                    {section['settings_html']}
                </div>
            </div>
            """
        
        if not sections_html:
            sections_html = '<div class="no-configs">No modules with configurable settings are currently enabled.</div>'

        html_content = _get_config_template().format(sections_html=sections_html)
        return HTMLResponse(content=html_content)

    @app.post("/config")
    async def config_submit(request: Request, _: None = Depends(rate_limit_dependency)):
        """Handle configuration form submission."""
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")
        
        try:
            form_data = await request.form()
            
            # Parse form data into module_settings structure
            # Format: {cell_key}_{setting_id} = value
            module_settings = {}
            
            for key, value in form_data.items():
                if '_' in key:
                    parts = key.rsplit('_', 1)
                    if len(parts) == 2:
                        cell_key, setting_id = parts
                        if cell_key not in module_settings:
                            module_settings[cell_key] = {}
                        module_settings[cell_key][setting_id] = value
            
            # Update config
            current_config.set("module_settings", module_settings)
            
            # Broadcast config update via WebSocket to all connected clients
            if connection_manager:
                try:
                    message = {"type": "config_update", "data": {"reload": True}}
                    # Broadcast to all browser connections
                    disconnected = []
                    for conn in connection_manager.browser_connections:
                        try:
                            await conn.send_json(message)
                        except Exception:
                            disconnected.append(conn)
                    for conn in disconnected:
                        if conn in connection_manager.browser_connections:
                            connection_manager.browser_connections.remove(conn)
                    # Broadcast to desktop if connected
                    if connection_manager.desktop_connection:
                        try:
                            await connection_manager.desktop_connection.send_json(message)
                        except Exception:
                            connection_manager.desktop_connection = None
                except Exception as e:
                    _log.debug("WebSocket broadcast failed: %s", e)
            
            return RedirectResponse(url="/", status_code=303)
            
        except Exception as e:
            return HTMLResponse(
                content=f"<h1>Error</h1><p>Failed to save configuration: {e}</p>",
                status_code=500
            )
