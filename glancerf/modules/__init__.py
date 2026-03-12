"""
Cell modules for GlanceRF.
Each module is a folder (e.g. clock/) containing:
  - module.py   -> defines MODULE = {"id", "name", "color", "settings"?, ...}
  - index.html  -> inner HTML for the cell (optional; can be empty)
  - style.css   -> CSS injected once per page (optional)
  - script.js   -> JS injected once per page (optional)

Folders whose names start with _ are skipped. User modules live under _custom/ and survive updates.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from glancerf.config import get_logger

_log = get_logger("modules")

_MODULES_DIR = Path(__file__).resolve().parent
_CUSTOM_MODULES_DIR = _MODULES_DIR / "_custom"
_loaded: Optional[List[Dict[str, Any]]] = None
_by_id: Optional[Dict[str, Dict[str, Any]]] = None
_folder_by_id: Optional[Dict[str, Path]] = None

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
    If folder has __init__.py, load as package first so api_routes can be imported."""
    module_py = folder / "module.py"
    if not module_py.is_file():
        return None
    pkg_name = f"{spec_prefix}.{folder.name}"
    try:
        if (folder / "__init__.py").is_file():
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
        doc = (mod.__doc__ or "").strip()
        m["description"] = doc.split("\n\n")[0][:200] if doc else "No description available"
        if len(m["description"]) >= 200:
            m["description"] = m["description"] + "..."
        # Only load from files if module didn't set these (module.py can use load_assets(__file__))
        for key, filename in [("inner_html", "index.html"), ("css", "style.css"), ("js", "script.js")]:
            if key not in m:
                path = folder / filename
                m[key] = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
        global _folder_by_id
        if _folder_by_id is None:
            _folder_by_id = {}
        _folder_by_id[m["id"]] = folder
        return m
    except Exception as e:
        _log.warning("Failed to load module from %s: %s", folder.name, e)
        return None


def _discover_modules() -> List[Dict[str, Any]]:
    """Scan built-in modules dir, then _custom/. Custom overrides built-in when same id."""
    global _loaded
    if _loaded is not None:
        return _loaded

    result: List[Dict[str, Any]] = [dict(EMPTY_MODULE)]
    seen_ids: set = {""}
    by_id_temp: Dict[str, int] = {}

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


def get_module_assets(
    layout: List[List[str]],
    map_overlay_layout: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """Collect css and js from all modules in layout and map_overlay_layout (when map is in layout).
    Returns (css, js). Map overlay modules are included when map appears in the layout."""
    ids_in_layout: set = set()
    for row in layout or []:
        for cell_value in row:
            if cell_value:
                ids_in_layout.add(cell_value)
    has_map = "map" in ids_in_layout
    if has_map and map_overlay_layout:
        for mid in map_overlay_layout:
            if mid and isinstance(mid, str):
                ids_in_layout.add(mid.strip())
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
    """Clear the in-memory module list so next get_modules() reloads from disk."""
    global _loaded, _by_id, _folder_by_id
    _loaded = None
    _by_id = None
    _folder_by_id = None


def get_modules() -> List[Dict[str, Any]]:
    """Return all discovered cell modules (id, name, color, description). Order: empty first, then by folder name."""
    return _discover_modules()


def get_module_ids() -> List[str]:
    """Return list of module ids (for validation)."""
    return [m["id"] for m in _discover_modules()]


def get_module_dir(module_id: str) -> Optional[Path]:
    """Return the folder path for a module, or None."""
    if _folder_by_id is None:
        _discover_modules()
    return (_folder_by_id or {}).get(module_id)


def _module_package_for_folder(folder: Path) -> Optional[str]:
    """Return the Python package name for a module folder (e.g. glancerf.modules.clock or glancerf.custom.mymod)."""
    try:
        if folder.parent == _CUSTOM_MODULES_DIR:
            return "glancerf.custom." + folder.name
        parent = _MODULES_DIR.parent
        rel = folder.relative_to(parent)
        return parent.name + "." + rel.as_posix().replace("/", ".").replace("\\", ".")
    except (ValueError, AttributeError):
        return None


def get_module_warmer(module_id: str) -> Optional[Callable[[dict, Any], Any]]:
    """Return the cache-warmer callable for a module, or None."""
    m = get_module_by_id(module_id)
    if not m or not m.get("cache_warmer"):
        return None
    folder = get_module_dir(module_id)
    if not folder or not (folder / "warmer.py").is_file():
        return None
    try:
        pkg = _module_package_for_folder(folder)
        if not pkg:
            return None
        mod = importlib.import_module(pkg + ".warmer")
        warm = getattr(mod, "warm", None)
        return warm if callable(warm) else None
    except Exception:
        return None


def get_module_api_packages() -> List[str]:
    """Return package names for modules that provide api_routes.py."""
    _discover_modules()
    packages: List[str] = []
    for folder in (_folder_by_id or {}).values():
        if (folder / "api_routes.py").is_file():
            pkg = _module_package_for_folder(folder)
            if pkg:
                packages.append(pkg)
    return packages


def get_gpio_features() -> List[Dict[str, Any]]:
    """Return GPIO features advertised by modules."""
    _discover_modules()
    result: List[Dict[str, Any]] = []
    for m in (_loaded or []):
        mid = m.get("id") or ""
        if not mid:
            continue
        gpio = m.get("gpio")
        if not isinstance(gpio, dict):
            continue
        name = m.get("name") or mid
        for item in gpio.get("inputs") or []:
            if isinstance(item, dict) and item.get("id") and item.get("name"):
                result.append({
                    "module_id": mid,
                    "module_name": name,
                    "direction": "in",
                    "function_id": str(item["id"]),
                    "function_name": str(item["name"]),
                })
        for item in gpio.get("outputs") or []:
            if isinstance(item, dict) and item.get("id") and item.get("name"):
                result.append({
                    "module_id": mid,
                    "module_name": name,
                    "direction": "out",
                    "function_id": str(item["id"]),
                    "function_name": str(item["name"]),
                })
    return result


def validate_module_dependencies() -> List[Tuple[str, str]]:
    """Try to import each module's api_routes. Returns (module_name, error_message) for failures."""
    try:
        from glancerf.utils.numpy_fallback import try_numpy_baseline_fallback
    except ImportError:
        try_numpy_baseline_fallback = lambda e: False

    failures: List[Tuple[str, str]] = []
    for pkg in get_module_api_packages():
        module_name = pkg.split(".")[-1] if "." in pkg else pkg
        try:
            importlib.import_module(pkg + ".api_routes")
        except ModuleNotFoundError as e:
            missing = e.name or "unknown"
            failures.append((module_name, f"Missing dependency '{missing}'. Install with: pip install {missing}"))
        except Exception as e:
            if try_numpy_baseline_fallback(e):
                return validate_module_dependencies()
            failures.append((module_name, str(e)))
    return failures
