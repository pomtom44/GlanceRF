# ---------------------------------------------------------------------------
# Example module - template for creating new cell modules
# ---------------------------------------------------------------------------
# HOW TO USE: Copy this entire folder and rename it to your module id
# (e.g. my_weather). Folders whose names start with _ (like _example) are
# skipped by the loader and never appear in the module list.
#
# FILES IN THIS FOLDER:
#   module.py   - This file. Defines the MODULE dict (id, name, color, optional settings).
#   index.html  - HTML fragment injected into each grid cell that uses this module.
#   style.css   - CSS for this module only. Scoped under .grid-cell-{id}.
#   script.js   - JS that runs on the page; finds and updates this module's cells.
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
