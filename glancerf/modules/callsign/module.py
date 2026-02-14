"""Shows your callsign, grid square (QTH), and an optional comment. Uses Setup callsign and location if you leave the cell fields blank."""

# Value is two chars: symbol table (/) or (\) + symbol character. APRS: /- = House QTH, /[ = Human.
QTH_MAP_ICON_OPTIONS = [
    {"value": "/-", "label": "House"},
    {"value": "/>", "label": "Car"},
    {"value": "/;", "label": "Portable"},
    {"value": "/#", "label": "DX"},
    {"value": "/&", "label": "Tent"},
    {"value": "/O", "label": "Satellite / balloon"},
    {"value": "/H", "label": "HF"},
    {"value": "/V", "label": "VHF"},
    {"value": "/\\", "label": "Digi"},
    {"value": "/?", "label": "Unknown"},
    {"value": "/[", "label": "Person"},
]

MODULE = {
    "id": "callsign",
    "name": "Callsign / QTH",
    "color": "#0d1117",
    "settings": [
        {"id": "callsign", "label": "Callsign", "type": "text", "default": ""},
        {"id": "grid", "label": "Grid square / QTH", "type": "text", "default": ""},
        {"id": "comment", "label": "Comment (optional)", "type": "text", "default": ""},
        {"type": "separator"},
        {"id": "on_the_air_shortcut", "label": "On The Air shortcut (optional)", "type": "text", "default": "", "placeholder": "e.g. F12"},
        {"type": "separator"},
        {
            "id": "show_qth_on_map",
            "label": "Show QTH on map",
            "type": "select",
            "options": [
                {"value": "0", "label": "Off"},
                {"value": "1", "label": "On"},
            ],
            "default": "0",
        },
        {
            "id": "qth_map_icon",
            "label": "Map icon",
            "type": "select",
            "options": QTH_MAP_ICON_OPTIONS,
            "default": "/-",
        },
    ],
    "gpio": {
        "inputs": [{"id": "on_the_air", "name": "On The Air"}],
    },
}


def _on_gpio_on_the_air(value: bool) -> None:
    """GPIO input: On The Air toggle. UI receives gpio_input WebSocket and shows/hides On The Air indicator."""
    pass


GPIO_INPUT_HANDLERS = {"on_the_air": _on_gpio_on_the_air}
