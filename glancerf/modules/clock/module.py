"""Clock cell: local, UTC, and optional third timezone."""

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

THIRD_TIMEZONE_OPTIONS = [
    {"value": "", "label": "None"},
    {"value": "UTC", "label": "UTC"},
    {"value": "Europe/London", "label": "London"},
    {"value": "Europe/Paris", "label": "Paris"},
    {"value": "America/New_York", "label": "New York"},
    {"value": "America/Chicago", "label": "Chicago"},
    {"value": "America/Denver", "label": "Denver"},
    {"value": "America/Los_Angeles", "label": "Los Angeles"},
    {"value": "Asia/Tokyo", "label": "Tokyo"},
    {"value": "Australia/Sydney", "label": "Sydney"},
    {"value": "Pacific/Auckland", "label": "Auckland"},
]

MODULE = {
    "id": "clock",
    "name": "Clock",
    "color": "#0d1117",
    "settings": [
        {"id": "show_date", "label": "Show date", "type": "select", "options": ON_OFF_OPTIONS, "default": "0"},
        {"id": "show_local", "label": "Local time", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_utc", "label": "UTC time", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "third_timezone", "label": "Third time (timezone or city)", "type": "select", "options": THIRD_TIMEZONE_OPTIONS, "default": ""},
    ],
}
