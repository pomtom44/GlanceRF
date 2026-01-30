"""Weather cell: current conditions from Open-Meteo."""

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

UNITS_OPTIONS = [
    {"value": "metric", "label": "Metric (C, km/h, hPa)"},
    {"value": "imperial", "label": "Imperial (F, mph, inHg)"},
]

MODULE = {
    "id": "weather",
    "name": "Weather",
    "color": "#0d1117",
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {"id": "units", "label": "Units", "type": "select", "options": UNITS_OPTIONS, "default": "metric"},
        {"id": "show_conditions", "label": "Show conditions (e.g. Cloudy)", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_temperature", "label": "Show temperature", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_feels_like", "label": "Show feels like", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_humidity", "label": "Show humidity", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_wind", "label": "Show wind", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_pressure", "label": "Show pressure", "type": "select", "options": ON_OFF_OPTIONS, "default": "0"},
    ],
}
