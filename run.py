#!/usr/bin/env python3
"""
Main entry point for GlanceRF.
Runs the web server and launches UI based on config.
"""

import os
import signal
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add Project directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Hide console window on Windows only when in desktop mode (native window).
# Terminal + Browser mode: keep console visible. Set GLANCERF_SHOW_CONSOLE=1 to force visible.
if sys.platform == "win32" and not os.environ.get("GLANCERF_DOCKER") and not os.environ.get("GLANCERF_SHOW_CONSOLE"):
    _hide_console = False
    try:
        import json
        _cfg_path = Path(__file__).parent / "glancerf_config.json"
        if _cfg_path.exists():
            with open(_cfg_path, encoding="utf-8") as _f:
                _d = json.load(_f)
            _mode = str(_d.get("desktop_mode", "browser")).strip().lower()
            if _mode == "none":
                _mode = "headless"
            if os.environ.get("GLANCERF_DESKTOP_MODE"):
                _mode = str(os.environ["GLANCERF_DESKTOP_MODE"]).strip().lower()
                if _mode == "none":
                    _mode = "headless"
            # Only hide when desktop app (native window); browser/headless keep terminal visible
            _hide_console = (_mode == "desktop")
        if _hide_console:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass

# Show splash only for desktop window mode (not headless/browser) - quick config read first
_splash_root = None
if sys.platform == "win32" and not os.environ.get("GLANCERF_DOCKER"):
    _need_splash = False
    try:
        import json
        _cfg_path = Path(__file__).parent / "glancerf_config.json"
        if _cfg_path.exists():
            with open(_cfg_path, encoding="utf-8") as _f:
                _d = json.load(_f)
            if "desktop_mode" in _d:
                _mode = str(_d["desktop_mode"]).strip().lower()
                _need_splash = (_mode == "desktop")
            elif "use_desktop" in _d and "desktop_window" in _d:
                _need_splash = bool(_d["use_desktop"] and _d["desktop_window"])
            else:
                _need_splash = bool(_d.get("use_desktop", True)) and bool(_d.get("desktop_window", False))
        if os.environ.get("GLANCERF_DESKTOP_MODE"):
            _em = str(os.environ["GLANCERF_DESKTOP_MODE"]).strip().lower()
            _need_splash = (_em == "desktop")
        if _need_splash:
            import tkinter as tk
            _splash_root = tk.Tk()
            _splash_root.title("GlanceRF")
            _splash_root.resizable(False, False)
            _splash_root.attributes("-topmost", True)
            _lbl = tk.Label(_splash_root, text="Starting GlanceRF...", font=("Segoe UI", 12))
            _lbl.pack(padx=40, pady=30)
            _w, _h = 260, 90
            _x = (_splash_root.winfo_screenwidth() - _w) // 2
            _y = (_splash_root.winfo_screenheight() - _h) // 2
            _splash_root.geometry(f"{_w}x{_h}+{_x}+{_y}")
            _splash_root.update_idletasks()
            _splash_root.update()
            for _ in range(3):
                _splash_root.update()
    except Exception:
        _splash_root = None

from glancerf.config import ConfigValidationError, get_config, get_logger, setup_logging
from glancerf.main import run_server, run_readonly_server
from glancerf.modules import validate_module_dependencies
from glancerf.utils import get_local_ip


def _wait_for_http(log, url: str, name: str, max_wait: float = 10, on_wait=None) -> bool:
    """Poll URL until it responds or max_wait seconds. Returns True if ready. on_wait called each poll."""
    waited = 0
    while waited < max_wait:
        if on_wait:
            try:
                on_wait()
            except Exception:
                pass
        try:
            import urllib.request
            import urllib.error
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
            waited += 0.5
    log.warning("%s did not respond within %s seconds", name, max_wait)
    return False


def _graceful_shutdown(signum=None, frame=None):
    """Handle Ctrl+C / SIGTERM with clean shutdown."""
    log = get_logger("run")
    log.info("Shutting down GlanceRF...")
    sys.exit(0)


