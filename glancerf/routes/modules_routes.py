"""
Modules management page routes for GlanceRF
Shows all available modules, their status, descriptions, and per-module settings (expandable)
"""

import html as html_module
import importlib.util
import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config
from glancerf.modules import get_modules, get_module_by_id, get_module_dir
from glancerf.rate_limit import rate_limit_dependency
from glancerf.view_utils import build_merged_cells_from_spans

_MODULES_DIR = Path(__file__).parent.parent / "modules"

# Form field names use double underscore so setting_id can contain underscores: cell_key__setting_id
_CELL_SETTING_SEP = "__"


def _get_module_description(module_id: str) -> str:
    """Get module description from docstring (folder module.py or legacy .py)."""
    module_file = None
    folder = get_module_dir(module_id)
    if folder and (folder / "module.py").is_file():
        module_file = folder / "module.py"
    if module_file is None:
        module_file = _MODULES_DIR / f"{module_id}.py"
    if not module_file.exists():
        return "No description available"
    try:
        spec = importlib.util.spec_from_file_location(
            f"glancerf.modules.{module_id}", module_file
        )
        if spec is None or spec.loader is None:
            return "No description available"
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        if mod.__doc__:
            doc = mod.__doc__.strip()
            lines = doc.split("\n\n")
            if lines:
                desc = lines[0].strip()
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                return desc
        return "No description available"
    except Exception:
        return "No description available"


def _render_setting_input(setting: dict, cell_key: str, current_value: str, setting_id: str) -> str:
    """Render an input field for a module setting. Form name is cell_key + __ + setting_id."""
    setting_type = setting.get("type", "text")
    setting_label = html_module.escape(setting.get("label", ""))
    input_id = f"{cell_key}_{setting_id}".replace("_", "-")
    input_name = f"{cell_key}{_CELL_SETTING_SEP}{setting_id}"

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
    else:
        return f"""
        <div class="setting-field">
            <label for="{input_id}">{setting_label}</label>
            <input type="{setting_type}" id="{input_id}" name="{input_name}"
                   value="{html_module.escape(str(current_value))}" class="setting-input">
        </div>
        """


