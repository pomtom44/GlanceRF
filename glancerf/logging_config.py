"""
Logging configuration for GlanceRF.
Configures console (always) and optional log file from config.
Levels: default (INFO: startup/shutdown, ERROR: errors), detailed (+ DETAILED: requests, heartbeat, etc.), verbose (+ DEBUG: everything else).
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Custom level between DEBUG (10) and INFO (20): web requests, heartbeat, update checks
DETAILED_LEVEL = 15
logging.addLevelName(DETAILED_LEVEL, "DETAILED")

LOG_LEVEL_MAP = {
    "default": logging.INFO,     # startup, shutdown (INFO), errors (ERROR)
    "detailed": DETAILED_LEVEL,  # same + DETAILED (web requests, heartbeat, sync checks)
    "verbose": logging.DEBUG,    # same + DEBUG (per-request details, etc.)
}


def _level_from_config(config: Any) -> int:
    """Resolve numeric level from config. Default to INFO if missing or invalid."""
    raw = config.get("log_level") if hasattr(config, "get") else None
    if not raw:
        return logging.INFO
    return LOG_LEVEL_MAP.get(str(raw).strip().lower(), logging.INFO)


def _log_path_from_config(config: Any) -> Optional[str]:
    """Return log file path if set and non-empty, else None."""
    raw = config.get("log_path") if hasattr(config, "get") else None
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def setup_logging(config: Any) -> None:
    """
    Configure logging for GlanceRF from config.
    - Always adds a console handler.
    - Adds a file handler only if config has a non-empty "log_path".
    - Level comes from config "log_level": "default" | "detailed" | "verbose".
    """
    level = _level_from_config(config)
    log_path = _log_path_from_config(config)

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    root = logging.getLogger("glancerf")
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_path:
        path = Path(log_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as e:
            root.warning("Could not open log file %s: %s", log_path, e)

    # Ensure child loggers (glancerf.telemetry, etc.) use our level
    logging.getLogger("glancerf").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given name (e.g. glancerf.telemetry). Prefer glancerf.* namespace."""
    if not name.startswith("glancerf."):
        name = "glancerf." + name
    return logging.getLogger(name)