def main():
    """Main entry point - configuration from config file."""
    # Graceful shutdown
    try:
        signal.signal(signal.SIGINT, _graceful_shutdown)
    except (ValueError, OSError):
        pass
    try:
        signal.signal(signal.SIGTERM, _graceful_shutdown)
    except (ValueError, OSError, AttributeError):
        pass

    # Load config and set up logging
    try:
        config = get_config()
        setup_logging(config)
    except (FileNotFoundError, IOError, ConfigValidationError) as e:
        if _splash_root:
            try:
                _splash_root.destroy()
            except Exception:
                pass
        import logging
        logging.basicConfig(level=logging.ERROR, format="%(message)s")
        logging.error("Error: %s", e)
        logging.error("Config file not found or invalid.")
        sys.exit(1)

    log = get_logger("run")

    port = config.get("port", 8080)
    readonly_port = config.get("readonly_port", 8081)
    desktop_mode = str(config.get("desktop_mode", "browser")).strip().lower()
    if desktop_mode == "none":
        desktop_mode = "headless"
    if os.environ.get("GLANCERF_DOCKER"):
        desktop_mode = "headless"
    if os.environ.get("GLANCERF_DESKTOP_MODE"):
        desktop_mode = str(os.environ["GLANCERF_DESKTOP_MODE"]).strip().lower()
        if desktop_mode == "none":
            desktop_mode = "headless"
    if os.environ.get("GLANCERF_PORT"):
        port = int(os.environ["GLANCERF_PORT"])
    if os.environ.get("GLANCERF_READONLY_PORT"):
        readonly_port = int(os.environ["GLANCERF_READONLY_PORT"])
    use_desktop = desktop_mode in ("desktop", "browser")
    desktop_window = desktop_mode == "desktop" and sys.platform == "win32"
    if _splash_root and (use_desktop and desktop_window):
        splash_root = _splash_root
    else:
        if _splash_root:
            try:
                _splash_root.destroy()
            except Exception:
                pass
        splash_root = None

    # Validate module dependencies (returns empty until modules are implemented)
    failures = validate_module_dependencies()
    if failures:
        if splash_root:
            try:
                splash_root.destroy()
            except Exception:
                pass
        for module_name, err_msg in failures:
            log.error("Module '%s' could not be loaded: %s", module_name, err_msg)
        log.error("Fix the above and restart GlanceRF.")
        sys.exit(1)

    if port is None or readonly_port is None:
        log.error("Missing required configuration: port or readonly_port")
        sys.exit(1)

    # Ensure we run from the Project directory (important when launched from shortcut)
    project_dir = Path(__file__).parent
    try:
        os.chdir(project_dir)
    except OSError:
        pass

    # V7 does not relaunch with pythonw - run in same process so server starts correctly.
    # Use GLANCERF_NO_CONSOLE=1 or a shortcut with pythonw to hide the console if desired.
    local_ip = get_local_ip()
    use_desktop_window = desktop_window and sys.platform == "win32"

    # Match V7: readonly first, then main server (both in threads)
    log.info("Starting read-only server on http://%s:%s", local_ip, readonly_port)
    readonly_thread = threading.Thread(
        target=run_readonly_server,
        args=("0.0.0.0", readonly_port, True),
        daemon=True,
    )
    readonly_thread.start()

    log.info("Starting main server on http://%s:%s", local_ip, port)
    server_thread = threading.Thread(
        target=run_server,
        args=("0.0.0.0", port, True),
        daemon=True,
    )
    server_thread.start()

    if use_desktop:
        # Wait for main (read-write) server to be ready (30s for Sandbox/VMs)
        server_ready = _wait_for_http(
            log, f"http://127.0.0.1:{port}/api/time", "main server", max_wait=30,
            on_wait=lambda: splash_root.update() if splash_root else None,
        )
        if not server_ready:
            log.warning("Main server did not start within 30 seconds - desktop may show Retry")

        if use_desktop_window:
            # Apply config.disable_gpu or runtime Sandbox detection before importing desktop
            if config.get("disable_gpu"):
                os.environ["GLANCERF_DISABLE_GPU"] = "1"
            elif not os.environ.get("GLANCERF_DISABLE_GPU"):
                try:
                    from glancerf.desktop.gpu_detect import should_disable_gpu
                    if should_disable_gpu():
                        os.environ["GLANCERF_DISABLE_GPU"] = "1"
                except Exception:
                    pass
            try:
                from glancerf.desktop import run_desktop
                log.info("Starting desktop window (Windows)")
                run_desktop(port, server_thread, splash_root=splash_root)
            except ImportError as e:
                log.warning("Desktop window unavailable (%s); falling back to browser", e)
                if splash_root:
                    try:
                        splash_root.destroy()
                    except Exception:
                        pass
                if server_ready:
                    webbrowser.open(f"http://localhost:{port}")
                else:
                    log.info("Open http://localhost:%s in your browser", port)

        if not use_desktop_window:
            if server_ready:
                webbrowser.open(f"http://localhost:{port}")
            else:
                log.info("Open http://localhost:%s in your browser", port)

    # Keep main thread alive (server runs in daemon thread)
    try:
        while server_thread.is_alive():
            server_thread.join(timeout=1)
    except KeyboardInterrupt:
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
