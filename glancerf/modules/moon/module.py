"""Moon phase, moonrise and moonset for a given location. Uses Open-Meteo for rise/set; phase computed locally."""

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

MODULE = {
    "id": "moon",
    "name": "Moon",
    "color": "#0d1117",
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {"id": "show_phase", "label": "Show moon phase", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moonrise", "label": "Show moonrise", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moonset", "label": "Show moonset", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
    ],
}
