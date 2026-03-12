"""
Time utilities for GlanceRF.
"""

from datetime import datetime, timezone
from typing import Dict


def get_current_time() -> Dict[str, str]:
    """Get current UTC and local time information."""
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()

    return {
        "utc": now_utc.strftime("%H:%M:%S"),
        "local": now_local.strftime("%H:%M:%S"),
        "utc_date": now_utc.strftime("%Y-%m-%d"),
        "local_date": now_local.strftime("%Y-%m-%d"),
        "utc_full": now_utc.isoformat(),
        "local_full": now_local.isoformat(),
        "utc_timestamp": now_utc.timestamp(),
        "local_timestamp": now_local.timestamp(),
    }
