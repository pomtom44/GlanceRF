"""Shows recent items from an RSS or Atom feed. You set the feed URL, max items, and refresh interval; the backend fetches and caches."""

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
