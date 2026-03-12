"""Displays the current date (weekday, day, month, year) in your choice of format."""

from glancerf.modules.loader import load_assets

DATE_FORMAT_OPTIONS = [
    {"value": "dmy", "label": "Day Month Year (e.g. 27 Jan 2025)"},
    {"value": "mdy", "label": "Month Day Year (e.g. Jan 27, 2025)"},
    {"value": "ymd", "label": "Year Month Day (e.g. 2025 Jan 27)"},
]

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "date",
    "name": "Date",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "date_format", "label": "Date format", "type": "select", "options": DATE_FORMAT_OPTIONS, "default": "dmy"},
    ],
}
