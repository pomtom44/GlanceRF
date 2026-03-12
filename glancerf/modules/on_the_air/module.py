"""Shows On The Air (red) or Off The Air (grey). Toggle via GPIO or keyboard shortcut."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "on_the_air",
    "name": "On The Air",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
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
