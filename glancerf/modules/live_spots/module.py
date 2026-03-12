"""Live spots from RBN, PSK Reporter, DX cluster, etc. List or table view with band colors."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "live_spots",
    "name": "Live spots",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {
            "id": "filter_mode",
            "label": "Filter",
            "type": "select",
            "options": [
                {"value": "received", "label": "Received by"},
                {"value": "sent", "label": "Sent by"},
            ],
            "default": "received",
        },
        {
            "id": "callsign_or_grid",
            "label": "Callsign or grid square",
            "type": "text",
            "default": "",
            "placeholder": "e.g. G4ABC or IO91",
        },
        {
            "id": "display_mode",
            "label": "Show as",
            "type": "select",
            "options": [
                {"value": "list", "label": "List"},
                {"value": "table", "label": "Table"},
            ],
            "default": "list",
        },
        {
            "id": "age_mins",
            "label": "Max age (minutes)",
            "type": "number",
            "min": 1,
            "max": 1440,
            "default": "60",
            "placeholder": "table view",
        },
        {"id": "band_160", "label": "Show 160m", "type": "checkbox", "default": True},
        {"id": "band_160_color", "label": "Line color", "type": "color", "default": "#8b4513"},
        {"id": "band_80", "label": "Show 80m", "type": "checkbox", "default": True},
        {"id": "band_80_color", "label": "Line color", "type": "color", "default": "#4682b4"},
        {"id": "band_60", "label": "Show 60m", "type": "checkbox", "default": True},
        {"id": "band_60_color", "label": "Line color", "type": "color", "default": "#20b2aa"},
        {"id": "band_40", "label": "Show 40m", "type": "checkbox", "default": True},
        {"id": "band_40_color", "label": "Line color", "type": "color", "default": "#00ff00"},
        {"id": "band_30", "label": "Show 30m", "type": "checkbox", "default": True},
        {"id": "band_30_color", "label": "Line color", "type": "color", "default": "#9acd32"},
        {"id": "band_20", "label": "Show 20m", "type": "checkbox", "default": True},
        {"id": "band_20_color", "label": "Line color", "type": "color", "default": "#ffd700"},
        {"id": "band_17", "label": "Show 17m", "type": "checkbox", "default": True},
        {"id": "band_17_color", "label": "Line color", "type": "color", "default": "#ff8c00"},
        {"id": "band_15", "label": "Show 15m", "type": "checkbox", "default": True},
        {"id": "band_15_color", "label": "Line color", "type": "color", "default": "#f08080"},
        {"id": "band_12", "label": "Show 12m", "type": "checkbox", "default": True},
        {"id": "band_12_color", "label": "Line color", "type": "color", "default": "#da70d6"},
        {"id": "band_10", "label": "Show 10m", "type": "checkbox", "default": True},
        {"id": "band_10_color", "label": "Line color", "type": "color", "default": "#9370db"},
        {"id": "band_6", "label": "Show 6m", "type": "checkbox", "default": True},
        {"id": "band_6_color", "label": "Line color", "type": "color", "default": "#00ced1"},
        {"id": "band_2", "label": "Show 2m", "type": "checkbox", "default": True},
        {"id": "band_2_color", "label": "Line color", "type": "color", "default": "#e0e0e0"},
    ],
    "cache_warmer": True,
}
