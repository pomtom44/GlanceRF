"""Shows GPS stats when connected: position, time, altitude, speed, track, satellites."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "gps",
    "name": "GPS",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [],
}
