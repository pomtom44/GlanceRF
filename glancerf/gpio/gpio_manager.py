"""
GPIO runtime manager for GlanceRF.
Configures pins from gpio_assignments, dispatches input events to modules,
and exposes set_output() for modules to drive output pins.
Only active when gpio_support.is_gpio_available() is True.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from glancerf.config import get_config
from glancerf.config import get_logger
from glancerf.gpio.gpio_support import get_available_pins, is_gpio_available

_log = get_logger("gpio_manager")

_GPIO: Any = None
_assignments: Dict[str, Dict[str, str]] = {}
_feature_by_key: Dict[str, Dict[str, Any]] = {}
_handlers_cache: Dict[str, Dict[str, Callable[[bool], None]]] = {}
_pins_configured: set = set()
_broadcast_cm: Any = None
_broadcast_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_gpio_module():
    """Lazy import RPi.GPIO so it is only loaded when GPIO is available."""
    global _GPIO
    if _GPIO is None and is_gpio_available():
        try:
            import RPi.GPIO as G
            _GPIO = G
        except ImportError:
            pass
    return _GPIO


def _build_feature_key(module_id: str, function_id: str) -> str:
    return f"{module_id}:{function_id}"


def _direction_for_feature(module_id: str, function_id: str) -> Optional[str]:
    return _feature_by_key.get(_build_feature_key(module_id, function_id), {}).get("direction")


def _get_module_dir(module_id: str) -> Optional[Path]:
    """Return module folder path for module_id."""
    try:
        from glancerf.modules import get_module_dir
        return get_module_dir(module_id)
    except ImportError:
        return None


def _load_input_handlers(module_id: str) -> Dict[str, Callable[[bool], None]]:
    """Load GPIO_INPUT_HANDLERS from the module's module.py."""
    if module_id in _handlers_cache:
        return _handlers_cache[module_id]
    result: Dict[str, Callable[[bool], None]] = {}
    folder = _get_module_dir(module_id)
    if not folder:
        _handlers_cache[module_id] = result
        return result
    module_py = folder / "module.py"
    if not module_py.is_file():
        _handlers_cache[module_id] = result
        return result
    spec_name = f"glancerf.gpio_module_{module_id}"
    try:
        spec = importlib.util.spec_from_file_location(spec_name, module_py)
        if spec is None or spec.loader is None:
            _handlers_cache[module_id] = result
            return result
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec_name] = mod
        spec.loader.exec_module(mod)
        handlers = getattr(mod, "GPIO_INPUT_HANDLERS", None)
        if isinstance(handlers, dict):
            for fid, fn in handlers.items():
                if callable(fn):
                    result[str(fid)] = fn
        _handlers_cache[module_id] = result
    except Exception as e:
        _log.debug("gpio_manager: could not load input handlers for %s: %s", module_id, e)
        _handlers_cache[module_id] = result
    return result


def _on_pin_event(pin_bcm: int) -> None:
    """Called when an input pin changes. Dispatch to the assigned module handler."""
    pin_str = str(pin_bcm)
    assignment = _assignments.get(pin_str)
    if not assignment:
        return
    module_id = assignment.get("module_id")
    function_id = assignment.get("function_id")
    if not module_id or not function_id:
        return
    if _direction_for_feature(module_id, function_id) != "in":
        return
    G = _get_gpio_module()
    if not G:
        return
    try:
        value = G.input(pin_bcm)
        value = bool(value)
    except Exception as e:
        _log.debug("gpio_manager: read pin %s failed: %s", pin_bcm, e)
        return
    handlers = _load_input_handlers(module_id)
    handler = handlers.get(function_id)
    if handler:
        try:
            handler(value)
        except Exception as e:
            _log.exception("gpio_manager: module %s handler %s failed: %s", module_id, function_id, e)
    else:
        _log.debug("gpio_manager: no handler for %s/%s", module_id, function_id)
    if _broadcast_cm is not None and _broadcast_loop is not None:
        try:
            asyncio.run_coroutine_threadsafe(
                _broadcast_cm.broadcast_gpio_input(module_id, function_id, value),
                _broadcast_loop,
            )
        except Exception as e:
            _log.debug("gpio_manager: broadcast failed: %s", e)


