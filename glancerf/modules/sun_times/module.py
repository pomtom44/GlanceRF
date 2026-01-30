"""Sunrise, sunset and optional moonrise/moonset for a given location. Uses Open-Meteo."""

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

MODULE = {
    "id": "sun_times",
    "name": "Sunrise / Sunset",
    "color": "#0d1117",
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {"id": "show_sunrise", "label": "Show sunrise", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_sunset", "label": "Show sunset", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moon", "label": "Show moonrise and moonset", "type": "select", "options": ON_OFF_OPTIONS, "default": "0"},
    ],
}
