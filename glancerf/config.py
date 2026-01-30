"""
Configuration management for GlanceRF
Handles loading and saving settings to JSON file
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigValidationError(ValueError):
    """Raised when config structure or value types are invalid."""

    pass


def _default_layout(rows: int, cols: int) -> list:
    """Build a grid layout of empty cells."""
    return [["" for _ in range(cols)] for _ in range(rows)]


def resize_layout_to_grid(layout: list, grid_columns: int, grid_rows: int) -> list:
    """Resize layout to exactly grid_rows x grid_columns, preserving existing cells and filling with empty string."""
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


DEFAULT_CONFIG: Dict[str, Any] = {
    "port": 8080,
    "readonly_port": 8081,
    "use_desktop": True,
    "first_run": True,
    "max_grid_scale": 10,
    "grid_columns": 3,
    "grid_rows": 3,
    "aspect_ratio": "16:9",
    "orientation": "landscape",
    "layout": _default_layout(3, 3),
    "cell_spans": {},
    "module_settings": {},
}


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate config dict structure and types. Raises ConfigValidationError if invalid."""
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

    if "use_desktop" in config and config["use_desktop"] is not None:
        _check_type("use_desktop", config["use_desktop"], bool)

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
            raise ConfigValidationError(f"Config key 'orientation' must be 'landscape' or 'portrait', got {config['orientation']!r}")

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
        for key, val in config["cell_spans"].items():
            if not isinstance(key, str):
                raise ConfigValidationError(f"Config key 'cell_spans': key must be string, got {type(key).__name__}")
            if not isinstance(val, dict):
                raise ConfigValidationError(f"Config key 'cell_spans': value for {key!r} must be object")
            for span_key in ("colspan", "rowspan"):
                if span_key in val and val[span_key] is not None:
                    if not isinstance(val[span_key], int) or val[span_key] < 1:
                        raise ConfigValidationError(f"Config key 'cell_spans': {key!r}.{span_key} must be positive integer")

    if "module_settings" in config and config["module_settings"] is not None:
        _check_type("module_settings", config["module_settings"], dict)

    if "first_run" in config and config["first_run"] is not None:
        _check_type("first_run", config["first_run"], bool)

    if "telemetry_enabled" in config and config["telemetry_enabled"] is not None:
        _check_type("telemetry_enabled", config["telemetry_enabled"], bool)

    if "update_mode" in config and config["update_mode"] is not None:
        _check_type("update_mode", config["update_mode"], str)

    if "update_check_time" in config and config["update_check_time"] is not None:
        _check_type("update_check_time", config["update_check_time"], str)

    if "setup_callsign" in config and config["setup_callsign"] is not None:
        _check_type("setup_callsign", config["setup_callsign"], str)

    if "setup_location" in config and config["setup_location"] is not None:
        _check_type("setup_location", config["setup_location"], str)

    if "telemetry_guid" in config and config["telemetry_guid"] is not None:
        _check_type("telemetry_guid", config["telemetry_guid"], str)

    for key in ("desktop_window_width", "desktop_window_height", "desktop_window_x", "desktop_window_y"):
        if key in config and config[key] is not None:
            _check_type(key, config[key], int)

    if "log_level" in config and config["log_level"] is not None:
        _check_type("log_level", config["log_level"], str)
        if config["log_level"] not in ("default", "detailed", "verbose"):
            raise ConfigValidationError(
                f"Config key 'log_level' must be 'default', 'detailed', or 'verbose', got {config['log_level']!r}"
            )

    if "log_path" in config and config["log_path"] is not None:
        _check_type("log_path", config["log_path"], str)


class Config:
    """Manages GlanceRF configuration"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration
        
        Args:
            config_dir: Directory where config file will be stored.
                       If None, uses the directory where the script is located.
        """
        if config_dir is None:
            # Use the directory where this module is located
            config_dir = Path(__file__).parent.parent
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "glancerf_config.json"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file. If file does not exist, use default config and save it."""
        if not self.config_file.exists():
            self._config = deepcopy(DEFAULT_CONFIG)
            self.save()
            return
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise IOError(f"Error loading config file {self.config_file}: {e}")
        _validate_config(self._config)
    
    def save(self) -> None:
        """Save configuration to file"""
        _validate_config(self._config)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            raise IOError(f"Error saving config file {self.config_file}: {e}")
    
    def get(self, key: str) -> Any:
        """Get a configuration value (returns None if key doesn't exist)"""
        return self._config.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self._config[key] = value
        self.save()
    


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_dir: Optional[Path] = None) -> Config:
    """Get the global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_dir)
    return _config_instance
