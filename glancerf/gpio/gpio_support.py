"""
GPIO availability and pin list for GlanceRF.
Detects Raspberry Pi / RPi.GPIO and provides pin list and menu HTML.
"""

from pathlib import Path
from typing import List, Optional, Tuple

# Common BCM GPIO pins on 40-pin header (general-purpose; exclude 0/1 UART, 28-31, etc.)
_DEFAULT_BCM_PINS: List[Tuple[int, str]] = [
    (2, "GPIO 2"), (3, "GPIO 3"), (4, "GPIO 4"), (5, "GPIO 5"),
    (6, "GPIO 6"), (7, "GPIO 7"), (8, "GPIO 8"), (9, "GPIO 9"),
    (10, "GPIO 10"), (11, "GPIO 11"), (12, "GPIO 12"), (13, "GPIO 13"),
    (14, "GPIO 14"), (15, "GPIO 15"), (16, "GPIO 16"), (17, "GPIO 17"),
    (18, "GPIO 18"), (19, "GPIO 19"), (20, "GPIO 20"), (21, "GPIO 21"),
    (22, "GPIO 22"), (23, "GPIO 23"), (24, "GPIO 24"), (25, "GPIO 25"),
    (26, "GPIO 26"), (27, "GPIO 27"),
]

_gpio_available_cached: Optional[bool] = None


def _detect_gpio_available() -> bool:
    """Check if RPi.GPIO can be imported (Raspberry Pi)."""
    try:
        import RPi.GPIO as _  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        model = Path("/proc/device-tree/model").read_text().strip()
        if "Raspberry Pi" in model:
            return False
    except Exception:
        pass
    return False


def is_gpio_available() -> bool:
    """Return True if GPIO (RPi.GPIO) is available on this system."""
    global _gpio_available_cached
    if _gpio_available_cached is None:
        _gpio_available_cached = _detect_gpio_available()
    return _gpio_available_cached


def clear_gpio_availability_cache() -> None:
    """Clear the cached GPIO availability so next is_gpio_available() re-checks."""
    global _gpio_available_cached
    _gpio_available_cached = None


def get_available_pins() -> List[Tuple[int, str]]:
    """Return list of (BCM number, label) for pins that can be assigned."""
    if not is_gpio_available():
        return []
    return list(_DEFAULT_BCM_PINS)


def get_gpio_menu_html() -> str:
    """Return HTML fragment for the menu: link to /gpio if available, else empty string."""
    if not is_gpio_available():
        return ""
    return '\n                <li><a href="/gpio">GPIO</a></li>'
