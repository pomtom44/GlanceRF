"""
Main page HTML template for GlanceRF.
Loads template and assets from glancerf/web/ (templates/main/, static/css/, static/js/).
"""

from pathlib import Path

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_MAIN_TEMPLATE_PATH = _WEB_DIR / "templates" / "main" / "index.html"
_main_template_cache = None


def _get_main_template() -> str:
    """Load main page HTML template from file (cached)."""
    global _main_template_cache
    if _main_template_cache is None:
        _main_template_cache = _MAIN_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _main_template_cache


def render_main_page(
    aspect_ratio_css: str,
    grid_css: str,
    grid_html: str,
    aspect_ratio: str,
    module_css: str = "",
    module_js: str = "",
    module_settings_json: str = "{}",
    setup_callsign_json: str = '""',
    setup_location_json: str = '""',
) -> str:
    """Render the main clock page HTML with WebSocket and aspect-ratio support."""
    return _get_main_template().format(
        grid_css=grid_css,
        grid_html=grid_html,
        module_css=module_css,
        module_js=module_js,
        module_settings_json=module_settings_json,
        setup_callsign_json=setup_callsign_json,
        setup_location_json=setup_location_json,
    )
