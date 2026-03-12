"""
Read-only main page HTML template for GlanceRF.
Same structure as main, no interactions.
"""

from pathlib import Path

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_READONLY_TEMPLATE_PATH = _WEB_DIR / "templates" / "readonly" / "index.html"
_readonly_template_cache = None


def _get_readonly_template() -> str:
    """Load readonly page HTML template from file (cached)."""
    global _readonly_template_cache
    if _readonly_template_cache is None and _READONLY_TEMPLATE_PATH.is_file():
        _readonly_template_cache = _READONLY_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _readonly_template_cache or ""


def render_readonly_page(
    aspect_ratio_css: str,
    grid_css: str,
    grid_html: str,
    module_css: str = "",
    module_js: str = "",
    module_settings_json: str = "{}",
    modules_settings_schema_json: str = "{}",
    map_overlay_modules_json: str = "[]",
    map_overlay_layout_json: str = "[]",
    setup_callsign_json: str = '""',
    setup_location_json: str = '""',
    main_port: int = 8080,
    main_base_url: str = "http://127.0.0.1:8080",
    cache_bust: str = "",
) -> str:
    """Render the read-only clock page HTML (same structure as main, no interactions)."""
    module_css = module_css or ""
    module_js = module_js or ""
    template = _get_readonly_template()
    if not template:
        return f"<html><body><h1>GlanceRF (Read-Only)</h1><p>Template not found: {_READONLY_TEMPLATE_PATH}</p></body></html>"
    html = template.format(
        aspect_ratio_css=aspect_ratio_css,
        grid_css=grid_css,
        grid_html=grid_html,
        module_css=module_css,
        module_js=module_js,
        module_settings_json=module_settings_json,
        modules_settings_schema_json=modules_settings_schema_json,
        map_overlay_modules_json=map_overlay_modules_json,
        map_overlay_layout_json=map_overlay_layout_json,
        setup_callsign_json=setup_callsign_json,
        setup_location_json=setup_location_json,
        main_port=main_port,
        main_base_url=main_base_url.rstrip("/"),
    )
    if cache_bust:
        html = html.replace("__CACHE_BUST__", cache_bust)
    return html
