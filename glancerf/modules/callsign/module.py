"""Shows your callsign, grid square (QTH), and an optional comment. Uses Setup callsign and location if you leave the cell fields blank."""

MODULE = {
    "id": "callsign",
    "name": "Callsign / QTH",
    "color": "#0d1117",
    "settings": [
        {"id": "callsign", "label": "Callsign", "type": "text", "default": ""},
        {"id": "grid", "label": "Grid square / QTH", "type": "text", "default": ""},
        {"id": "comment", "label": "Comment (optional)", "type": "text", "default": ""},
    ],
}
