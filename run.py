#!/usr/bin/env python3
"""
Main entry point for GlanceRF
"""

import sys
import signal
import threading
from pathlib import Path

# Add the Project directory to the path so we can import glancerf
sys.path.insert(0, str(Path(__file__).parent))

from glancerf.main import run_server, run_readonly_server
from glancerf.config import get_config
from glancerf.utils import get_local_ip
from glancerf.logging_config import setup_logging, get_logger


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
    port = config.get("port")
    readonly_port = config.get("readonly_port")
    use_desktop = config.get("use_desktop")

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
        # GUI libraries (PyQt5, PyQtWebEngine) are only imported here if desktop mode is enabled
        # This allows headless operation without GUI dependencies installed
        # Import desktop module (only if needed)
        try:
            from glancerf.desktop import run_desktop
            import time
            import urllib.request
            import urllib.error
            
            # Start server in a separate thread
            local_ip = get_local_ip()
            log.info("Starting main server on http://%s:%s", local_ip, port)
            server_thread = threading.Thread(
                target=run_server,
                args=("0.0.0.0", port, True),  # host, port, quiet - bind all interfaces so IP access works
                daemon=True
            )
            server_thread.start()
            
            # Wait for server to be ready (check if it responds)
            max_wait = 10  # seconds
            waited = 0
            server_ready = False
            while waited < max_wait:
                try:
                    urllib.request.urlopen(f"http://localhost:{port}/api/time", timeout=1)
                    server_ready = True
                    break
                except (urllib.error.URLError, OSError):
                    time.sleep(0.5)
                    waited += 0.5
            
            if not server_ready:
                log.error("Server did not start within %s seconds - desktop window may not load correctly", max_wait)

            # Run desktop application
            log.info("Starting desktop app")
            run_desktop(port, server_thread)
            
        except ImportError as e:
            log.error("Could not import desktop module: %s", e)
            log.error("Falling back to server-only mode")
            log.error("Make sure PyQt5 and PyQtWebEngine are installed: pip install PyQt5 PyQtWebEngine")
            run_server(port=port)
    else:
        # Server-only mode
        local_ip = get_local_ip()
        log.info("Starting main server on http://%s:%s", local_ip, port)
        run_server(port=port, quiet=False)


if __name__ == "__main__":
    main()
