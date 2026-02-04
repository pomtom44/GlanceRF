"""Upcoming amateur radio contests from WA7BNM and other open sources. Choose data sources and how many entries to show; custom RSS/iCal URLs supported.

Built-in sources: WA7BNM (worldwide), SSA Sweden, RSGB UK. ARRL (contests.arrl.org) does not
publish a public RSS/iCal feed. Users can add custom RSS or iCal URLs via the Custom sources setting.
"""

# Source IDs used for enabled_sources setting; must match labels in contest_service.
CONTEST_SOURCE_IDS = ["WA7BNM", "WA7BNM iCal", "SSA (SE)", "SSA (SE) iCal", "RSGB (UK)"]

MODULE = {
    "id": "contests",
    "name": "Contests",
    "color": "#0d1117",
    "settings": [
        {"id": "max_entries", "label": "Max entries to show", "type": "number", "default": "20"},
        {
            "id": "enabled_sources",
            "label": "Data sources",
            "type": "source_checkboxes",
            "default": '["WA7BNM","WA7BNM iCal","SSA (SE)","SSA (SE) iCal","RSGB (UK)"]',
        },
        {
            "id": "custom_sources",
            "label": "Custom sources (RSS / iCal URLs)",
            "type": "custom_sources",
            "default": "[]",
        },
    ],
}
