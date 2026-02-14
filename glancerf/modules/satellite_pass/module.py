"""Satellite list (CelesTrak) and current sub-satellite positions (SatChecker). Positions are shown as dots on the map when this module is on the layout."""

MODULE = {
    "id": "satellite_pass",
    "name": "Satellite positions",
    "color": "#0d1117",
    "settings": [
        {"id": "pass_location", "label": "Location", "type": "text", "default": "", "placeholder": "Grid square or lat,lon (uses system default if empty)"},
        {"id": "sat_view", "label": "View", "type": "select", "default": "pass", "options": [{"value": "pass", "label": "Next pass"}, {"value": "list", "label": "Pass list"}]},
        {"id": "sat_satellites", "label": "Satellites", "type": "satellite_table", "default": "{}"},
    ],
    "cache_warmer": True,
}
