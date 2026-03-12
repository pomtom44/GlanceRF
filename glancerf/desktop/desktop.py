"""
Desktop wrapper for GlanceRF using PyQt5 WebEngine.
Opens a native window displaying the web interface.

For slow startup in Windows Sandbox / VMs: set GLANCERF_DISABLE_GPU=1 before launch
to skip GPU init (Chromium will use software rendering).
"""

import os
import sys
import webbrowser
from pathlib import Path

# Avoid WGL/OpenGL context failures on Windows (RDP, VMs, basic drivers)
if sys.platform == "win32":
    os.environ.setdefault("QT_OPENGL", "angle")

_existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
_flags = [_existing] if _existing else []
if "--disable-gpu-sandbox" not in _existing and "--disable-gpu" not in _existing:
    _flags.append("--disable-gpu-sandbox")
if os.environ.get("GLANCERF_DISABLE_GPU", "").strip() in ("1", "true", "yes"):
    _flags.append("--disable-gpu")
# Windows Sandbox: Chromium's sandbox conflicts with host sandbox; --no-sandbox allows WebEngine to run
if sys.platform == "win32":
    _user = os.environ.get("USERNAME", "").strip()
    _comp = (os.environ.get("COMPUTERNAME") or "").upper()
    if _user == "WDAGUtilityAccount" or "SANDBOX" in _comp or "WINSANDBOX" in _comp:
        if "--no-sandbox" not in _existing:
            _flags.append("--no-sandbox")
        if "--disable-gpu" not in _existing:
            _flags.append("--disable-gpu")
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(f for f in _flags if f).strip()

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def _get_logo_path():
    """Return absolute path to logo: prefer .ico on Windows for taskbar, else .png."""
    project_logos = _PROJECT_DIR / "logos"
    workspace_root = _PROJECT_DIR.parent
    if sys.platform == "win32":
        for name in ("logo.ico", "logo.png"):
            p = (project_logos / name).resolve()
            if p.is_file():
                return p
        for p in (workspace_root / "logo.ico", workspace_root / "logo.png"):
            if p.resolve().is_file():
                return p.resolve()
        return None
    for p in (project_logos / "logo.png", workspace_root / "logo.png"):
        if p.resolve().is_file():
            return p.resolve()
    return None


def _app_icon():
    """Return QIcon for logo if present, else None (taskbar/window icon)."""
    try:
        from PyQt5.QtGui import QIcon
        path = _get_logo_path()
        if path is not None:
            return QIcon(str(path))
    except ImportError:
        pass
    return None


