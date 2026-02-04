"""HamClock-style satellite pass: sky dome with horizon and elevation rings, next pass path, current position, rise/set times. Uses CelesTrak TLEs and Setup location if the cell location is blank."""

MODULE = {
    "id": "satellite_pass",
    "name": "Satellite pass",
    "color": "#0d1117",
    "settings": [
        {"id": "location", "label": "Grid square or lat,lng", "type": "text", "default": ""},
        {
            "id": "selected_satellites",
            "label": "Satellites to track",
            "type": "satellite_checkboxes",
            "default": "[]",
        },
    ],
}
