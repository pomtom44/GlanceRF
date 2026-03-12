"""
Pages for layout, modules, updates.
"""

import html as html_module
import json as _json
import time
from pathlib import Path
from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from glancerf.config import get_config, get_logger
from glancerf.modules import get_module_by_id, get_module_dir, get_modules
from glancerf.utils import rate_limit_dependency
from glancerf.web import ConnectionManager
from glancerf.web.menu_html import get_menu_html

_log = get_logger("pages")

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_UPDATES_TEMPLATE_PATH = _WEB_DIR / "templates" / "updates" / "index.html"

_updates_template_cache = None


def register_pages(app, connection_manager: Optional[ConnectionManager] = None):
    """Register routes for modules, updates, map-modules. Layout is handled by layout_routes."""

    @app.get("/map-modules")
    async def map_modules_page():
        """Map only modules page - 1xN grid, same design as layout editor."""
        _log.debug("GET /map-modules")
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        modules_list = current_config.get("map_overlay_layout") or []
        if not isinstance(modules_list, list):
            modules_list = []
        modules_list = [m for m in modules_list if isinstance(m, str) and m.strip()]

        all_modules = get_modules()
        module_options = [
            ("", "-- Add module --"),
        ] + [(m["id"], m.get("name", m["id"])) for m in all_modules if m.get("id")]

        cache_bust = str(int(time.time() * 1000))
        raw_module_settings = current_config.get("module_settings") or {}
        layout = current_config.get("layout") or []
        modules_settings_schema = {}
        show_title_setting = {"id": "show_title", "label": "Show module title", "type": "checkbox", "default": True}
        for m in all_modules:
            mid = m.get("id", "")
            if not mid:
                continue
            existing = list(m.get("settings") or [])
            modules_settings_schema[mid] = [show_title_setting] + existing

        from glancerf.utils.module_conflicts import detect_module_conflicts
        conflicts = detect_module_conflicts(layout, modules_list, raw_module_settings, modules_settings_schema)
        for c in conflicts:
            mod = get_module_by_id(c["module_id"])
            c["module_name"] = (mod or {}).get("name", c["module_id"])
        conflict_data_json = _json.dumps(conflicts)
        module_settings_by_cell = {}
        for i, mod_id in enumerate(modules_list):
            cell_key = f"map_overlay_{i}"
            if cell_key in raw_module_settings and isinstance(raw_module_settings[cell_key], dict):
                module_settings_by_cell[cell_key] = raw_module_settings[cell_key]

        module_settings_scripts = []
        for m in all_modules:
            mid = m.get("id", "")
            if not mid:
                continue
            folder = get_module_dir(mid)
            if folder and (folder / "layout_settings.js").is_file():
                module_settings_scripts.append(mid)
        module_settings_scripts_html = "".join(
            f'<script src="/module/{mid}/layout_settings.js?v={cache_bust}"></script>'
            for mid in module_settings_scripts
        )

        rows = modules_list + [""]
        grid_cells = ""
        for i, mod_id in enumerate(rows):
            module = get_module_by_id(mod_id) if mod_id else None
            cell_bg = (module or {}).get("color", "#111")
            opts = "".join(
                f'<option value="{html_module.escape(mid)}"{" selected" if mid == mod_id else ""}>'
                f"{html_module.escape(name)}</option>"
                for mid, name in module_options
            )
            remove_btn = (
                f'<button type="button" class="map-module-remove" data-index="{i}" title="Remove">×</button>'
                if mod_id else ""
            )
            grid_cells += f'''
                <div class="map-module-cell grid-cell" data-index="{i}" style="background-color: {cell_bg};">
                    <select class="cell-widget-select map-module-select" data-index="{i}">
                        {opts}
                    </select>
                    <div class="cell-module-settings"></div>
                    {remove_btn}
                </div>
            '''

        menu_panel = get_menu_html()
        modules_json = _json.dumps(modules_list)
        module_settings_by_cell_json = _json.dumps(module_settings_by_cell)
        modules_settings_schema_json = _json.dumps(modules_settings_schema)
        setup_callsign_json = _json.dumps(current_config.get("setup_callsign") or "")
        setup_location_json = _json.dumps(current_config.get("setup_location") or "")

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlanceRF - Map only modules</title>
    <link rel="icon" href="/logo.png" type="image/png">
    <link rel="stylesheet" href="/static/css/pages.css">
    <link rel="stylesheet" href="/static/css/menu.css?v={cache_bust}">
    <link rel="stylesheet" href="/static/css/layout.css?v={cache_bust}">
    <link rel="stylesheet" href="/static/css/updates.css?v={cache_bust}">
    <style>
        body.map-modules-page {{ padding: 20px; overflow: auto; }}
        .map-modules-grid {{ display: grid; grid-template-columns: 1fr; grid-auto-rows: minmax(200px, 33vh); gap: 15px; width: 100%; margin-bottom: 24px; }}
        .map-module-cell {{ position: relative; display: flex; flex-direction: column; align-items: stretch; justify-content: flex-start; background-color: #1a1a1a; border: 2px solid #333; border-radius: 6px; overflow: hidden; min-height: 200px; }}
        .map-module-cell .cell-widget-select {{ margin-top: 8px; align-self: center; }}
        .map-module-remove {{ position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; background: #333; color: #f00; border: 1px solid #555; border-radius: 4px; cursor: pointer; font-size: 18px; line-height: 1; padding: 0; display: flex; align-items: center; justify-content: center; }}
        .map-module-remove:hover {{ background: #444; }}
    </style>
</head>
<body class="map-modules-page">
    <div id="glancerf-menu" role="dialog" aria-modal="true" aria-label="Menu">
        <div class="glancerf-menu-overlay" id="glancerf-menu-overlay"></div>
        <div class="glancerf-menu-panel">
{menu_panel}
        </div>
    </div>
    <div class="glancerf-page-container">
        <a href="/" class="glancerf-page-back-link">← Back to Main</a>
        <h1>Map only modules</h1>
        <div id="conflict-resolution-container"></div>
        <div class="map-modules-grid" id="map-modules-grid">
            {grid_cells}
        </div>
        <button type="button" class="btn btn-primary" id="map-modules-save">Save & back to dashboard</button>
    </div>
    <script>
        window.MAP_OVERLAY_MODULES = {modules_json};
        window.MAP_MODULE_OPTIONS = {_json.dumps([{"id": m["id"], "name": m.get("name", m["id"]), "color": m.get("color", "#111")} for m in all_modules if m.get("id")])};
        window.MAP_MODULES_CONFIG = {{
            "module_settings_by_cell": {module_settings_by_cell_json},
            "modules_settings_schema": {modules_settings_schema_json},
            "setup_callsign": {setup_callsign_json},
            "setup_location": {setup_location_json},
            "conflicts": {conflict_data_json}
        }};
    </script>
    <script src="/static/js/menu.js?v={cache_bust}"></script>
    <script src="/static/js/conflict-resolution.js?v={cache_bust}"></script>
    {module_settings_scripts_html}
    <script src="/static/js/map-modules.js?v={cache_bust}"></script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)

    @app.post("/api/map-modules")
    async def map_modules_save(request: Request, _: None = Depends(rate_limit_dependency)):
        """Save map overlay layout and module settings."""
        _log.debug("POST /api/map-modules")
        try:
            data = await request.json()
            modules = data.get("modules")
            if modules is None:
                return JSONResponse({"error": "modules missing"}, status_code=400)
            if not isinstance(modules, list):
                return JSONResponse({"error": "modules must be a list"}, status_code=400)
            modules = [str(m).strip() for m in modules if m and str(m).strip()]
            valid_ids = set(m["id"] for m in get_modules() if m.get("id"))
            for mid in modules:
                if mid not in valid_ids:
                    return JSONResponse({"error": f"Unknown module: {mid!r}"}, status_code=400)
            config = get_config()
            config.set("map_overlay_layout", modules)

            module_settings = data.get("module_settings")
            if module_settings is not None and isinstance(module_settings, dict):
                current = dict(config.get("module_settings") or {})
                for cell_key, settings in module_settings.items():
                    if isinstance(settings, dict) and cell_key.startswith("map_overlay_"):
                        current[cell_key] = {**(current.get(cell_key) or {}), **settings}
                for key in list(current):
                    if key.startswith("map_overlay_"):
                        try:
                            idx = int(key.split("_")[-1])
                            if idx >= len(modules):
                                del current[key]
                        except (ValueError, TypeError):
                            pass
                config.set("module_settings", current)

            if connection_manager:
                try:
                    await connection_manager.broadcast_config_update({"reload": True})
                except Exception as e:
                    _log.debug("broadcast_config_update failed: %s", e)
            return JSONResponse({"success": True})
        except Exception as e:
            _log.exception("map-modules save failed")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/modules")
    async def modules_page():
        """Modules page - lists installed modules and whether each is active in the layout."""
        _log.debug("GET /modules")
        try:
            from glancerf.modules import get_modules
        except ImportError:
            get_modules = lambda: []
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout") or []
        map_overlay_layout = current_config.get("map_overlay_layout") or []
        if not isinstance(map_overlay_layout, list):
            map_overlay_layout = []
        map_overlay_ids = set(m for m in map_overlay_layout if m and isinstance(m, str))
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
            module_name = html_module.escape(module.get("name", "Unknown"))
            is_enabled = module_id in enabled_module_ids
            is_map_only = module_id in map_overlay_ids and not is_enabled
            if is_enabled:
                status, status_class = "Enabled", "status-enabled"
            elif is_map_only:
                status, status_class = "Map Only", "status-map-only"
            else:
                status, status_class = "Disabled", "status-disabled"
            description = html_module.escape(module.get("description", "No description available"))
            modules_html += f"""
            <div class="module-item">
                <div class="module-header">
                    <div class="module-info">
                        <h3>{module_name}</h3>
                    </div>
                    <div class="module-status {status_class}">{status}</div>
                </div>
                <div class="module-description">{description}</div>
            </div>
            """

        if not modules_html:
            modules_html = '<p class="modules-empty">No modules installed yet. Add modules to glancerf/modules/ to see them here.</p>'

        menu_panel = get_menu_html()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlanceRF - Modules</title>
    <link rel="icon" href="/logo.png" type="image/png">
    <link rel="stylesheet" href="/static/css/pages.css">
    <link rel="stylesheet" href="/static/css/menu.css">
    <style>
        .modules-list {{ display: flex; flex-direction: column; gap: 15px; }}
        .module-item {{ background-color: #1a1a1a; border: 2px solid #333; border-radius: 6px; overflow: hidden; }}
        .module-item .module-header {{ display: flex; align-items: center; gap: 15px; padding: 20px; }}
        .module-info {{ flex: 1; }}
        .module-info h3 {{ margin: 0; color: #fff; font-size: 18px; }}
        .module-status {{ padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: bold; flex-shrink: 0; }}
        .status-enabled {{ background-color: #0f0; color: #000; }}
        .status-disabled {{ background-color: #333; color: #888; }}
        .status-map-only {{ background-color: #0af; color: #000; }}
        .module-description {{ color: #aaa; font-size: 14px; line-height: 1.6; padding: 0 20px 15px 20px; }}
        .modules-empty {{ color: #aaa; font-size: 14px; padding: 20px; }}
    </style>
</head>
<body>
    <div id="glancerf-menu" role="dialog" aria-modal="true" aria-label="Menu">
        <div class="glancerf-menu-overlay" id="glancerf-menu-overlay"></div>
        <div class="glancerf-menu-panel">
{menu_panel}
        </div>
    </div>
    <div class="glancerf-page-container">
        <a href="/" class="glancerf-page-back-link">← Back to Main</a>
        <h1>Modules</h1>
        <div class="modules-list">
            {modules_html}
        </div>
    </div>
    <script src="/static/js/menu.js"></script>
</body>
</html>
        """
        return HTMLResponse(content=html_content)

    @app.get("/updates")
    async def updates_page():
        """Updates page: check for updates, show current/latest version and release notes, trigger update."""
        global _updates_template_cache
        if _updates_template_cache is None and _UPDATES_TEMPLATE_PATH.is_file():
            _updates_template_cache = _UPDATES_TEMPLATE_PATH.read_text(encoding="utf-8")
        if _updates_template_cache is None:
            return HTMLResponse(content="<h1>Updates</h1><p>Template not found.</p>", status_code=500)
        content = _updates_template_cache.replace("__GLANCERF_MENU_PANEL__", get_menu_html())
        return HTMLResponse(content=content)
