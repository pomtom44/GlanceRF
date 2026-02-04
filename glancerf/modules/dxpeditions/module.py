"""Upcoming DXpeditions from NG3K Announced DX Operations (ADXO). Choose data sources and how many entries to show."""

# Source IDs used for enabled_sources setting; must match labels in dxpedition_service.
DXPEDITION_SOURCE_IDS = ["NG3K", "NG3K RSS", "DXCAL"]

MODULE = {
    "id": "dxpeditions",
    "name": "DXpeditions",
    "color": "#0d1117",
    "settings": [
        {"id": "max_entries", "label": "Max entries to show", "type": "number", "default": "15"},
        {
            "id": "enabled_sources",
            "label": "Data sources",
            "type": "source_checkboxes",
            "default": '["NG3K","NG3K RSS","DXCAL"]',
        },
    ],
}
