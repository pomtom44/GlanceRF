#!/usr/bin/env python3
"""
Main entry point for GlanceRF
"""

import os
import sys
import signal
import threading
from pathlib import Path

# Add the Project directory to the path so we can import glancerf
sys.path.insert(0, str(Path(__file__).parent))

from glancerf.main import run_server, run_readonly_server
from glancerf.config import get_config
from glancerf.utils import get_local_ip
from glancerf.config import setup_logging, get_logger
from glancerf.modules import validate_module_dependencies


def _graceful_shutdown(signum=None, frame=None):
    """Handle Ctrl+C / Cmd+C and SIGTERM with a clean message and normal shutdown."""
    log = get_logger("run")
    log.info("Shutting down GlanceRF...")
    raise KeyboardInterrupt()


def main():
    """Main entry point - all configuration from config file"""
    # Graceful shutdown on Ctrl+C (SIGINT) and SIGTERM
    try:
        signal.signal(signal.SIGINT, _graceful_shutdown)
    except (ValueError, OSError):
        pass  # SIGINT not available in some contexts (e.g. non-main thread)
    try:
        signal.signal(signal.SIGTERM, _graceful_shutdown)
    except (ValueError, OSError, AttributeError):
        pass  # SIGTERM not available on all platforms

    # Get all settings from config file; set up logging from config
    try:
        config = get_config()
        setup_logging(config)
    except (FileNotFoundError, IOError) as e:
        import logging
        logging.basicConfig(level=logging.ERROR, format="%(message)s")
        logging.error("Error: %s", e)
        logging.error("Config file not found or invalid.")
        sys.exit(1)

    log = get_logger("run")

    failures = validate_module_dependencies()
    if failures:
        for module_name, err_msg in failures:
            log.error("Module '%s' could not be loaded: %s", module_name, err_msg)
        log.error("Fix the above and restart GlanceRF.")
        sys.exit(1)

    port = config.get("port")
    readonly_port = config.get("readonly_port")
    use_desktop = config.get("use_desktop")

    # Env overrides for ports (e.g. Docker)
    if os.environ.get("GLANCERF_PORT"):
        port = int(os.environ["GLANCERF_PORT"])
    if os.environ.get("GLANCERF_READONLY_PORT"):
        readonly_port = int(os.environ["GLANCERF_READONLY_PORT"])
    # In Docker always run server-only; ignore use_desktop from config.
    if os.environ.get("GLANCERF_DOCKER"):
        use_desktop = False

    if port is None or readonly_port is None or use_desktop is None:
        log.error("Missing required configuration values: port, readonly_port, or use_desktop")
        sys.exit(1)

    # Start read-only server in a separate thread (always)
    local_ip = get_local_ip()
    log.info("Starting read-only server on http://%s:%s", local_ip, readonly_port)
    readonly_thread = threading.Thread(
        target=run_readonly_server,
        args=("0.0.0.0", readonly_port, True),  # host, port, quiet
        daemon=True
    )
    readonly_thread.start()

    if use_desktop:
        # Desktop mode: run main server in a thread (logs in this terminal), wait for ready, open browser, then block
        import time
        import urllib.request
        import urllib.error
        import webbrowser

        log.info("Starting main server on http://%s:%s", local_ip, port)
        server_thread = threading.Thread(
            target=run_server,
            args=("0.0.0.0", port, False),  # host, port, quiet=False so logs show in terminal
            daemon=False
        )
        server_thread.start()

        max_wait = 10
        waited = 0
        server_ready = False
        while waited < max_wait:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/time", timeout=1)
                server_ready = True
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
                waited += 0.5

        if server_ready:
            webbrowser.open(f"http://127.0.0.1:{port}")
        else:
            log.warning("Server did not respond within %s seconds; open http://127.0.0.1:%s in your browser", max_wait, port)

        server_thread.join()
    else:
        # Server (headless) mode: no browser launch
        log.info("Starting main server on http://%s:%s", local_ip, port)
        run_server(host="0.0.0.0", port=port, quiet=False)


if __name__ == "__main__":
    main()
