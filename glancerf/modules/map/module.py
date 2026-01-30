"""Basic world map."""

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
    ],
}
