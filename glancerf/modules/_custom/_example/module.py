"""
Example module - template for creating new cell modules.

Structure: HTML, CSS, JS files + Python script.
The Python script loads the 3 files and does any processing (API routes, etc.).

This folder is prefixed with _ so it is NOT loaded as a module (copy to a new
folder without the underscore to create a real module).
"""

from glancerf.modules.loader import load_assets

# Load HTML, CSS, JS from sibling files
inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "example",
    "name": "Example",
    "color": "#1a1a2e",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    # Optional: per-cell settings in layout editor
    # "settings": [
    #     {"id": "source", "label": "Data source", "type": "text", "default": ""},
    # ],
}
