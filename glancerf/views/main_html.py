"""
Main page HTML template for GlanceRF.
"""

from pathlib import Path

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_MAIN_TEMPLATE_PATH = _WEB_DIR / "templates" / "main" / "index.html"
_main_template_cache = None


def _get_main_template() -> str:
    """Load main page HTML template from file (cached)."""
    global _main_template_cache
    if _main_template_cache is None and _MAIN_TEMPLATE_PATH.is_file():
        _main_template_cache = _MAIN_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _main_template_cache or ""


def render_main_page(
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
    on_the_air_shortcut_json: str = '""',
    cache_bust: str = "",
) -> str:
    """Render the main clock page HTML."""
    module_css = module_css or ""
    module_js = module_js or ""
    template = _get_main_template()
    if not template:
        return f"<html><body><h1>GlanceRF</h1><p>Template not found: {_MAIN_TEMPLATE_PATH}</p></body></html>"
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
        on_the_air_shortcut_json=on_the_air_shortcut_json,
    )
    if cache_bust:
        html = html.replace("__CACHE_BUST__", cache_bust)
    return html
