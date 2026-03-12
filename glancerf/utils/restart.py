"""
Cross-platform restart of GlanceRF services.
Works when running as: Windows service, Linux systemd, macOS launchd, or run.py.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from glancerf.config import get_logger

_log = get_logger("restart")


def get_app_root() -> Path:
    """Project root (parent of glancerf package)."""
    return Path(__file__).resolve().parent.parent.parent


def _create_and_run_restart_script() -> bool:
    """Create and run platform-specific restart script. Returns True on success."""
    app_root = get_app_root()
    try:
        if sys.platform == "win32":
            script_path = app_root / "restart_services.bat"
            script_content = f"""@echo off
cd /d "{app_root}"
rem Wait for old process to exit and port to be released
timeout /t 4 /nobreak >nul
net stop GlanceRF 2>nul
timeout /t 2 /nobreak >nul
net start GlanceRF 2>nul
if %errorlevel% neq 0 (
    start "" /D "{app_root}" "{sys.executable}" run.py
)
"""
            with open(script_path, "w") as f:
                f.write(script_content)
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                ["cmd.exe", "/c", str(script_path)],
                cwd=str(app_root),
                creationflags=DETACHED_PROCESS,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        else:
            script_path = app_root / "restart_services.sh"
            python_exe = sys.executable
            if sys.platform == "darwin":
                plist = os.path.expanduser("~/Library/LaunchAgents/com.glancerf.plist")
                script_content = f"""#!/bin/sh
cd "{app_root}"
sleep 2
if [ -f "{plist}" ]; then
    launchctl unload "{plist}" 2>/dev/null || true
    sleep 1
    launchctl load "{plist}" 2>/dev/null || true
else
    exec "{python_exe}" run.py
fi
"""
            else:
                script_content = f"""#!/bin/sh
cd "{app_root}"
sleep 2
systemctl --user restart glancerf 2>/dev/null || exec "{python_exe}" run.py
"""
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            subprocess.Popen(
                [str(script_path)],
                cwd=str(app_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
    except Exception as e:
        _log.error("Failed to create or run restart script: %s", e)
        return False


def trigger_restart() -> Tuple[bool, str]:
    """
    Trigger a restart of GlanceRF services.
    Returns (success, message). Caller should exit after success.
    """
    if _create_and_run_restart_script():
        return True, "Restart initiated. The app will come back in a few seconds."
    return False, "Failed to start restart script."
