"""Shows On The Air (red) or Off The Air (grey). Toggle via GPIO or keyboard shortcut. Shares On The Air config with the Callsign module."""

MODULE = {
    "id": "on_the_air",
    "name": "On The Air",
    "color": "#0d1117",
    "settings": [
        {"id": "on_the_air_shortcut", "label": "Keyboard shortcut (optional)", "type": "text", "default": "", "placeholder": "e.g. F12"},
    ],
    "gpio": {
        "inputs": [{"id": "on_the_air", "name": "On The Air"}],
    },
}


def _on_gpio_on_the_air(value: bool) -> None:
    """GPIO input: On The Air toggle. UI receives gpio_input WebSocket and updates display."""
    pass


GPIO_INPUT_HANDLERS = {"on_the_air": _on_gpio_on_the_air}
