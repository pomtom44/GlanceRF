"""Traditional analog clock face with hour, minute, and optional second hands."""

from glancerf.modules.loader import load_assets

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

TIMEZONE_OPTIONS = [
    {"value": "local", "label": "Local"},
    {"value": "UTC", "label": "UTC"},
]

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "analog_clock",
    "name": "Analog clock",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "show_seconds", "label": "Show seconds hand", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "timezone", "label": "Time zone", "type": "select", "options": TIMEZONE_OPTIONS, "default": "local"},
    ],
}
