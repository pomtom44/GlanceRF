"""Sunrise and sunset times for a location (Open-Meteo). Optionally show moonrise and moonset. Uses Setup location if the cell field is blank. GPIO output: sun_up LED."""

from glancerf.modules.loader import load_assets

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "sun_times",
    "name": "Sunrise / Sunset",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {"id": "show_sunrise", "label": "Show sunrise", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_sunset", "label": "Show sunset", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moon", "label": "Show moonrise and moonset", "type": "select", "options": ON_OFF_OPTIONS, "default": "0"},
    ],
    "gpio": {
        "outputs": [{"id": "sun_up", "name": "Sun above horizon LED"}],
    },
    "cache_warmer": True,
}
