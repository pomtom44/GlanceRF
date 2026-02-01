"""
Cell modules for GlanceRF.
Each module is a folder (e.g. clock/) containing:
  - module.py   -> defines MODULE = {"id", "name", "color", "settings"?, ...}
  - index.html  -> inner HTML for the cell (optional; can be empty)
  - style.css   -> CSS injected once per page (optional)
  - script.js   -> JS injected once per page (optional)

Folders whose names start with _ are skipped and not loaded as modules.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_MODULES_DIR = Path(__file__).resolve().parent
# User modules live under glancerf/modules/_custom/; updater merges modules/ so this survives updates
_CUSTOM_MODULES_DIR = _MODULES_DIR / "_custom"
_loaded: Optional[List[Dict[str, Any]]] = None
_by_id: Optional[Dict[str, Dict[str, Any]]] = None
_folder_by_id: Optional[Dict[str, Path]] = None

# Built-in "empty" option for unset cells (no folder)
EMPTY_MODULE: Dict[str, Any] = {
    "id": "",
    "name": "-- Select module --",
    "color": "#111",
    "inner_html": "",
    "css": "",
    "js": "",
}


def _load_module_from_folder(folder: Path, spec_prefix: str = "glancerf.modules") -> Optional[Dict[str, Any]]:
    """Load MODULE from folder/module.py and inject inner_html, css, js from files."""
    module_py = folder / "module.py"
    if not module_py.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            f"{spec_prefix}.{folder.name}", module_py
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        if not hasattr(mod, "MODULE"):
            return None
        m = dict(mod.MODULE)
        if not isinstance(m, dict) or "id" not in m or "name" not in m or "color" not in m:
            return None
        # Override with file contents if present (so module.py can omit inner_html/css/js)
        for key, filename in [("inner_html", "index.html"), ("css", "style.css"), ("js", "script.js")]:
            path = folder / filename
            if path.is_file():
                m[key] = path.read_text(encoding="utf-8").strip()
            elif key not in m:
                m[key] = ""
        global _folder_by_id
        if _folder_by_id is None:
            _folder_by_id = {}
        _folder_by_id[m["id"]] = folder
        return m
    except Exception:
        return None


def _discover_modules() -> List[Dict[str, Any]]:
    """Scan built-in modules dir, then static glancerf/modules/_custom/. Custom overrides built-in when same id."""
    global _loaded
    if _loaded is not None:
        return _loaded

    result: List[Dict[str, Any]] = [dict(EMPTY_MODULE)]
    seen_ids: set = {""}
    by_id_temp: Dict[str, int] = {}  # id -> index in result (for override)

    for folder in sorted(_MODULES_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("_"):
            continue
        m = _load_module_from_folder(folder)
        if m:
            if m["id"] in seen_ids:
                idx = by_id_temp[m["id"]]
                result[idx] = m
            else:
                result.append(m)
                seen_ids.add(m["id"])
                by_id_temp[m["id"]] = len(result) - 1

    if _CUSTOM_MODULES_DIR.is_dir():
        for folder in sorted(_CUSTOM_MODULES_DIR.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue
            m = _load_module_from_folder(folder, spec_prefix="glancerf.custom")
            if m:
                if m["id"] in seen_ids:
                    idx = by_id_temp[m["id"]]
                    result[idx] = m
                else:
                    result.append(m)
                    seen_ids.add(m["id"])
                    by_id_temp[m["id"]] = len(result) - 1

    result.sort(key=lambda m: (m["id"] != "", m["id"]))
    global _by_id, _folder_by_id
    _loaded = result
    _by_id = {m["id"]: m for m in result}
    if _folder_by_id is None:
        _folder_by_id = {}
    return result


def get_module_by_id(module_id: str) -> Optional[Dict[str, Any]]:
    """Return the module dict for the given id, or None."""
    if _by_id is None:
        _discover_modules()
    return (_by_id or {}).get(module_id)


def get_module_assets(layout: List[List[str]]) -> Tuple[str, str]:
    """Collect css and js from all modules that appear in layout. Returns (css, js)."""
    ids_in_layout: set = set()
    for row in layout or []:
        for cell_value in row:
            if cell_value:
                ids_in_layout.add(cell_value)
    css_parts: List[str] = []
    js_parts: List[str] = []
    done_css: set = set()
    done_js: set = set()
    for mid in ids_in_layout:
        m = get_module_by_id(mid)
        if not m:
            continue
        if m.get("css") and mid not in done_css:
            css_parts.append(m["css"])
            done_css.add(mid)
        if m.get("js") and mid not in done_js:
            js_parts.append(m["js"])
            done_js.add(mid)
    return ("\n".join(css_parts), "\n".join(js_parts))


def get_modules() -> List[Dict[str, Any]]:
    """Return all discovered cell modules (id, name, color). Order: empty first, then by folder name."""
    return _discover_modules()


def get_color_map() -> Dict[str, str]:
    """Return a map from module id to background color (for grid rendering)."""
    return {m["id"]: m["color"] for m in _discover_modules()}


def get_module_ids() -> List[str]:
    """Return list of module ids (for validation if needed)."""
    return [m["id"] for m in _discover_modules()]


def get_module_dir(module_id: str) -> Optional[Path]:
    """Return the folder path for a folder-based module, or None (e.g. empty module has no folder)."""
    if _folder_by_id is None:
        _discover_modules()
    return (_folder_by_id or {}).get(module_id)
