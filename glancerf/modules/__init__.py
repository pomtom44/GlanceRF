"""
Cell modules for GlanceRF.
Each module is a folder (e.g. clock/) containing:
  - module.py   -> defines MODULE = {"id", "name", "color", "settings"?, ...}
  - index.html  -> inner HTML for the cell (optional; can be empty)
  - style.css   -> CSS injected once per page (optional)
  - script.js   -> JS injected once per page (optional)

Folders whose names start with _ are skipped and not loaded as modules.
"""

import importlib
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
    """Load MODULE from folder/module.py and inject inner_html, css, js from files.
    If folder has __init__.py, load it as a package first so api_routes can be imported as a submodule."""
    module_py = folder / "module.py"
    if not module_py.is_file():
        return None
    pkg_name = f"{spec_prefix}.{folder.name}"
    try:
        if (folder / "__init__.py").is_file():
            # Load as package so pkg.api_routes is importable
            spec_pkg = importlib.util.spec_from_file_location(pkg_name, folder / "__init__.py")
            if spec_pkg is None or spec_pkg.loader is None:
                return None
            pkg = importlib.util.module_from_spec(spec_pkg)
            sys.modules[pkg_name] = pkg
            spec_pkg.loader.exec_module(pkg)
            spec_mod = importlib.util.spec_from_file_location(pkg_name + ".module", module_py)
            if spec_mod is None or spec_mod.loader is None:
                return None
            mod = importlib.util.module_from_spec(spec_mod)
            sys.modules[pkg_name + ".module"] = mod
            spec_mod.loader.exec_module(mod)
            if not hasattr(mod, "MODULE"):
                return None
            m = dict(mod.MODULE)
        else:
            spec = importlib.util.spec_from_file_location(pkg_name, module_py)
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


def clear_module_cache() -> None:
    """Clear the in-memory module list so next get_modules() reloads from disk. Use after editing module.py."""
    global _loaded, _by_id
    _loaded = None
    _by_id = None


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


def get_module_api_packages() -> List[str]:
    """
    Return package names for modules that provide api_routes.py (e.g. glancerf.modules.satellite_pass).
    Core uses this to register each module's API routes at startup.
    """
    _discover_modules()
    packages: List[str] = []
    parent = _MODULES_DIR.parent
    for folder in (_folder_by_id or {}).values():
        if (folder / "api_routes.py").is_file():
            try:
                rel = folder.relative_to(parent)
                pkg = parent.name + "." + rel.as_posix().replace("/", ".").replace("\\", ".")
                packages.append(pkg)
            except ValueError:
                pass
    return packages


def validate_module_dependencies() -> List[Tuple[str, str]]:
    """
    Try to import each module that provides api_routes.py. Returns a list of
    (module_name, error_message) for any that fail. Used at startup to fail fast
    if a module's dependencies (e.g. skyfield for satellite_pass) are missing.
    """
    failures: List[Tuple[str, str]] = []
    for pkg in get_module_api_packages():
        module_name = pkg.split(".")[-1] if "." in pkg else pkg
        try:
            importlib.import_module(pkg + ".api_routes")
        except ModuleNotFoundError as e:
            missing = e.name or "unknown"
            failures.append((module_name, "Missing dependency '%s'. Install with: pip install %s" % (missing, missing)))
        except Exception as e:
            failures.append((module_name, str(e)))
    return failures