def register_modules_routes(app: FastAPI, connection_manager=None):
    """Register modules management routes."""

    @app.get("/modules")
    async def modules_page():
        """Modules management page - expandable cards with status, description, and per-module settings."""
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout") or []
        cell_spans = current_config.get("cell_spans") or {}
        module_settings = current_config.get("module_settings") or {}
        merged_cells, primary_cells = build_merged_cells_from_spans(cell_spans)

        enabled_module_ids = set()
        for row in layout:
            for cell_value in row:
                if cell_value:
                    enabled_module_ids.add(cell_value)

        all_modules = get_modules()
        modules_html = ""

        for module in all_modules:
            module_id = module.get("id", "")
            if not module_id:
                continue
            module_name = module.get("name", "Unknown")
            module_color = module.get("color", "#000")
            is_enabled = module_id in enabled_module_ids
            status = "Enabled" if is_enabled else "Disabled"
            status_class = "status-enabled" if is_enabled else "status-disabled"
            description = _get_module_description(module_id)
            settings_schema = module.get("settings") or []

            # Cells (row, col) where this module is used (primary cells only)
            cells_with_module = []
            for row_idx, row in enumerate(layout):
                for col_idx, cell_value in enumerate(row):
                    if cell_value != module_id:
                        continue
                    if (row_idx, col_idx) not in primary_cells:
                        continue
                    cells_with_module.append((row_idx, col_idx))

            has_settings = bool(settings_schema and cells_with_module)
            expandable_class = "module-item-expandable" if has_settings else ""
            body_content = ""
            if has_settings:
                cells_html = ""
                for row_idx, col_idx in cells_with_module:
                    cell_key = f"{row_idx}_{col_idx}"
                    cell_settings = module_settings.get(cell_key, {})
                    fields_html = ""
                    for setting in settings_schema:
                        setting_id = setting.get("id", "")
                        current_value = cell_settings.get(setting_id, setting.get("default", ""))
                        fields_html += _render_setting_input(setting, cell_key, current_value, setting_id)
                    cells_html += f"""
                    <div class="module-settings-cell">
                        <div class="module-settings-cell-title">Cell (Row {row_idx}, Col {col_idx})</div>
                        <div class="module-settings-fields">{fields_html}</div>
                    </div>
                    """
                body_content = f"""
                <div class="module-item-body">
                    <div class="module-settings-cells">{cells_html}</div>
                    <div class="module-settings-actions">
                        <button type="submit" class="btn-save">Save</button>
                    </div>
                </div>
                """

            if has_settings:
                modules_html += f"""
            <div class="module-item {expandable_class}">
                <div class="module-header" role="button" tabindex="0" aria-expanded="false" aria-controls="module-body-{html_module.escape(module_id)}" id="module-header-{html_module.escape(module_id)}">
                    <span class="module-toggle" aria-hidden="true">&gt;</span>
                    <div class="module-color" style="background-color: {module_color};"></div>
                    <div class="module-info">
                        <h3>{html_module.escape(module_name)}</h3>
                        <span class="module-id">ID: {html_module.escape(module_id)}</span>
                    </div>
                    <div class="module-status {status_class}">{status}</div>
                </div>
                <div class="module-description">{html_module.escape(description)}</div>
                <div class="module-item-body-wrap" id="module-body-{html_module.escape(module_id)}" hidden>
                    <form class="module-settings-form" method="post" action="/modules/save-settings" data-module-id="{html_module.escape(module_id)}">
                        {body_content}
                    </form>
                </div>
            </div>
            """
            else:
                modules_html += f"""
            <div class="module-item {expandable_class}">
                <div class="module-header">
                    <div class="module-color" style="background-color: {module_color};"></div>
                    <div class="module-info">
                        <h3>{html_module.escape(module_name)}</h3>
                        <span class="module-id">ID: {html_module.escape(module_id)}</span>
                    </div>
                    <div class="module-status {status_class}">{status}</div>
                </div>
                <div class="module-description">{html_module.escape(description)}</div>
            </div>
            """

        menu_list_no_config = """
                <li><a href="/setup">Setup</a></li>
                <li><a href="/layout">Layout editor</a></li>
                <li><a href="/modules">Modules</a></li>
                <li><a href="/updates">Updates</a></li>
            """

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlanceRF - Modules</title>
    <link rel="stylesheet" href="/static/css/menu.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Courier New', monospace; background-color: #000; color: #fff; padding: 20px; min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ margin-bottom: 30px; color: #fff; font-size: 32px; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; color: #0f0; text-decoration: none; font-size: 14px; }}
        .back-link:hover {{ text-decoration: underline; }}
        .modules-list {{ display: flex; flex-direction: column; gap: 15px; }}
        .module-item {{ background-color: #111; border: 2px solid #333; border-radius: 5px; overflow: hidden; }}
        .module-item .module-header {{ display: flex; align-items: center; gap: 15px; padding: 20px; }}
        .module-item-expandable .module-header {{ cursor: pointer; }}
        .module-item-expandable .module-header:hover {{ background-color: #1a1a1a; }}
        .module-toggle {{ width: 20px; flex-shrink: 0; color: #888; font-size: 14px; transition: transform 0.2s; }}
        .module-item-expandable .module-header[aria-expanded="true"] .module-toggle {{ transform: rotate(90deg); }}
        .module-color {{ width: 40px; height: 40px; border-radius: 5px; border: 1px solid #444; flex-shrink: 0; }}
        .module-info {{ flex: 1; }}
        .module-info h3 {{ margin: 0 0 5px 0; color: #fff; font-size: 18px; }}
        .module-id {{ color: #888; font-size: 12px; }}
        .module-status {{ padding: 8px 16px; border-radius: 5px; font-size: 14px; font-weight: bold; flex-shrink: 0; }}
        .status-enabled {{ background-color: #0f0; color: #000; }}
        .status-disabled {{ background-color: #333; color: #aaa; }}
        .module-description {{ color: #aaa; font-size: 14px; line-height: 1.6; padding: 0 20px 15px 55px; }}
        .module-item-body-wrap {{ padding: 0 20px 20px; border-top: 1px solid #333; }}
        .module-settings-cells {{ display: flex; flex-direction: column; gap: 20px; margin-bottom: 15px; }}
        .module-settings-cell {{ background-color: #0a0a0a; border: 1px solid #333; border-radius: 5px; padding: 15px; }}
        .module-settings-cell-title {{ color: #888; font-size: 12px; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }}
        .module-settings-fields {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
        .setting-field {{ display: flex; flex-direction: column; gap: 5px; }}
        .setting-field label {{ color: #aaa; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .setting-input {{ background-color: #000; border: 1px solid #333; color: #fff; padding: 8px 12px; font-family: inherit; font-size: 14px; border-radius: 3px; }}
        .setting-input:focus {{ outline: none; border-color: #0f0; }}
        .module-settings-actions {{ display: flex; justify-content: flex-end; }}
        .btn-save {{ background-color: #0f0; color: #000; border: none; padding: 10px 24px; font-family: inherit; font-size: 14px; font-weight: bold; border-radius: 5px; cursor: pointer; }}
        .btn-save:hover {{ background-color: #0a0; }}
    </style>
</head>
<body>
    <div id="glancerf-menu" role="dialog" aria-modal="true" aria-label="Menu">
        <div class="glancerf-menu-overlay" id="glancerf-menu-overlay"></div>
        <div class="glancerf-menu-panel">
            <h2>Menu</h2>
            <ul class="glancerf-menu-list">
                {menu_list_no_config}
            </ul>
        </div>
    </div>
    <div class="container">
        <a href="/" class="back-link">← Back to Main</a>
        <h1>Modules</h1>
        <div class="modules-list">
            {modules_html}
        </div>
    </div>
    <script>
        document.addEventListener('keydown', function(event) {{
            var isInputFocused = document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA' || document.activeElement.tagName === 'SELECT' || document.activeElement.isContentEditable);
            if (isInputFocused) return;
            if (event.key === 'm' || event.key === 'M') {{
                event.preventDefault();
                var menu = document.getElementById('glancerf-menu');
                if (menu) menu.classList.toggle('open');
            }}
            if (event.key === 'Escape') {{
                var menu = document.getElementById('glancerf-menu');
                if (menu && menu.classList.contains('open')) {{ menu.classList.remove('open'); event.preventDefault(); }}
            }}
        }});
        var o = document.getElementById('glancerf-menu-overlay');
        if (o) o.addEventListener('click', function() {{ var m = document.getElementById('glancerf-menu'); if (m) m.classList.remove('open'); }});
        document.querySelectorAll('.module-item-expandable .module-header').forEach(function(header) {{
            header.addEventListener('click', function() {{
                var expanded = this.getAttribute('aria-expanded') === 'true';
                var bodyId = this.getAttribute('aria-controls');
                var body = bodyId ? document.getElementById(bodyId) : null;
                this.setAttribute('aria-expanded', expanded ? 'false' : 'true');
                if (body) body.hidden = expanded;
            }});
            header.addEventListener('keydown', function(e) {{
                if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); this.click(); }}
            }});
        }});
    </script>
</body>
</html>
        """

        return HTMLResponse(content=html_content)

    @app.post("/modules/save-settings")
    async def modules_save_settings(request: Request, _: None = Depends(rate_limit_dependency)):
        """Save module settings for the submitted form. Form field names: cell_key__setting_id."""
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        form_data = await request.form()
        merge = {}
        for key, value in form_data.items():
            if _CELL_SETTING_SEP not in key:
                continue
            cell_key, setting_id = key.split(_CELL_SETTING_SEP, 1)
            if cell_key not in merge:
                merge[cell_key] = {}
            merge[cell_key][setting_id] = value

        if not merge:
            return RedirectResponse(url="/modules", status_code=303)

        current = dict(current_config.get("module_settings") or {})
        for cell_key, settings in merge.items():
            current[cell_key] = {**(current.get(cell_key) or {}), **settings}
        current_config.set("module_settings", current)

        if connection_manager:
            try:
                msg = {"type": "config_update", "data": {"reload": True}}
                for conn in list(connection_manager.browser_connections):
                    try:
                        await conn.send_json(msg)
                    except Exception:
                        pass
                if connection_manager.desktop_connection:
                    try:
                        await connection_manager.desktop_connection.send_json(msg)
                    except Exception:
                        connection_manager.desktop_connection = None
                for conn in list(connection_manager.readonly_connections):
                    try:
                        await conn.send_json(msg)
                    except Exception:
                        pass
            except Exception:
                pass

        return RedirectResponse(url="/modules", status_code=303)