def set_broadcast(connection_manager: Any, loop: asyncio.AbstractEventLoop) -> None:
    """Set the connection manager and event loop for GPIO input broadcast. Call from main at startup."""
    global _broadcast_cm, _broadcast_loop
    _broadcast_cm = connection_manager
    _broadcast_loop = loop


def set_output(module_id: str, function_id: str, value: bool) -> None:
    """Set a GPIO output pin. Call from modules that own an output function."""
    G = _get_gpio_module()
    if not G:
        _log.debug("gpio_manager: set_output ignored (GPIO not available)")
        return
    key = _build_feature_key(module_id, function_id)
    if _feature_by_key.get(key, {}).get("direction") != "out":
        _log.debug("gpio_manager: set_output %s/%s not an output", module_id, function_id)
        return
    for pin_str, assignment in _assignments.items():
        if assignment.get("module_id") == module_id and assignment.get("function_id") == function_id:
            try:
                pin_bcm = int(pin_str)
                G.output(pin_bcm, G.HIGH if value else G.LOW)
                return
            except (ValueError, RuntimeError) as e:
                _log.debug("gpio_manager: set_output pin %s failed: %s", pin_str, e)
                return
    _log.debug("gpio_manager: no pin assigned for output %s/%s", module_id, function_id)


def start_gpio_manager() -> None:
    """Load assignments from config and configure pins. No-op if GPIO not available."""
    global _assignments, _feature_by_key, _pins_configured
    if not is_gpio_available():
        return
    try:
        from glancerf.modules import get_gpio_features
        features = get_gpio_features()
    except ImportError:
        features = []
    G = _get_gpio_module()
    if not G:
        return
    try:
        G.setmode(G.BCM)
        G.setwarnings(False)
    except Exception as e:
        _log.debug("gpio_manager: init failed: %s", e)
        return
    config = get_config()
    raw = config.get("gpio_assignments") or {}
    if not isinstance(raw, dict):
        raw = {}
    features_dict = {_build_feature_key(f["module_id"], f["function_id"]): f for f in features}
    _feature_by_key.clear()
    _feature_by_key.update(features_dict)
    _assignments.clear()
    for pin_str, val in raw.items():
        if not isinstance(val, dict):
            continue
        mid = val.get("module_id")
        fid = val.get("function_id")
        if not mid or not fid:
            continue
        key = _build_feature_key(mid, fid)
        if key not in features_dict:
            continue
        _assignments[pin_str] = {"module_id": mid, "function_id": fid}
    available_bcm = {bcm for bcm, _ in get_available_pins()}
    for pin_str, assignment in _assignments.items():
        try:
            pin_bcm = int(pin_str)
        except ValueError:
            continue
        if pin_bcm not in available_bcm:
            continue
        direction = _direction_for_feature(assignment["module_id"], assignment["function_id"])
        if direction == "in":
            try:
                G.setup(pin_bcm, G.IN, pull_up_down=G.PUD_UP)
                G.add_event_detect(pin_bcm, G.BOTH, callback=lambda p=pin_bcm: _on_pin_event(p), bouncetime=50)
                _pins_configured.add(pin_bcm)
            except Exception as e:
                _log.debug("gpio_manager: setup input pin %s failed: %s", pin_bcm, e)
        elif direction == "out":
            try:
                G.setup(pin_bcm, G.OUT, initial=G.LOW)
                _pins_configured.add(pin_bcm)
            except Exception as e:
                _log.debug("gpio_manager: setup output pin %s failed: %s", pin_bcm, e)
    _log.debug("gpio_manager: started with %s assignments", len(_assignments))


def stop_gpio_manager() -> None:
    """Clean up GPIO and remove event detection."""
    global _pins_configured
    G = _get_gpio_module()
    if not G:
        return
    for pin_bcm in list(_pins_configured):
        try:
            G.remove_event_detect(pin_bcm)
        except Exception:
            pass
        try:
            G.cleanup(pin_bcm)
        except Exception:
            pass
    _pins_configured.clear()
    try:
        G.cleanup()
    except Exception:
        pass
    _log.debug("gpio_manager: stopped")
