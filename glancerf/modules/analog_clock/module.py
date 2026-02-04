"""Traditional analog clock face with hour, minute, and optional second hands. Choose local or UTC time zone."""

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

TIMEZONE_OPTIONS = [
    {"value": "local", "label": "Local"},
    {"value": "UTC", "label": "UTC"},
]

MODULE = {
    "id": "analog_clock",
    "name": "Analog clock",
    "color": "#0d1117",
    "settings": [
        {"id": "show_seconds", "label": "Show seconds hand", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "timezone", "label": "Time zone", "type": "select", "options": TIMEZONE_OPTIONS, "default": "local"},
    ],
}