def run_desktop(port: int = 8080, server_thread=None, splash_root=None):
    """Run GlanceRF in desktop window mode."""
    try:
        from PyQt5.QtCore import QCoreApplication, QObject, QTimer, QUrl, Qt, QEvent
        from PyQt5.QtGui import QFont, QIcon
        from PyQt5.QtWidgets import (
            QApplication,
            QMainWindow,
            QShortcut,
            QStackedWidget,
            QWidget,
            QVBoxLayout,
            QLabel,
            QProgressBar,
            QPushButton,
            QSizePolicy,
        QStyle,
        )
    except ImportError:
        # PyQt5 missing - open browser as fallback (no desktop window possible)
        webbrowser.open(f"http://127.0.0.1:{port}")
        return

    from glancerf.config import get_config
    from glancerf.utils import calculate_dimensions, get_closest_aspect_ratio

    # Required for Qt WebEngine: share OpenGL contexts before QApplication
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setApplicationName("GlanceRF")
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GlanceRF.Desktop.1")
        except (AttributeError, OSError):
            pass

    win = QMainWindow()
    win.setWindowTitle("GlanceRF")
    win.setWindowFlags(
        Qt.Window
        | Qt.WindowCloseButtonHint
        | Qt.WindowMinimizeButtonHint
        | Qt.WindowMaximizeButtonHint
    )

    # Loading widget
    loading = QWidget()
    loading.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
    layout = QVBoxLayout(loading)
    layout.setAlignment(Qt.AlignCenter)
    layout.setSpacing(24)
    label = QLabel("Starting GlanceRF...")
    label.setStyleSheet("color: #c9d1d9; font-size: 18px;")
    try:
        font = QFont("Segoe UI", 18)
        if font.exactMatch():
            label.setFont(font)
    except Exception:
        pass
    layout.addWidget(label, 0, Qt.AlignHCenter)
    bar = QProgressBar()
    bar.setRange(0, 0)
    bar.setFixedWidth(200)
    bar.setStyleSheet(
        "QProgressBar { border: 1px solid #30363d; border-radius: 4px; background: #161b22; }"
        "QProgressBar::chunk { background: #238636; border-radius: 3px; }"
    )
    layout.addWidget(bar, 0, Qt.AlignHCenter)
    retry_btn = QPushButton("Retry")
    retry_btn.setStyleSheet("color: #0f0; background: #21262d; padding: 8px 24px;")
    retry_btn.setVisible(False)
    layout.addWidget(retry_btn, 0, Qt.AlignHCenter)

    stack = QStackedWidget()
    stack.addWidget(loading)
    win.setCentralWidget(stack)
    win.setMinimumSize(400, 300)

    # Icon
    if icon is not None:
        win.setWindowIcon(icon)

    # F11 fullscreen shortcut
    f11_shortcut = QShortcut(Qt.Key_F11, win)
    f11_shortcut.setContext(Qt.ApplicationShortcut)

    # Geometry from config
    config = get_config()
    aspect_ratio = config.get("aspect_ratio") or "16:9"
    orientation = config.get("orientation") or "landscape"
    screen = QApplication.primaryScreen().geometry()
    max_width = screen.width() - 100
    max_height = screen.height() - 100
    saved_w = config.get("desktop_window_width")
    saved_h = config.get("desktop_window_height")
    if isinstance(saved_w, (int, float)) and isinstance(saved_h, (int, float)) and saved_w > 0 and saved_h > 0:
        width = int(saved_w)
        height = int(saved_h)
        saved_x = config.get("desktop_window_x")
        saved_y = config.get("desktop_window_y")
        if isinstance(saved_x, (int, float)) and isinstance(saved_y, (int, float)):
            x, y = int(saved_x), int(saved_y)
        else:
            x = (screen.width() - width) // 2
            y = (screen.height() - height) // 2
    else:
        width, height = calculate_dimensions(aspect_ratio, max_width, max_height, orientation)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
    win.setGeometry(x, y, width, height)

    _resize_save_timer = None
    _was_maximized_before_fullscreen = False
    browser_ref = [None]
    aspect_ratio_ref = [aspect_ratio]

    def _save_window_geometry():
        geo = win.geometry()
        config.set("desktop_window_width", geo.width())
        config.set("desktop_window_height", geo.height())
        config.set("desktop_window_x", geo.x())
        config.set("desktop_window_y", geo.y())
        closest = get_closest_aspect_ratio(geo.width(), geo.height())
        if closest != aspect_ratio_ref[0]:
            aspect_ratio_ref[0] = closest
            config.set("aspect_ratio", closest)

    def _debounced_save_geometry():
        nonlocal _resize_save_timer
        if _resize_save_timer is not None:
            _resize_save_timer.stop()
        _resize_save_timer = QTimer(win)
        _resize_save_timer.setSingleShot(True)
        _resize_save_timer.timeout.connect(_save_window_geometry)
        _resize_save_timer.start(500)

    def _toggle_fullscreen():
        nonlocal _was_maximized_before_fullscreen
        if win.isFullScreen():
            win.showNormal()
            if _was_maximized_before_fullscreen:
                win.showMaximized()
        else:
            _was_maximized_before_fullscreen = win.isMaximized()
            win.showFullScreen()

    f11_shortcut.activated.connect(_toggle_fullscreen)

    def resize_event(event):
        QMainWindow.resizeEvent(win, event)
        _debounced_save_geometry()

    def move_event(event):
        QMainWindow.moveEvent(win, event)
        _debounced_save_geometry()

    win.resizeEvent = resize_event
    win.moveEvent = move_event

    def check_config_changes():
        try:
            new_cfg = get_config()
            new_ar = new_cfg.get("aspect_ratio") or "16:9"
            new_cols = new_cfg.get("grid_columns")
            new_rows = new_cfg.get("grid_rows")
            if new_cols is None or new_rows is None:
                return
            changed = False
            if new_ar != aspect_ratio_ref[0]:
                aspect_ratio_ref[0] = new_ar
                config.set("aspect_ratio", new_ar)
                changed = True
            cur_cols, cur_rows = config.get("grid_columns"), config.get("grid_rows")
            if cur_cols is not None and cur_rows is not None:
                if new_cols != cur_cols or new_rows != cur_rows:
                    changed = True
            if changed and browser_ref[0] is not None:
                browser_ref[0].reload()
        except Exception:
            pass

    config_timer = QTimer()
    config_timer.timeout.connect(check_config_changes)
    config_timer.start(2000)

    # Tray icon only in headless mode (via tray_helper); desktop mode has a visible window
    def close_splash():
        if splash_root:
            try:
                splash_root.destroy()
            except Exception:
                pass

    win.show()
    win.raise_()
    win.activateWindow()
    app.processEvents()
    close_splash()

    def init_browser():
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
        except (ImportError, OSError) as e:
            # Import can fail when installed: DLL load failed, Sandbox restrictions, etc.
            err_msg = str(e).strip() or "unknown"
            label.setText(
                "PyQtWebEngine failed to load.\n\n"
                f"Error: {err_msg[:80]}\n\n"
                "If running in Windows Sandbox: try outside Sandbox, or use\n"
                "browser mode instead.\n\n"
                "Otherwise: pip install PyQtWebEngine"
            )
            retry_btn.setText("Open in browser")
            retry_btn.setVisible(True)
            bar.setVisible(False)
            retry_btn.clicked.connect(lambda: (webbrowser.open(f"http://127.0.0.1:{port}"), app.quit()))
            return
        browser = QWebEngineView()
        browser.setStyleSheet("background-color: #0d1117;")
        browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        browser_ref[0] = browser

        class F11Filter(QObject):
            def __init__(self, toggle_fn):
                super().__init__()
                self.toggle_fn = toggle_fn

            def eventFilter(self, obj, event):
                if obj == browser and event.type() == QEvent.KeyPress and event.key() == Qt.Key_F11:
                    self.toggle_fn()
                    return True
                return False

        browser.installEventFilter(F11Filter(_toggle_fullscreen))
        stack.addWidget(browser)
        url_obj = QUrl(f"http://127.0.0.1:{port}?desktop=true")

        def on_load_finished(ok):
            if ok and stack.currentIndex() == 0:
                stack.setCurrentIndex(1)
                retry_btn.setVisible(False)
                bar.setVisible(True)
            elif not ok and stack.currentIndex() == 0:
                retry_btn.setVisible(True)
                bar.setVisible(False)
                retry_btn.setText("Retry (connection failed)")

        def do_load():
            browser.setUrl(url_obj)

        def maybe_show_retry():
            if stack.currentIndex() == 0:
                retry_btn.setVisible(True)
                bar.setVisible(False)
                retry_btn.setText("Retry (server not ready)")

        def on_retry_click():
            retry_btn.setVisible(False)
            bar.setVisible(True)
            do_load()

        # Don't switch back to loading on loadStarted - it can fire for sub-frames/redirects
        # and trap the app on the loading screen. Only transition once on first successful load.
        browser.loadFinished.connect(on_load_finished)
        retry_btn.clicked.connect(on_retry_click)
        do_load()
        QTimer.singleShot(8000, maybe_show_retry)

    QTimer.singleShot(0, init_browser)

    sys.exit(app.exec_())
