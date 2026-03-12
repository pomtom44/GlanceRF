"""APRS station list from local cache. Shows last-updated nodes; can appear on the map when in map overlay layout.

Data from config_dir/cache/aprs.db (populated by APRS-IS ingest or similar). No live APRS-IS connection from this module."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "aprs",
    "name": "APRS stations",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "max_entries", "label": "Max entries to show", "type": "number", "default": "30"},
        {"id": "hours", "label": "Time window (hours)", "type": "number", "default": "6"},
        {"id": "aprs_filter", "label": "Filter (p/PREFIX or p/P1/P2)", "type": "text", "default": "", "placeholder": "e.g. p/W1 p/VE", "hintUrl": "https://www.aprs-is.net/javAPRSFilter.aspx", "hintText": "APRS-IS filter guide"},
        {"id": "aprs_display_mode", "label": "Map display", "type": "select", "options": [{"value": "dots", "label": "Dots"}, {"value": "icons", "label": "Icons"}], "default": "dots"},
    ],
    "cache_warmer": True,
}
