"""
Centralized menu HTML for GlanceRF.
V1 layout: Setup, Layout, Modules, Updates, Restart services, GPIO, + in-menu updates section.
"""

from glancerf.gpio import get_gpio_menu_html


def get_menu_html(base_url: str = "") -> str:
    """
    Return the full menu panel HTML (inner content of glancerf-menu-panel).
    base_url: prefix for links (e.g. "" for main server, or full base for readonly).
    """
    prefix = base_url.rstrip("/") if base_url else ""
    gpio_html = get_gpio_menu_html()
    return f"""
            <h2>Menu</h2>
            <ul class="glancerf-menu-list">
                <li><a href="{prefix}/setup">Setup</a></li>
                <li><a href="{prefix}/layout">Layout & Config editor</a></li>
                <li><a href="{prefix}/map-modules">Map only modules</a></li>
                <li><a href="{prefix}/modules">Modules list</a></li>
                <li><a href="{prefix}/updates">Updates</a></li>
                <li><button type="button" class="menu-link" id="menu-restart-services">Restart services</button></li>
                {gpio_html}
            </ul>
"""
