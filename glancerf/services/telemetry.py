"""
Telemetry sender for GlanceRF.
Sends anonymous usage data (version, platform) when enabled.
"""

import asyncio
import platform
import re
import time
from datetime import datetime
from typing import Optional, Tuple

import httpx

from glancerf import __version__
from glancerf.config import get_config, get_logger

_log = get_logger("telemetry")

TELEMETRY_URL = "https://glancerf-telemetry.zl4st.com/telemetry.php"

_LINUX_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+(?:-\d+)?)\s*\(")


def _normalize_platform_version(system: str, raw_version: str) -> str:
    """Return a short platform version. On Linux, extract kernel version."""
    if not raw_version or not isinstance(raw_version, str):
        return raw_version or ""
    if system == "Linux":
        m = _LINUX_VERSION_RE.search(raw_version)
        if m:
            return m.group(1).strip()
    return raw_version.strip()[:128] if len(raw_version) > 128 else raw_version.strip()


def get_system_info() -> dict:
    """Get system information for telemetry."""
    system = platform.system()
    raw_version = platform.version()
    return {
        "platform": system,
        "platform_release": platform.release(),
        "platform_version": _normalize_platform_version(system, raw_version),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }


def get_glancerf_info() -> dict:
    """Get GlanceRF info for telemetry. Module counts omitted until modules are implemented."""
    try:
        config = get_config()
        desktop_mode = config.get("desktop_mode") or "browser"
        return {
            "version": __version__,
            "desktop_mode": desktop_mode,
            "use_desktop": desktop_mode in ("desktop", "browser"),  # backward compat for telemetry server
        }
    except Exception:
        return {"version": __version__}


def get_guid() -> Tuple[Optional[str], bool]:
    """Get existing GUID from config. Returns (guid, is_first_checkin)."""
    try:
        config = get_config()
        guid = config.get("telemetry_guid")
        if not guid:
            return None, True
        return guid, False
    except Exception:
        return None, True


async def request_guid_only() -> bool:
    """Request a GUID from the server."""
    try:
        config = get_config()
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "guid_request",
            "glancerf": get_glancerf_info(),
            "system": get_system_info(),
            "guid": "",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(TELEMETRY_URL, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            if data.get("guid"):
                config.set("telemetry_guid", data["guid"])
                return True
    except Exception as e:
        _log.debug("Telemetry GUID request failed: %s", e)
    return False


async def send_telemetry(event_type: str = "heartbeat", additional_data: Optional[dict] = None) -> bool:
    """Send telemetry data. Returns True on success."""
    try:
        config = get_config()
        if config.get("first_run", True):
            return False
        if not config.get("telemetry_enabled", True):
            return False

        guid, _ = get_guid()
        if not guid:
            return False

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "glancerf": get_glancerf_info(),
            "system": get_system_info(),
            "guid": guid,
        }
        if additional_data:
            payload["additional"] = additional_data

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(TELEMETRY_URL, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            return True
    except Exception as e:
        _log.debug("Telemetry send failed: %s", e)
        return False


class TelemetrySender:
    """Manages periodic telemetry sending."""

    def __init__(self):
        self.start_time = time.time()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = 3600  # 1 hour

    async def _run_heartbeat(self) -> None:
        """Background task: send periodic heartbeats."""
        try:
            # Request GUID immediately on launch (don't wait for first_run)
            guid, _ = get_guid()
            if not guid:
                await request_guid_only()

            # Wait for first_run to complete before sending startup/heartbeat events
            config = get_config()
            if config.get("first_run", True):
                while config.get("first_run", True):
                    await asyncio.sleep(60)
                    config = get_config()

            await send_telemetry("startup", {"startup_time": datetime.utcnow().isoformat()})
            await asyncio.sleep(300)

            while True:
                try:
                    uptime = int(time.time() - self.start_time)
                    await send_telemetry("heartbeat", {"uptime_seconds": uptime})
                    await asyncio.sleep(self.heartbeat_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    _log.debug("Heartbeat error: %s", e)
                    await asyncio.sleep(60)
        except asyncio.CancelledError:
            raise

    def start(self) -> None:
        """Start the telemetry background task."""
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._run_heartbeat())

    def stop(self) -> None:
        """Stop the telemetry background task."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
