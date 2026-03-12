"""Embeds a web page: Direct (iframe) or Proxy (backend fetches, strips frame blockers)."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "webbrowser",
    "name": "Web Browser",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "url", "label": "URL", "type": "text", "default": ""},
        {"id": "mode", "label": "Display mode", "type": "select", "options": [
            {"value": "iframe", "label": "Direct (iframe)"},
            {"value": "proxy", "label": "Proxy"},
        ], "default": "iframe"},
    ],
}
