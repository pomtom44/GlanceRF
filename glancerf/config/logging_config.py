"""
Logging configuration for GlanceRF.
Industry-standard setup: structured format, logger hierarchy, configurable levels.

Levels:
- default: Startup and error only. [INFO] for startup/shutdown, [ERROR] for errors.
- detailed: Default plus system calls (web requests, API calls). Messages show [DETAILED].
- verbose: Detailed plus step-by-step internals. Extra messages show [DEBUG].
- debug: Alias for verbose.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Between DEBUG (10) and INFO (20): system calls, one or two per action
DETAILED_LEVEL = 15
logging.addLevelName(DETAILED_LEVEL, "DETAILED")

LOG_LEVEL_MAP = {
    "default": logging.INFO,
    "detailed": DETAILED_LEVEL,
    "verbose": logging.DEBUG,
    "debug": logging.DEBUG,
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
    Configure logging from config.
    - Console handler (always)
    - File handler (if config has non-empty log_path)
    - Level: default | detailed | verbose | debug
    - Format: timestamp | level | logger | message
    """
    level = _level_from_config(config)
    log_path = _log_path_from_config(config)

    # Industry-standard format: timestamp, level, logger name, message
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
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

    logging.getLogger("glancerf").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger. Names are under glancerf.* namespace."""
    if not name.startswith("glancerf."):
        name = "glancerf." + name
    return logging.getLogger(name)
