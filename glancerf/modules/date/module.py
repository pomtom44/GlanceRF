"""Standalone date cell: current date with optional format (DMY, MDY, YMD)."""

DATE_FORMAT_OPTIONS = [
    {"value": "dmy", "label": "Day Month Year (e.g. 27 Jan 2025)"},
    {"value": "mdy", "label": "Month Day Year (e.g. Jan 27, 2025)"},
    {"value": "ymd", "label": "Year Month Day (e.g. 2025 Jan 27)"},
]

MODULE = {
    "id": "date",
    "name": "Date",
    "color": "#0d1117",
    "settings": [
        {"id": "date_format", "label": "Date format", "type": "select", "options": DATE_FORMAT_OPTIONS, "default": "dmy"},
    ],
}
