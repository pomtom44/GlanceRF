"""
GPIO setup routes for GlanceRF.
Only registered when GPIO is available. Serves /gpio setup page and saves assignments.
"""

import json
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from glancerf.config import get_config
from glancerf.gpio import get_available_pins, is_gpio_available, start_gpio_manager, stop_gpio_manager
from glancerf.web.menu_html import get_menu_html
from glancerf.config import get_logger
from glancerf.modules import get_gpio_features
from glancerf.utils import rate_limit_dependency

_log = get_logger("gpio_routes")
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_GPIO_TEMPLATE_PATH = _WEB_DIR / "templates" / "gpio" / "index.html"
_gpio_template_cache = None


def _get_gpio_template() -> str:
    global _gpio_template_cache
    if _gpio_template_cache is None and _GPIO_TEMPLATE_PATH.is_file():
        _gpio_template_cache = _GPIO_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _gpio_template_cache or ""


def _modules_from_features(features):
    """Unique modules from features list, for dropdown."""
    seen = set()
    out = []
    for f in features:
        mid = f.get("module_id")
        if mid and mid not in seen:
            seen.add(mid)
            out.append({"id": mid, "name": f.get("module_name") or mid})
    return out


def _features_by_module(features):
    """Group features by module_id for function dropdown."""
    out = {}
    for f in features:
        mid = f.get("module_id")
        if not mid:
            continue
        if mid not in out:
            out[mid] = []
        out[mid].append({
            "function_id": f.get("function_id"),
            "function_name": f.get("function_name"),
            "direction": f.get("direction"),
        })
    return out


def register_gpio_routes(app: FastAPI):
    """Register GPIO setup routes. Safe to call even when GPIO not available (routes no-op or redirect)."""

    @app.get("/gpio", response_class=HTMLResponse)
    async def gpio_page():
        if not is_gpio_available():
            _log.debug("GET /gpio: GPIO not available, redirect to setup")
            return RedirectResponse(url="/setup")
        try:
            config = get_config()
        except (FileNotFoundError, IOError):
            return RedirectResponse(url="/setup")
        pins = get_available_pins()
        features = get_gpio_features()
        modules = _modules_from_features(features)
        features_by_module = _features_by_module(features)
        assignments = config.get("gpio_assignments") or {}
        if not isinstance(assignments, dict):
            assignments = {}
        template = _get_gpio_template()
        if not template:
            return HTMLResponse(content="<h1>GPIO</h1><p>Template not found.</p>", status_code=500)
        cache_bust = str(int(time.time() * 1000))
        html = template.replace("__PINS_JSON__", json.dumps([{"bcm": b, "label": l} for b, l in pins]))
        html = html.replace("__MODULES_JSON__", json.dumps(modules))
        html = html.replace("__FEATURES_BY_MODULE_JSON__", json.dumps(features_by_module))
        html = html.replace("__ASSIGNMENTS_JSON__", json.dumps(assignments))
        html = html.replace("__GLANCERF_MENU_PANEL__", get_menu_html())
        html = html.replace("__CACHE_BUST__", cache_bust)
        return HTMLResponse(content=html)

    @app.post("/gpio")
    async def gpio_save(request: Request, _: None = Depends(rate_limit_dependency)):
        if not is_gpio_available():
            return JSONResponse({"error": "GPIO not available"}, status_code=400)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        assignments = body.get("assignments")
        if not isinstance(assignments, dict):
            return JSONResponse({"error": "assignments must be an object"}, status_code=400)
        features = {f["module_id"] + ":" + f["function_id"]: f for f in get_gpio_features()}
        pins_valid = {str(b) for b, _ in get_available_pins()}
        normalized = {}
        for pin_str, val in assignments.items():
            if pin_str not in pins_valid:
                continue
            if not isinstance(val, dict):
                continue
            mid = val.get("module_id")
            fid = val.get("function_id")
            if not mid or not fid:
                continue
            key = mid + ":" + fid
            if key not in features:
                continue
            normalized[pin_str] = {"module_id": mid, "function_id": fid}
        config = get_config()
        config.set("gpio_assignments", normalized)
        stop_gpio_manager()
        start_gpio_manager()
        _log.debug("gpio: saved %s assignments", len(normalized))
        return JSONResponse({"ok": True, "assignments": normalized})
