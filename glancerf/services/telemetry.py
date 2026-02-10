"""
Telemetry sender for GlanceRF
Sends anonymous usage data to telemetry server
"""

import asyncio
import platform
import re
import time
from datetime import datetime
from typing import Optional, List, Tuple

import httpx

from glancerf import __version__
from glancerf.config import get_config, DETAILED_LEVEL, get_logger
from glancerf.modules import get_modules

_log = get_logger("telemetry")


TELEMETRY_URL = "https://glancerf-telemetry.zl4st.com/telemetry.php"

# Linux kernel version in platform.version() looks like:
# "#1 SMP PREEMPT_DYNAMIC PMX 6.8.12-16 (2025-10-14T08:58Z)" -> we want "6.8.12-16"
_LINUX_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+(?:-\d+)?)\s*\(")


def _normalize_platform_version(system: str, raw_version: str) -> str:
    """Return a short, readable platform version. On Linux, extract kernel version only."""
    if not raw_version or not isinstance(raw_version, str):
        return raw_version or ""
    if system == "Linux":
        m = _LINUX_VERSION_RE.search(raw_version)
        if m:
            return m.group(1).strip()
        m = re.search(r"\d+\.\d+\.\d+(?:-\d+)?", raw_version)
        if m:
            return m.group(0)
    return raw_version.strip()[:128] if len(raw_version) > 128 else raw_version.strip()


def get_system_info() -> dict:
    """Get detailed system information."""
    system = platform.system()
    raw_version = platform.version()
    return {
        "platform": system,
        "platform_release": platform.release(),
        "platform_version": _normalize_platform_version(system, raw_version),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation(),
    }


def get_glancerf_info() -> dict:
    """Get GlanceRF configuration info including modules."""
    try:
        config = get_config()

        layout = config.get("layout") or []
        grid_columns = config.get("grid_columns") or 0
        grid_rows = config.get("grid_rows") or 0

        enabled_modules = set()
        for row in layout:
            for cell_value in row:
                if cell_value:
                    enabled_modules.add(cell_value)

        all_modules = get_modules()
        installed_module_ids = [m.get("id", "") for m in all_modules if m.get("id")]

        module_settings = config.get("module_settings") or {}
        configured_cells = len(module_settings)

        return {
            "version": __version__,
            "grid_columns": grid_columns,
            "grid_rows": grid_rows,
            "enabled_module_count": len(enabled_modules),
            "enabled_modules": sorted(list(enabled_modules)),
            "installed_module_count": len(installed_module_ids),
            "installed_modules": sorted(installed_module_ids),
            "configured_cells_count": configured_cells,
            "use_desktop": config.get("use_desktop") or False,
            "update_mode": config.get("update_mode") or "none",
        }
    except Exception as e:
        return {
            "version": __version__,
            "error": "config_read_failed",
            "error_detail": str(e)
        }


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
    """Request a GUID from the server without logging an installation event."""
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
            response = await client.post(
                TELEMETRY_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("guid"):
                        config.set("telemetry_guid", response_data["guid"])
                        _log.log(DETAILED_LEVEL, "Telemetry GUID received (guid_request)")
                        return True
                except Exception as e:
                    _log.warning("Failed to parse GUID from response: %s", e)
        return False
    except httpx.ConnectError as e:
        _log.error("Telemetry connection error: %s", e)
        return False
    except httpx.TimeoutException as e:
        _log.error("Telemetry timeout: %s", e)
        return False
    except httpx.HTTPStatusError as e:
        _log.error("Telemetry HTTP error %s: %s", e.response.status_code, e)
        return False
    except Exception as e:
        _log.error("Telemetry GUID request failed: %s", e, exc_info=True)
        return False


async def send_telemetry(event_type: str = "heartbeat", additional_data: Optional[dict] = None) -> bool:
    """Send telemetry data to the server."""
    try:
        config = get_config()

        first_run = config.get("first_run")
        if first_run is None:
            first_run = True

        if first_run:
            return False

        telemetry_enabled = config.get("telemetry_enabled")
        if telemetry_enabled is None:
            telemetry_enabled = True

        if not telemetry_enabled:
            return False

        guid, is_first_checkin = get_guid()

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
            response = await client.post(
                TELEMETRY_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True
    except httpx.ConnectError as e:
        _log.error("Telemetry connection error: %s", e)
        return False
    except httpx.TimeoutException as e:
        _log.error("Telemetry timeout: %s", e)
        return False
    except httpx.HTTPStatusError as e:
        _log.error("Telemetry HTTP error %s: %s", e.response.status_code, e)
        return False
    except Exception as e:
        _log.error("Telemetry send failed: %s", e, exc_info=True)
        return False


class TelemetrySender:
    """Manages periodic telemetry sending"""

    def __init__(self):
        self.start_time = time.time()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = 3600  # 1 hour

    async def send_startup(self):
        """Send startup telemetry event."""
        await send_telemetry("startup", {
            "startup_time": datetime.utcnow().isoformat()
        })

    async def run_heartbeat(self):
        """Background task: send periodic heartbeat telemetry."""
        try:
            config = get_config()
            first_run = config.get("first_run")
            if first_run is None:
                first_run = True

            guid, _ = get_guid()
            if not guid:
                await request_guid_only()

            while first_run:
                await asyncio.sleep(60)
                config = get_config()
                first_run = config.get("first_run")
                if first_run is None:
                    first_run = True

            await self.send_startup()
            _log.log(DETAILED_LEVEL, "Telemetry startup event sent")

            await asyncio.sleep(300)

            while True:
                try:
                    uptime_seconds = int(time.time() - self.start_time)
                    await send_telemetry("heartbeat", {
                        "uptime_seconds": uptime_seconds
                    })
                    _log.log(DETAILED_LEVEL, "Telemetry heartbeat sent (uptime %s s)", uptime_seconds)
                    await asyncio.sleep(self.heartbeat_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    _log.error("Heartbeat error: %s", e, exc_info=True)
                    await asyncio.sleep(60)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            _log.error("Fatal telemetry error: %s", e, exc_info=True)

    def start(self):
        """Start the telemetry background task."""
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self.run_heartbeat())

    def stop(self):
        """Stop the telemetry background task."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
