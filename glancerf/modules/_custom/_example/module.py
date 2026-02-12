# ---------------------------------------------------------------------------
# Example module - template for creating new cell modules
# ---------------------------------------------------------------------------
# HOW TO USE: Copy this entire folder (glancerf/modules/_custom/_example/) and
# rename the copy to your module id (e.g. my_weather). Keep __init__.py. Then edit module.py,
# index.html, style.css, and script.js. Your module will appear in the layout editor.
#
# FILES IN THIS FOLDER:
#   __init__.py - Makes this folder a Python package. Required if you add api_routes.py; keep it.
#   module.py   - This file. Defines the MODULE dict (id, name, color, optional settings).
#   index.html  - HTML fragment injected into each grid cell that uses this module.
#   style.css   - CSS for this module only. Scoped under .grid-cell-{id}.
#   script.js   - JS that runs on the page; finds and updates this module's cells.
#   api_routes.py - Optional. If you add it, keep __init__.py so the core can load your routes.
#
# NAMING: Use your module id + underscore for all classes you define
# (e.g. my_module_label). The core adds .grid-cell-{id} to the cell div;
# your CSS/JS use that to scope styles and find cells. See index/style/script.
# ---------------------------------------------------------------------------

MODULE = {
    "id": "example",
    "name": "Example",
    "color": "#333333",
    # Optional: "settings": [ {"id": "foo", "label": "Foo", "type": "text", "default": ""}, ... ],
}
