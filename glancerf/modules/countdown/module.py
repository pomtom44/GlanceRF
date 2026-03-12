"""Countdown to a target date and time, or stopwatch showing elapsed time from a start."""

from glancerf.modules.loader import load_assets

MODE_OPTIONS = [
    {"value": "countdown", "label": "Countdown (to target)"},
    {"value": "stopwatch", "label": "Stopwatch (elapsed from start)"},
    {"value": "live_stopwatch", "label": "Live stopwatch (start/stop + reset hotkeys)"},
]

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "countdown",
    "name": "Countdown / Stopwatch",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "mode", "label": "Mode", "type": "select", "options": MODE_OPTIONS, "default": "countdown"},
        {"id": "date", "label": "Date (YYYY-MM-DD)", "type": "text", "default": ""},
        {"id": "time", "label": "Time (optional, HH:MM or HH:MM:SS)", "type": "text", "default": ""},
        {"id": "label", "label": "Label (optional)", "type": "text", "default": ""},
        {"id": "start_stop_shortcut", "label": "Start/Stop hotkey (live stopwatch)", "type": "text", "default": "", "placeholder": "e.g. Space or s"},
        {"id": "reset_shortcut", "label": "Reset hotkey (live stopwatch)", "type": "text", "default": "", "placeholder": "e.g. r"},
    ],
    "gpio": {
        "inputs": [
            {"id": "start_stop", "name": "Start/Stop"},
            {"id": "reset", "name": "Reset"},
        ],
        "outputs": [{"id": "running", "name": "Running LED"}],
    },
}


def _on_gpio_start_stop(value: bool) -> None:
    """GPIO input: Start/Stop. Broadcast to browsers so countdown UI can start/stop timer."""
    pass


def _on_gpio_reset(value: bool) -> None:
    """GPIO input: Reset. Broadcast to browsers so countdown UI can reset."""
    pass


GPIO_INPUT_HANDLERS = {"start_stop": _on_gpio_start_stop, "reset": _on_gpio_reset}
