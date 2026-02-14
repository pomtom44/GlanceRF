#!/usr/bin/env python3
"""
Tray icon helper for GlanceRF when running as a Windows service (headless).
"""
import sys
from pathlib import Path

_project_dir = Path(__file__).resolve().parent.parent.parent
try:
    _in_path = any(Path(p).resolve() == _project_dir for p in sys.path if p)
except (OSError, ValueError):
    _in_path = False
if not _in_path:
    sys.path.insert(0, str(_project_dir))

try:
    import pystray
    from PIL import Image
except ImportError:
    print("tray_helper requires: pip install pystray Pillow")
    sys.exit(1)

import webbrowser


def _get_port():
    try:
        from glancerf.config import get_config
        return int(get_config().get("port") or 8080)
    except Exception:
        return 8080


_TRAY_ICON_SIZE = (128, 128)


def _load_icon_image():
    project_dir = Path(__file__).resolve().parent.parent.parent
    logo_path = project_dir / "logos" / "logo.png"
    if not logo_path.is_file():
        logo_path = project_dir.parent / "logo.png"
    if logo_path.is_file():
        try:
            img = Image.open(logo_path).convert("RGBA")
            img = img.resize(_TRAY_ICON_SIZE, Image.LANCZOS)
            return img
        except Exception:
            pass
    return Image.new("RGBA", _TRAY_ICON_SIZE, (30, 60, 120, 255))


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
