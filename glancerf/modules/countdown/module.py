"""Countdown to a target date and time, or stopwatch showing elapsed time from a start. Optional label; updates every second."""

MODE_OPTIONS = [
    {"value": "countdown", "label": "Countdown (to target)"},
    {"value": "stopwatch", "label": "Stopwatch (elapsed from start)"},
]

MODULE = {
    "id": "countdown",
    "name": "Countdown / Stopwatch",
    "color": "#0d1117",
    "settings": [
        {"id": "mode", "label": "Mode", "type": "select", "options": MODE_OPTIONS, "default": "countdown"},
        {"id": "date", "label": "Date (YYYY-MM-DD)", "type": "text", "default": ""},
        {"id": "time", "label": "Time (optional, HH:MM or HH:MM:SS)", "type": "text", "default": ""},
        {"id": "label", "label": "Label (optional)", "type": "text", "default": ""},
    ],
}
