"""
Modules management page routes for GlanceRF
Shows all available modules, their status, and descriptions
"""

import html as html_module
import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from glancerf.config import get_config
from glancerf.modules import get_modules, get_module_by_id, get_module_dir

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


def register_modules_routes(app: FastAPI):
    """Register modules management routes."""

    @app.get("/modules")
    async def modules_page():
        """Modules management page - shows all modules with status and descriptions."""
        try:
            current_config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")

        layout = current_config.get("layout") or []
        
        # Get all enabled module IDs (modules that appear in layout)
        enabled_module_ids = set()
        for row in layout:
            for cell_value in row:
                if cell_value:
                    enabled_module_ids.add(cell_value)
        
        # Get all modules
        all_modules = get_modules()
        
        # Build modules list HTML
        modules_html = ""
        for module in all_modules:
            module_id = module.get("id", "")
            module_name = module.get("name", "Unknown")
            module_color = module.get("color", "#000")
            is_enabled = module_id in enabled_module_ids
            status = "Enabled" if is_enabled else "Disabled"
            status_class = "status-enabled" if is_enabled else "status-disabled"
            description = _get_module_description(module_id)
            
            modules_html += f"""
            <div class="module-item">
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
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlanceRF - Modules</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background-color: #000;
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            margin-bottom: 30px;
            color: #fff;
            font-size: 32px;
        }}
        
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #0f0;
            text-decoration: none;
            font-size: 14px;
        }}
        
        .back-link:hover {{
            text-decoration: underline;
        }}
        
        .modules-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .module-item {{
            background-color: #111;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 20px;
        }}
        
        .module-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .module-color {{
            width: 40px;
            height: 40px;
            border-radius: 5px;
            border: 1px solid #444;
            flex-shrink: 0;
        }}
        
        .module-info {{
            flex: 1;
        }}
        
        .module-info h3 {{
            margin: 0 0 5px 0;
            color: #fff;
            font-size: 18px;
        }}
        
        .module-id {{
            color: #888;
            font-size: 12px;
        }}
        
        .module-status {{
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
            flex-shrink: 0;
        }}
        
        .status-enabled {{
            background-color: #0f0;
            color: #000;
        }}
        
        .status-disabled {{
            background-color: #333;
            color: #aaa;
        }}
        
        .module-description {{
            color: #aaa;
            font-size: 14px;
            line-height: 1.6;
            padding-left: 55px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Main</a>
        <h1>Modules</h1>
        <div class="modules-list">
            {modules_html}
        </div>
    </div>
    
    <script>
        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {{
            const isInputFocused = document.activeElement && (
                document.activeElement.tagName === 'INPUT' ||
                document.activeElement.tagName === 'TEXTAREA' ||
                document.activeElement.isContentEditable
            );
            
            if (isInputFocused) return;
            
            // S key - Setup
            if (event.key === 's' || event.key === 'S') {{
                window.location.href = '/setup';
                return;
            }}
            
            // L key - Layout
            if (event.key === 'l' || event.key === 'L') {{
                window.location.href = '/layout';
                return;
            }}
            
            // C key - Config
            if (event.key === 'c' || event.key === 'C') {{
                window.location.href = '/config';
                return;
            }}
            
            // M key - Modules (already here)
            if (event.key === 'm' || event.key === 'M') {{
                window.location.href = '/modules';
                return;
            }}
        }});
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
