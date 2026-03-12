"""
Detect if GPU should be disabled for Chromium (QtWebEngine).
Returns True when running in Windows Sandbox, VMs with software rendering,
or when only Microsoft Basic Display Adapter is present.
Used during install to set config.disable_gpu for faster desktop startup.
"""

import os
import subprocess
import sys


def should_disable_gpu() -> bool:
    """
    Return True if we should add --disable-gpu for Chromium.
    Detects: Windows Sandbox, software-only display adapters.
    """
    if sys.platform != "win32":
        return False

    # Windows Sandbox: runs as WDAGUtilityAccount
    if os.environ.get("USERNAME", "").strip() == "WDAGUtilityAccount":
        return True

    # Computer name often contains "Sandbox" in WSB
    comp = os.environ.get("COMPUTERNAME", "").upper()
    if "SANDBOX" in comp or "WINSANDBOX" in comp:
        return True

    # Check display adapters: if only Microsoft Basic Display/Render, use software rendering
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False
        names = (result.stdout or "").strip().lower()
        if not names:
            return False
        # Split by newlines in case of multiple adapters
        adapters = [a.strip() for a in names.splitlines() if a.strip()]
        basic_only = all(
            "microsoft basic display" in a or "microsoft basic render" in a
            for a in adapters
        )
        if basic_only and adapters:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return False


if __name__ == "__main__":
    # For installer: print "true" or "false" for easy parsing
    print("true" if should_disable_gpu() else "false")
