"""
Time utilities for GlanceRF.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def get_current_time(config: Optional[Any] = None) -> Dict[str, str]:
    """
    Get current UTC and local time information.
    If config has gps_time_enabled and GPS provides time, use GPS time for UTC.
    """
    now_utc = datetime.now(timezone.utc)
    if config and config.get("gps_time_enabled"):
        try:
            from glancerf.services.gps_service import get_gps_time
            gps_time = get_gps_time(config)
            if gps_time is not None:
                now_utc = gps_time
        except Exception:
            pass
    now_local = now_utc.astimezone()

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
