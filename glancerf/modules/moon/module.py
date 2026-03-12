"""Moon phase (icon and illumination), moonrise and moonset for a location. Rise/set from SunCalc; phase is computed in the browser."""

from glancerf.modules.loader import load_assets

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "moon",
    "name": "Moon",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {"id": "show_phase", "label": "Show moon phase", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moonrise", "label": "Show moonrise", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
        {"id": "show_moonset", "label": "Show moonset", "type": "select", "options": ON_OFF_OPTIONS, "default": "1"},
    ],
}
