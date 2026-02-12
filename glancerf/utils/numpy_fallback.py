"""
Fallback when NumPy fails to load due to CPU baseline (e.g. X86_V2) mismatch.
Attempts to reinstall NumPy with baseline=none and restart the process.
"""

import os
import subprocess
import sys


_ENV_REBUILD_ATTEMPTED = "GLANCERF_NUMPY_REBUILD_ATTEMPTED"


def _is_numpy_baseline_error(message: str) -> bool:
    """True if the exception message indicates NumPy CPU baseline mismatch."""
    if not message:
        return False
    msg = message.strip().lower()
    return (
        "numpy" in msg
        and "baseline" in msg
        and ("doesn't support" in msg or "does not support" in msg or "machine" in msg)
    )


def try_numpy_baseline_fallback(exception: BaseException) -> bool:
    """
    If the exception is a NumPy CPU baseline error, attempt to reinstall NumPy
    with baseline=none and re-exec the process. Returns True if we handled it
    (caller should not re-raise; process may have been replaced via exec).
    Returns False if this was not a baseline error or rebuild was skipped/failed.
    """
    msg = str(exception).strip()
    if not _is_numpy_baseline_error(msg):
        return False
    if os.environ.get(_ENV_REBUILD_ATTEMPTED):
        return False
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "numpy",
                "--no-binary",
                "numpy",
                "--force-reinstall",
                "-C",
                "setup-args=-Dcpu-baseline=none",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if result.returncode != 0:
        return False
    os.environ[_ENV_REBUILD_ATTEMPTED] = "1"
    os.execv(sys.executable, [sys.executable] + sys.argv)
    return True  # unreachable if exec succeeds
