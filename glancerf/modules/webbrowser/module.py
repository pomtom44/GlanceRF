"""Embeds a web page: Direct (iframe) or Proxy (backend fetches, strips frame blockers)."""

MODULE = {
    "id": "webbrowser",
    "name": "Web Browser",
    "color": "#0d1117",
    "settings": [
        {"id": "url", "label": "URL", "type": "text", "default": ""},
        {"id": "mode", "label": "Display mode", "type": "select", "options": [
            {"value": "iframe", "label": "Direct (iframe)"},
            {"value": "proxy", "label": "Proxy"},
        ], "default": "iframe"},
    ],
}
