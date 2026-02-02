"""Basic world map with optional grid, terminator, sun/moon, and aurora overlays."""

GRID_OPTIONS = [
    {"value": "none", "label": "None"},
    {"value": "tropics", "label": "Tropics"},
    {"value": "latlong", "label": "Lat/Long"},
    {"value": "maidenhead", "label": "Maidenhead"},
]

ON_OFF_OPTIONS = [
    {"value": "1", "label": "On"},
    {"value": "0", "label": "Off"},
]

MODULE = {
    "id": "map",
    "name": "Map",
    "color": "#0d1117",
    "settings": [
        {
            "id": "map_style",
            "label": "Map source",
            "type": "select",
            "options": [
                {"value": "carto", "label": "Carto"},
                {"value": "opentopomap", "label": "OpenTopoMap"},
                {"value": "esri", "label": "Esri (satellite)"},
                {"value": "nasagibs", "label": "NASA GIBS"},
            ],
            "default": "carto",
        },
        {
            "id": "tile_style",
            "label": "Tile style",
            "type": "select",
            "parentSettingId": "map_style",
            "optionsBySource": {
                "carto": [
                    {"value": "carto_voyager", "label": "Voyager"},
                    {"value": "carto_positron", "label": "Positron"},
                    {"value": "carto_positron_nolabels", "label": "Positron, no labels"},
                    {"value": "carto_dark", "label": "Dark Matter"},
                    {"value": "carto_dark_nolabels", "label": "Dark Matter, no labels"},
                ],
                "opentopomap": [{"value": "otm_default", "label": "Default"}],
                "esri": [{"value": "esri_imagery", "label": "World Imagery"}],
                "nasagibs": [{"value": "nasa_nightlights", "label": "Night Lights"}],
            },
            "options": [
                {"value": "carto_voyager", "label": "Voyager"},
                {"value": "carto_positron", "label": "Positron"},
                {"value": "carto_positron_nolabels", "label": "Positron, no labels"},
                {"value": "carto_dark", "label": "Dark Matter"},
                {"value": "carto_dark_nolabels", "label": "Dark Matter, no labels"},
            ],
            "default": "carto_voyager",
        },
        {"id": "zoom", "label": "Zoom level", "type": "number", "min": 0, "max": 18, "default": "2"},
        {"id": "center", "label": "Map center (grid square or lat,lng)", "type": "text", "default": ""},
        {
            "id": "grid_style",
            "label": "Grid overlay",
            "type": "select",
            "options": GRID_OPTIONS,
            "default": "none",
        },
        {
            "id": "show_terminator",
            "label": "Day/night terminator line",
            "type": "select",
            "options": ON_OFF_OPTIONS,
            "default": "0",
        },
        {
            "id": "show_sun_moon",
            "label": "Sun and moon on map",
            "type": "select",
            "options": ON_OFF_OPTIONS,
            "default": "0",
        },
        {
            "id": "show_aurora",
            "label": "Aurora forecast overlay",
            "type": "select",
            "options": ON_OFF_OPTIONS,
            "default": "0",
        },
        {
            "id": "aurora_opacity",
            "label": "Aurora overlay opacity",
            "type": "range",
            "min": 0,
            "max": 100,
            "default": "50",
            "unit": "%",
        },
    ],
}
