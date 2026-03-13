"""
Configuration management for GlanceRF.
Handles loading and saving settings to JSON file with validation.
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from glancerf.config.logging_config import get_logger

_log = get_logger("config")


class ConfigValidationError(ValueError):
    """Raised when config structure or value types are invalid."""

    pass


def resize_layout_to_grid(layout: list, grid_columns: int, grid_rows: int) -> list:
    """Resize layout to exactly grid_rows x grid_columns, preserving existing cells."""
    result = []
    for row in range(grid_rows):
        result_row = []
        for col in range(grid_columns):
            if layout and row < len(layout) and col < len(layout[row]):
                result_row.append(layout[row][col] if isinstance(layout[row][col], str) else "")
            else:
                result_row.append("")
        result.append(result_row)
    return result


_DESKTOP_MODES = ("desktop", "browser", "terminal", "headless", "none")

_INITIAL_CONFIG: Dict[str, Any] = {
    "port": 8080,
    "readonly_port": 8081,
    "desktop_mode": "browser",
    "first_run": True,
    "max_grid_scale": 10,
}


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate config dict. Raises ConfigValidationError if invalid."""
    if not isinstance(config, dict):
        raise ConfigValidationError("Config must be a JSON object")

    def _check_type(key: str, value: Any, expected_type: type, message: Optional[str] = None) -> None:
        if not isinstance(value, expected_type):
            msg = message or f"Config key {key!r} must be {expected_type.__name__}, got {type(value).__name__}"
            raise ConfigValidationError(msg)

    if "port" in config and config["port"] is not None:
        _check_type("port", config["port"], int)
        p = config["port"]
        if not (1 <= p <= 65535):
            raise ConfigValidationError(f"Config key 'port' must be 1-65535, got {p}")

    if "readonly_port" in config and config["readonly_port"] is not None:
        _check_type("readonly_port", config["readonly_port"], int)
        p = config["readonly_port"]
        if not (1 <= p <= 65535):
            raise ConfigValidationError(f"Config key 'readonly_port' must be 1-65535, got {p}")

    if "desktop_mode" in config and config["desktop_mode"] is not None:
        _check_type("desktop_mode", config["desktop_mode"], str)
        mode = str(config["desktop_mode"]).strip().lower()
        if mode not in _DESKTOP_MODES:
            raise ConfigValidationError(
                f"Config key 'desktop_mode' must be one of {_DESKTOP_MODES}, got {config['desktop_mode']!r}"
            )

    if "max_grid_scale" in config and config["max_grid_scale"] is not None:
        _check_type("max_grid_scale", config["max_grid_scale"], int)
        m = config["max_grid_scale"]
        if not (1 <= m <= 20):
            raise ConfigValidationError(f"Config key 'max_grid_scale' must be 1-20, got {m}")

    if "grid_columns" in config and config["grid_columns"] is not None:
        _check_type("grid_columns", config["grid_columns"], int)
        if config["grid_columns"] < 1:
            raise ConfigValidationError("Config key 'grid_columns' must be at least 1")

    if "grid_rows" in config and config["grid_rows"] is not None:
        _check_type("grid_rows", config["grid_rows"], int)
        if config["grid_rows"] < 1:
            raise ConfigValidationError("Config key 'grid_rows' must be at least 1")

    if "aspect_ratio" in config and config["aspect_ratio"] is not None:
        _check_type("aspect_ratio", config["aspect_ratio"], str)

    if "orientation" in config and config["orientation"] is not None:
        _check_type("orientation", config["orientation"], str)
        if config["orientation"] not in ("landscape", "portrait"):
            raise ConfigValidationError(f"Config key 'orientation' must be 'landscape' or 'portrait'")

    if "layout" in config and config["layout"] is not None:
        _check_type("layout", config["layout"], list)
        for i, row in enumerate(config["layout"]):
            if not isinstance(row, list):
                raise ConfigValidationError(f"Config key 'layout': row {i} must be a list")
            for j, cell in enumerate(row):
                if not isinstance(cell, str):
                    raise ConfigValidationError(f"Config key 'layout': cell ({i},{j}) must be a string")

    if "cell_spans" in config and config["cell_spans"] is not None:
        _check_type("cell_spans", config["cell_spans"], dict)

    if "module_settings" in config and config["module_settings"] is not None:
        _check_type("module_settings", config["module_settings"], dict)

    if "gpio_assignments" in config and config["gpio_assignments"] is not None:
        _check_type("gpio_assignments", config["gpio_assignments"], dict)

    if "first_run" in config and config["first_run"] is not None:
        _check_type("first_run", config["first_run"], bool)

    if "log_level" in config and config["log_level"] is not None:
        _check_type("log_level", config["log_level"], str)
        if config["log_level"] not in ("default", "detailed", "verbose", "debug"):
            raise ConfigValidationError(
                f"Config key 'log_level' must be 'default', 'detailed', 'verbose', or 'debug'"
            )

    if "log_path" in config and config["log_path"] is not None:
        _check_type("log_path", config["log_path"], str)

    if "setup_callsign" in config and config["setup_callsign"] is not None:
        _check_type("setup_callsign", config["setup_callsign"], str)
    if "setup_location" in config and config["setup_location"] is not None:
        _check_type("setup_location", config["setup_location"], str)
    if "gps_location_enabled" in config and config["gps_location_enabled"] is not None:
        _check_type("gps_location_enabled", config["gps_location_enabled"], bool)
    if "gps_time_enabled" in config and config["gps_time_enabled"] is not None:
        _check_type("gps_time_enabled", config["gps_time_enabled"], bool)
    if "gps_source" in config and config["gps_source"] is not None:
        _check_type("gps_source", config["gps_source"], str)
        if config["gps_source"] not in ("gpsd", "serial", "auto"):
            raise ConfigValidationError("Config key 'gps_source' must be 'gpsd', 'serial', or 'auto'")
    if "gps_serial_port" in config and config["gps_serial_port"] is not None:
        _check_type("gps_serial_port", config["gps_serial_port"], str)
    if "setup_ssid" in config and config["setup_ssid"] is not None:
        _check_type("setup_ssid", config["setup_ssid"], str)
    if "aprs_passcode" in config and config["aprs_passcode"] is not None and config["aprs_passcode"] != "":
        try:
            int(config["aprs_passcode"])
        except (TypeError, ValueError):
            raise ConfigValidationError("Config key 'aprs_passcode' must be an integer")
    if "aprs_cache_max_size_mb" in config and config["aprs_cache_max_size_mb"] is not None and config["aprs_cache_max_size_mb"] != "":
        try:
            mb = float(config["aprs_cache_max_size_mb"])
            if not (100 <= mb <= 10000):
                raise ConfigValidationError("Config key 'aprs_cache_max_size_mb' must be 100-10000 (MB)")
        except (TypeError, ValueError):
            raise ConfigValidationError("Config key 'aprs_cache_max_size_mb' must be a number")
    if "aprs_cache_max_age_hours" in config and config["aprs_cache_max_age_hours"] is not None and config["aprs_cache_max_age_hours"] != "":
        try:
            h = float(config["aprs_cache_max_age_hours"])
            if not (1 <= h <= 8760):
                raise ConfigValidationError("Config key 'aprs_cache_max_age_hours' must be 1-8760")
        except (TypeError, ValueError):
            raise ConfigValidationError("Config key 'aprs_cache_max_age_hours' must be a number")
    if "aprs_debug" in config and config["aprs_debug"] is not None:
        if not isinstance(config["aprs_debug"], bool):
            raise ConfigValidationError("Config key 'aprs_debug' must be a boolean")
    if "update_mode" in config and config["update_mode"] is not None:
        _check_type("update_mode", config["update_mode"], str)
        if config["update_mode"] not in ("none", "notify", "auto"):
            raise ConfigValidationError("Config key 'update_mode' must be 'none', 'notify', or 'auto'")
    if "update_check_time" in config and config["update_check_time"] is not None:
        _check_type("update_check_time", config["update_check_time"], str)
    if "on_the_air_shortcut" in config and config["on_the_air_shortcut"] is not None:
        _check_type("on_the_air_shortcut", config["on_the_air_shortcut"], str)

    if "map_overlay_layout" in config and config["map_overlay_layout"] is not None:
        _check_type("map_overlay_layout", config["map_overlay_layout"], list)
        for i, item in enumerate(config["map_overlay_layout"]):
            if not isinstance(item, str):
                raise ConfigValidationError(f"Config key 'map_overlay_layout': item {i} must be a string")


