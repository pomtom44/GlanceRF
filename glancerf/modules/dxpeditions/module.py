"""Upcoming DXpeditions from NG3K Announced DX Operations (ADXO). Choose data sources and how many entries to show."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

# Source IDs used for enabled_sources setting; must match labels in dxpedition_service.
DXPEDITION_SOURCE_IDS = ["NG3K", "NG3K RSS", "DXCAL"]

MODULE = {
    "id": "dxpeditions",
    "name": "DXpeditions",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "max_entries", "label": "Max entries to show", "type": "number", "default": "15"},
        {"id": "refresh_hours", "label": "Refresh interval (hours)", "type": "number", "default": "6"},
        {
            "id": "enabled_sources",
            "label": "Data sources",
            "type": "source_checkboxes",
            "default": '["NG3K","NG3K RSS","DXCAL"]',
        },
        {"id": "scroll_toggle", "label": "Auto-scroll list", "type": "checkbox", "default": False},
    ],
    "gpio": {
        "outputs": [{"id": "alert", "name": "Active DXpedition LED"}],
    },
    "cache_warmer": True,
}
