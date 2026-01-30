"""
Read-only main page HTML template for GlanceRF.
Loads template and assets from glancerf/web/ (templates/readonly/, static/css/, static/js/).
"""

from pathlib import Path

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_READONLY_TEMPLATE_PATH = _WEB_DIR / "templates" / "readonly" / "index.html"
_readonly_template_cache = None


def _get_readonly_template() -> str:
    """Load readonly page HTML template from file (cached)."""
    global _readonly_template_cache
    if _readonly_template_cache is None:
        _readonly_template_cache = _READONLY_TEMPLATE_PATH.read_text(encoding="utf-8")
    return _readonly_template_cache


def render_readonly_page(
    aspect_ratio_css: str,
    grid_css: str,
    grid_html: str,
    aspect_ratio: str,
    module_css: str = "",
    module_js: str = "",
    module_settings_json: str = "{}",
) -> str:
    """Render the read-only clock page HTML (no interactions)."""
    return _get_readonly_template().format(
        grid_css=grid_css,
        grid_html=grid_html,
        module_css=module_css,
        module_js=module_js,
        module_settings_json=module_settings_json,
    )
