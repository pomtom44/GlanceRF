"""
Desktop wrapper for GlanceRF using PyQt5 WebEngine
Opens a native window displaying the web interface
"""

import os
import sys

# Avoid WGL/OpenGL context failures on Windows (RDP, VMs, basic drivers).
# ANGLE uses Direct3D instead of OpenGL; set before Qt is loaded.
if sys.platform == "win32":
    os.environ.setdefault("QT_OPENGL", "angle")

# Reduce Chromium GPU/compositor errors (SharedImageManager, DisplayCompositor GL).
# Set before Qt WebEngine is used. Add "--disable-gpu" for full software rendering if needed.
_existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
if "--disable-gpu-sandbox" not in _existing and "--disable-gpu" not in _existing:
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (_existing + " --disable-gpu-sandbox").strip()

from PyQt5.QtCore import QUrl, QTimer, QPoint, QEvent, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView

from glancerf.config import get_config
from glancerf.aspect_ratio import calculate_dimensions, get_closest_aspect_ratio


class GlanceRFWindow(QMainWindow):
    """Main window for GlanceRF desktop application"""

    def __init__(self, port: int = 8080):
        super().__init__()
        self.port = port
        self.config = get_config()
        self.aspect_ratio = self.config.get("aspect_ratio") or "16:9"
        self.orientation = self.config.get("orientation") or "landscape"
        self.initial_position_set = False
        self._resize_save_timer = None
        self._was_maximized_before_fullscreen = False
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowCloseButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
        )
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(f"http://localhost:{self.port}?desktop=true"))
        self.browser.page().settings().setAttribute(
            self.browser.page().settings().WebAttribute.JavascriptEnabled, True
        )
        self.browser.installEventFilter(self)
        self.browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.browser.setMinimumSize(0, 0)
        self.browser.setMaximumSize(16777215, 16777215)
        self.setCentralWidget(self.browser)
        self.setWindowTitle("GlanceRF")

        f11_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        f11_shortcut.setContext(Qt.ApplicationShortcut)
        f11_shortcut.activated.connect(self._toggle_fullscreen)

        screen = QApplication.primaryScreen().geometry()
        max_width = screen.width() - 100
        max_height = screen.height() - 100

        saved_w = self.config.get("desktop_window_width")
        saved_h = self.config.get("desktop_window_height")
        if isinstance(saved_w, (int, float)) and isinstance(saved_h, (int, float)) and saved_w > 0 and saved_h > 0:
            width = int(saved_w)
            height = int(saved_h)
            saved_x = self.config.get("desktop_window_x")
            saved_y = self.config.get("desktop_window_y")
            if isinstance(saved_x, (int, float)) and isinstance(saved_y, (int, float)):
                x = int(saved_x)
                y = int(saved_y)
            else:
                x = (screen.width() - width) // 2
                y = (screen.height() - height) // 2
        else:
            width, height = calculate_dimensions(
                self.aspect_ratio, max_width, max_height, self.orientation
            )
            x = (screen.width() - width) // 2
            y = (screen.height() - height) // 2

        self.setGeometry(x, y, width, height)
        self.initial_position_set = True

        self.setMinimumSize(400, 300)
        self.setMaximumSize(16777215, 16777215)
        self.show()

        # Re-apply max size after show; some platforms apply limits at show time
        self.setMaximumSize(16777215, 16777215)
        self.browser.setMaximumSize(16777215, 16777215)

        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.check_config_changes)
        self.config_timer.start(2000)

    def eventFilter(self, obj, event):
        """Capture F11 for fullscreen toggle even when browser has focus."""
        if obj is self.browser and event.type() == QEvent.KeyPress and event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
            return True
        return super().eventFilter(obj, event)

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and normal window. F11."""
        if self.isFullScreen():
            self.showNormal()
            if self._was_maximized_before_fullscreen:
                self.showMaximized()
        else:
            self._was_maximized_before_fullscreen = self.isMaximized()
            self.showFullScreen()

    def _get_height_ratio(self) -> float:
        """Get height/width ratio for current aspect ratio"""
        from glancerf.aspect_ratio import get_aspect_ratio_value
        ratio = get_aspect_ratio_value(self.aspect_ratio)
        if ratio:
            return ratio[1] / ratio[0]
        return 9 / 16

    def _save_window_geometry_and_ratio(self):
        """Save current window size and position; update aspect_ratio to closest match."""
        geo = self.geometry()
        self.config.set("desktop_window_width", geo.width())
        self.config.set("desktop_window_height", geo.height())
        self.config.set("desktop_window_x", geo.x())
        self.config.set("desktop_window_y", geo.y())
        closest = get_closest_aspect_ratio(geo.width(), geo.height())
        if closest != self.aspect_ratio:
            self.aspect_ratio = closest
            self.config.set("aspect_ratio", closest)

    def resizeEvent(self, event):
        """On resize, schedule save of size and closest aspect ratio."""
        super().resizeEvent(event)
        if self._resize_save_timer is not None:
            self._resize_save_timer.stop()
        self._resize_save_timer = QTimer(self)
        self._resize_save_timer.setSingleShot(True)
        self._resize_save_timer.timeout.connect(self._save_window_geometry_and_ratio)
        self._resize_save_timer.start(500)

    def moveEvent(self, event):
        """On move, schedule save of position."""
        super().moveEvent(event)
        if self._resize_save_timer is not None:
            self._resize_save_timer.stop()
        self._resize_save_timer = QTimer(self)
        self._resize_save_timer.setSingleShot(True)
        self._resize_save_timer.timeout.connect(self._save_window_geometry_and_ratio)
        self._resize_save_timer.start(500)
    
    def check_config_changes(self):
        """Check for config changes and reload if any settings changed"""
        try:
            new_config = get_config()
            new_aspect_ratio = new_config.get("aspect_ratio") or "16:9"
            new_grid_columns = new_config.get("grid_columns")
            new_grid_rows = new_config.get("grid_rows")

            if new_grid_columns is None or new_grid_rows is None:
                return

            config_changed = False
            if new_aspect_ratio != self.aspect_ratio:
                self.aspect_ratio = new_aspect_ratio
                self._resize_to_aspect_ratio()
                config_changed = True

            current_grid_columns = self.config.get("grid_columns")
            current_grid_rows = self.config.get("grid_rows")
            if current_grid_columns is not None and current_grid_rows is not None:
                if new_grid_columns != current_grid_columns or new_grid_rows != current_grid_rows:
                    config_changed = True

            if config_changed:
                self.config = new_config
                self.browser.reload()
        except Exception:
            pass

    def _resize_to_aspect_ratio(self):
        """Resize window to match current aspect ratio; save new size to config."""
        geo = self.geometry()
        x, y = geo.x(), geo.y()
        width = geo.width()
        height_ratio = self._get_height_ratio()
        new_height = int(width * height_ratio)

        screen = QApplication.screenAt(self.mapToGlobal(self.rect().center()))
        if screen is None:
            screen = QApplication.primaryScreen()
        sg = screen.geometry()
        screen_w = sg.width()
        screen_h = sg.height()
        max_w = screen_w - 100
        max_h = screen_h - 100

        if new_height > max_h:
            new_height = max_h
            width = int(new_height / height_ratio)
            if width > max_w:
                width = max_w
                new_height = int(width * height_ratio)

        self.setGeometry(x, y, width, new_height)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(16777215, 16777215)
        self.browser.setMaximumSize(16777215, 16777215)
        self._save_window_geometry_and_ratio()

    def closeEvent(self, event):
        """Handle window close event"""
        # Allow normal close
        event.accept()


def run_desktop(port: int = 8080, server_thread=None):
    """
    Run GlanceRF in desktop mode
    
    Args:
        port: Port number for the web server
        server_thread: Thread running the server (optional)
    """
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("GlanceRF")
    
    # Create and show main window
    window = GlanceRFWindow(port)
    
    # Run the application
    # This blocks until the window is closed
    exit_code = app.exec_()
    sys.exit(exit_code)


def run_virtual_desktop(port: int = 8080):
    """
    Run GlanceRF as virtual desktop in background
    Web browsers will mirror this virtual desktop
    
    Args:
        port: Port number for the web server
    """
    # Create QApplication (headless - no window shown)
    app = QApplication(sys.argv)
    app.setApplicationName("GlanceRF (Virtual)")
    
    # Create window but don't show it
    window = GlanceRFWindow(port)
    window.hide()  # Hide the window - it runs in background
    
    # Run the application (keeps virtual desktop alive)
    app.exec_()
