"""
Telemetry sender for GlanceRF
Sends anonymous usage data to telemetry server
"""

import asyncio
import json
import platform
import time
from datetime import datetime
from typing import Optional, List, Tuple

import httpx

from glancerf import __version__
from glancerf.config import get_config
from glancerf.logging_config import get_logger
from glancerf.modules import get_modules

_log = get_logger("telemetry")


TELEMETRY_URL = "https://glancerf-telemetry.zl4st.com/telemetry.php"


def get_system_info() -> dict:
    """Get detailed system information."""
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation(),
    }


def get_glancerf_info() -> dict:
    """Get GlanceRF configuration info including modules."""
    try:
        config = get_config()
        
        # Get layout info
        layout = config.get("layout") or []
        grid_columns = config.get("grid_columns") or 0
        grid_rows = config.get("grid_rows") or 0
        
        # Get enabled modules (modules currently in use on dashboard)
        enabled_modules = set()
        for row in layout:
            for cell_value in row:
                if cell_value:
                    enabled_modules.add(cell_value)
        
        # Get all installed modules (all modules in modules folder)
        all_modules = get_modules()
        installed_module_ids = [m.get("id", "") for m in all_modules if m.get("id")]
        
        # Get module settings count
        module_settings = config.get("module_settings") or {}
        configured_cells = len(module_settings)
        
        return {
            "version": __version__,
            "grid_columns": grid_columns,
            "grid_rows": grid_rows,
            "enabled_module_count": len(enabled_modules),
            "enabled_modules": sorted(list(enabled_modules)),  # List of enabled module IDs
            "installed_module_count": len(installed_module_ids),
            "installed_modules": sorted(installed_module_ids),  # List of all installed module IDs
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
    """
    Get existing GUID from config.
    
    Returns:
        (guid, is_first_checkin) tuple where:
        - guid: Existing GUID from config, or None if not set
        - is_first_checkin: True if no GUID exists in config yet
    """
    try:
        config = get_config()
        guid = config.get("telemetry_guid")
        if not guid:
            return None, True
        return guid, False
    except Exception:
        return None, True


async def send_installation_event() -> bool:
    """
    Send installation event to server during setup to get GUID and log installation.
    This is called during first_run to register the installation with the server.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config()
        
        # Get GUID - should be None on first call
        guid, is_first_checkin = get_guid()
        
        # Build installation payload
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "installation",  # Special event type for setup
            "glancerf": get_glancerf_info(),
            "system": get_system_info(),
            "guid": "",  # Always send empty GUID so server generates one
        }
        
        # Send to server
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                TELEMETRY_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Server should return a GUID
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get("guid"):
                        # Server provided a GUID, save it
                        config.set("telemetry_guid", response_data["guid"])
                        _log.info("Telemetry installation event sent (GUID received)")
                        return True
                except Exception as e:
                    _log.warning("Failed to parse GUID from response: %s", e)
            
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


async def send_telemetry(event_type: str = "heartbeat", additional_data: Optional[dict] = None) -> bool:
    """
    Send telemetry data to the server.
    
    Args:
        event_type: Type of event (heartbeat, startup, error, etc.)
        additional_data: Optional additional data to include
    
    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config()
        
        # Check if setup is complete (first_run must be False)
        first_run = config.get("first_run")
        if first_run is None:
            first_run = True  # Default to True if not set (assume first run)
        
        # Don't send regular telemetry during initial setup
        if first_run:
            return False
        
        # Check if telemetry is enabled
        telemetry_enabled = config.get("telemetry_enabled")
        if telemetry_enabled is None:
            telemetry_enabled = True  # Default to enabled (opt-out)
        
        if not telemetry_enabled:
            return False
        
        # Get GUID from config
        guid, is_first_checkin = get_guid()
        
        if not guid:
            # No GUID yet - this shouldn't happen after setup, but handle gracefully
            return False
        
        # Build telemetry payload
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "glancerf": get_glancerf_info(),
            "system": get_system_info(),
            "guid": guid,
        }
        
        if additional_data:
            payload["additional"] = additional_data
        
        # Send to server
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
            
            # Check if this is first run and we need to register installation
            first_run = config.get("first_run")
            if first_run is None:
                first_run = True
            
            guid, _ = get_guid()
            
            # If first run and no GUID, send installation event to get GUID from server
            if first_run and not guid:
                await send_installation_event()
            
            # Wait for setup to complete before sending regular telemetry
            while first_run:
                await asyncio.sleep(60)  # Check every minute
                config = get_config()
                first_run = config.get("first_run")
                if first_run is None:
                    first_run = True
            
            # Setup is complete - send startup and start heartbeats
            await self.send_startup()
            _log.info("Telemetry startup event sent")

            # Wait a bit before starting heartbeats
            await asyncio.sleep(300)  # 5 minutes

            while True:
                try:
                    uptime_seconds = int(time.time() - self.start_time)
                    await send_telemetry("heartbeat", {
                        "uptime_seconds": uptime_seconds
                    })
                    _log.info("Telemetry heartbeat sent (uptime %s s)", uptime_seconds)
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
