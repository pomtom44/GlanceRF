"""
Modules management page routes for GlanceRF
Shows installed modules and whether each is active (used in the current layout).
"""

import html as html_module
import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config
from glancerf.modules import clear_module_cache, get_modules, get_module_dir
from glancerf.logging_config import get_logger

_log = get_logger("modules_routes")
_MODULES_DIR = Path(__file__).parent.parent / "modules"


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


def register_modules_routes(app: FastAPI, connection_manager=None):
    """Register modules management routes."""

    @app.get("/modules")
    async def modules_page():
        """Modules page - lists installed modules and whether each is active in the layout."""
        _log.debug("GET /modules")
        clear_module_cache()
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            _log.debug("modules: config not found, redirect to setup")
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout") or []
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
            module_color = module.get("color", "#111")
            is_enabled = module_id in enabled_module_ids
            status = "Enabled" if is_enabled else "Disabled"
            status_class = "status-enabled" if is_enabled else "status-disabled"
            description = _get_module_description(module_id)
            modules_html += f"""
            <div class="module-item">
                <div class="module-header">
                    <div class="module-color" style="background-color: {html_module.escape(module_color)};"></div>
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
        .module-color {{ width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }}
        .module-info {{ flex: 1; }}
        .module-info h3 {{ margin: 0 0 5px 0; color: #fff; font-size: 18px; }}
        .module-id {{ color: #888; font-size: 12px; }}
        .module-status {{ padding: 8px 16px; border-radius: 5px; font-size: 14px; font-weight: bold; flex-shrink: 0; }}
        .status-enabled {{ background-color: #0f0; color: #000; }}
        .status-disabled {{ background-color: #333; color: #aaa; }}
        .module-description {{ color: #aaa; font-size: 14px; line-height: 1.6; padding: 0 20px 15px 20px; }}
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
    </script>
</body>
</html>
        """

        return HTMLResponse(content=html_content)
