#!/usr/bin/env python3
"""Tray icon helper for GlanceRF when running as a Windows service (headless)."""
import json
import sys
import webbrowser
from pathlib import Path

_project_dir = Path(__file__).resolve().parent.parent.parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

try:
    import pystray
    from PIL import Image
except ImportError:
    print("tray_helper requires: pip install pystray Pillow")
    sys.exit(1)


def _get_port():
    config_path = _project_dir / "glancerf_config.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return int(json.load(f).get("port", 8080))
        except Exception:
            pass
    return 8080


def _load_icon_image():
    logo_path = _project_dir / "logos" / "logo.png"
    if not logo_path.is_file():
        logo_path = _project_dir.parent / "logo.png"
    if logo_path.is_file():
        try:
            img = Image.open(logo_path).convert("RGBA")
            return img.resize((128, 128), Image.LANCZOS)
        except Exception:
            pass
    return Image.new("RGBA", (128, 128), (30, 60, 120, 255))


def main():
    port = _get_port()
    url = "http://localhost:%s" % port

    def open_browser(icon=None, item=None):
        webbrowser.open(url)

    def quit_app(icon=None, item=None):
        icon.stop()

    icon_image = _load_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Open GlanceRF", open_browser, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("GlanceRF", icon=icon_image, title="GlanceRF - Click to open in browser", menu=menu)
    icon.run()


if __name__ == "__main__":
    main()