def _migrate_desktop_config(config: Dict[str, Any]) -> bool:
    """Migrate legacy use_desktop/desktop_window to desktop_mode. Returns True if migrated."""
    migrated = False
    # Migrate old use_desktop + desktop_window → desktop_mode
    if "use_desktop" in config or "desktop_window" in config:
        use_desktop = config.pop("use_desktop", True)
        desktop_window = config.pop("desktop_window", False)
        if not use_desktop:
            config["desktop_mode"] = "headless"
        elif desktop_window:
            config["desktop_mode"] = "desktop"
        else:
            config["desktop_mode"] = "browser"
        migrated = True
        _log.debug("Migrated use_desktop=%s desktop_window=%s → desktop_mode=%s",
                   use_desktop, desktop_window, config["desktop_mode"])
    # Normalize desktop_mode: "none" → "headless"
    if config.get("desktop_mode") == "none":
        config["desktop_mode"] = "headless"
        migrated = True
    return migrated


class Config:
    """Manages GlanceRF configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(__file__).resolve().parent.parent.parent
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "glancerf_config.json"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file. Creates initial config if missing."""
        if not self.config_file.exists():
            _log.debug("Config file not found, creating at %s", self.config_file)
            self._config = deepcopy(_INITIAL_CONFIG)
            self.save()
            return
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            migrated = _migrate_desktop_config(self._config)
            _validate_config(self._config)
            if migrated:
                self.save()
            _log.debug("Config loaded from %s", self.config_file)
        except (json.JSONDecodeError, IOError) as e:
            raise IOError(f"Error loading config file {self.config_file}: {e}")

    def save(self) -> None:
        """Save configuration to file."""
        _validate_config(self._config)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            _log.debug("Config saved to %s", self.config_file)
        except IOError as e:
            raise IOError(f"Error saving config file {self.config_file}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._config[key] = value
        self.save()


_config_instance: Optional[Config] = None


def get_config(config_dir: Optional[Path] = None) -> Config:
    """Get the global config instance."""
    global _config_instance
    if _config_instance is None:
        if config_dir is None and os.environ.get("GLANCERF_PROJECT"):
            config_dir = Path(os.environ["GLANCERF_PROJECT"])
        _config_instance = Config(config_dir)
    return _config_instance
