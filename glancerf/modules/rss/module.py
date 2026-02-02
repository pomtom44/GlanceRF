"""Generic RSS feed cell. Displays recent items from a configurable feed URL (fetched via backend proxy)."""

MODULE = {
    "id": "rss",
    "name": "RSS Feed",
    "color": "#0d1117",
    "settings": [
        {"id": "rss_url", "label": "RSS feed URL", "type": "text", "default": ""},
        {"id": "max_items", "label": "Max items to show", "type": "number", "min": 1, "max": 50, "default": "10"},
        {"id": "refresh_min", "label": "Refresh interval (minutes)", "type": "number", "min": 1, "max": 120, "default": "15"},
    ],
}
