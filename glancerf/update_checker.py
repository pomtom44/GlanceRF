"""
Update checker and notifier for GlanceRF
Checks for new versions and notifies users based on update_mode setting
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from datetime import datetime, time as dt_time
from typing import Optional, Tuple, Dict, Any

import httpx

from glancerf import __version__
from glancerf.config import get_config
from glancerf.logging_config import DETAILED_LEVEL, get_logger
from glancerf.updater import perform_auto_update

_log = get_logger("update_checker")


# GitHub API endpoint for releases (configure for your GlanceRF repo)
GITHUB_RELEASES_URL = "https://api.github.com/repos/pomtom44/GlanceRF/releases/latest"


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string (e.g. '0.1.0') into (major, minor, patch) tuple."""
    parts = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str.strip())
    if parts:
        return (int(parts.group(1)), int(parts.group(2)), int(parts.group(3)))
    return (0, 0, 0)


def compare_versions(current: str, latest: str) -> bool:
    """Return True if latest > current."""
    curr_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    return latest_tuple > curr_tuple


# GitHub API requires a User-Agent header (returns 403 without it)
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GlanceRF-update-checker"}


async def check_github_release() -> Optional[str]:
    """Check GitHub releases API for latest version. Returns version string or None."""
    info = await get_latest_release_info()
    return info.get("version") if info else None


async def get_latest_release_info() -> Optional[Dict[str, Any]]:
    """Fetch latest release from GitHub. Returns dict with version, release_notes, or None."""
    _log.debug("Fetching latest release from %s", GITHUB_RELEASES_URL)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GITHUB_RELEASES_URL, headers=GITHUB_HEADERS)
            _log.debug("GitHub releases API response: status=%s", response.status_code)
            if response.status_code == 200:
                data = response.json()
                tag = data.get("tag_name", "")
                version = tag.lstrip("v") if tag else None
                _log.debug("Latest release tag=%s version=%s", tag, version)
                if version and re.match(r"^\d+\.\d+\.\d+", version):
                    _log.log(DETAILED_LEVEL, "GitHub releases API: latest=%s", version)
                    body = data.get("body") or ""
                    return {"version": version, "release_notes": (body.strip() if body else "")}
                _log.debug("No valid version in response (tag=%s)", tag)
            else:
                _log.debug("GitHub API returned %s: %s", response.status_code, response.text[:300] if response.text else "")
    except Exception as e:
        _log.debug("GitHub release check failed: %s", e, exc_info=True)
    return None


async def check_version_endpoint(url: str) -> Optional[str]:
    """Check a simple version endpoint. Returns version string or None."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                version = data.get("version") or data.get("latest_version")
                if version and isinstance(version, str):
                    return version
    except Exception as e:
        _log.debug("Version endpoint check failed: %s", e)
    return None


async def check_for_updates() -> Optional[str]:
    """Check for updates. Returns latest version string if available, else None."""
    _log.debug("Checking for updates (current=%s)", __version__)
    latest = await check_github_release()
    _log.debug("Latest from GitHub: %s", latest)
    if latest and compare_versions(__version__, latest):
        _log.debug("Update available: %s > %s", latest, __version__)
        return latest
    _log.debug("No update available")
    return None


def parse_check_time(time_str: str) -> Optional[dt_time]:
    """Parse HH:MM time string into time object."""
    match = re.match(r"^(\d{1,2}):(\d{2})$", time_str.strip())
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return dt_time(hour, minute)
    return None


def seconds_until_time(target_time: dt_time) -> float:
    """Calculate seconds until next occurrence of target_time (today or tomorrow)."""
    now = datetime.now()
    target_dt = datetime.combine(now.date(), target_time)
    if target_dt <= now:
        target_dt = datetime.combine(now.date(), target_time)
        target_dt = target_dt.replace(day=target_dt.day + 1)
    delta = target_dt - now
    return delta.total_seconds()


class UpdateChecker:
    """Manages update checking and notifications"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.last_check_result: Optional[str] = None  # Latest version found, or None
        self.check_task: Optional[asyncio.Task] = None
    
    async def check_and_notify(self):
        """Check for updates and send notifications if needed."""
        try:
            config = get_config()
            update_mode = config.get("update_mode") or "none"
            
            if update_mode == "none":
                return
            
            latest = await check_for_updates()
            if latest:
                self.last_check_result = latest
                _log.log(DETAILED_LEVEL, "Update check: version %s available (current %s)", latest, __version__)

                if update_mode == "auto":
                    # Perform automatic update
                    success, message = await perform_auto_update(latest)
                    await self.send_update_notification(
                        latest, 
                        update_mode,
                        update_status="success" if success else "failed",
                        update_message=message
                    )
                    if success:
                        # Update successful - schedule restart
                        await self.schedule_restart()
                elif update_mode == "notify":
                    # Just notify, don't update
                    await self.send_update_notification(latest, update_mode)
            else:
                self.last_check_result = None
                _log.log(DETAILED_LEVEL, "Update check: no update available (current %s)", __version__)
        except Exception as e:
            _log.debug("Update check failed: %s", e, exc_info=True)
    
    async def schedule_restart(self, delay_seconds: int = 10):  # Default 10 seconds
        """
        Schedule application restart after update.
        
        Args:
            delay_seconds: How long to wait before restarting
        """
        # Send notification about pending restart
        await self.connection_manager.broadcast_update_notification({
            "type": "update_available",
            "data": {
                "current_version": __version__,
                "latest_version": self.last_check_result,
                "update_mode": "auto",
                "restart_pending": True,
                "restart_in_seconds": delay_seconds
            }
        })
        
        # Wait before restarting
        await asyncio.sleep(delay_seconds)
        
        # Restart the application
        from glancerf.updater import create_restart_script
        
        restart_script = create_restart_script()
        if restart_script:
            try:
                # Use the restart script
                if sys.platform == "win32":
                    subprocess.Popen([str(restart_script)], shell=True, cwd=str(restart_script.parent))
                else:
                    subprocess.Popen([str(restart_script)], shell=True, cwd=str(restart_script.parent))
            except Exception as e:
                _log.error("Failed to start restart script: %s", e)
                # Continue to exit anyway
        
        # Exit current process (restart script will start new one)
        os._exit(0)
    
    async def send_update_notification(
        self, 
        latest_version: str, 
        update_mode: str,
        update_status: Optional[str] = None,
        update_message: Optional[str] = None
    ):
        """Send update notification to all connected clients via WebSocket."""
        message = {
            "type": "update_available",
            "data": {
                "current_version": __version__,
                "latest_version": latest_version,
                "update_mode": update_mode,
            }
        }
        
        if update_status:
            message["data"]["update_status"] = update_status
        if update_message:
            message["data"]["update_message"] = update_message
        
        await self.connection_manager.broadcast_update_notification(message)
    
    async def run_scheduled_checks(self):
        """Background task: check for updates at configured time daily."""
        while True:
            try:
                config = get_config()
                update_mode = config.get("update_mode") or "none"
                check_time_str = config.get("update_check_time") or "03:00"
                
                if update_mode == "none":
                    await asyncio.sleep(3600)  # Check again in 1 hour
                    continue
                
                check_time = parse_check_time(check_time_str)
                if not check_time:
                    check_time = dt_time(3, 0)  # Default 3 AM
                
                # Wait until check time
                wait_seconds = seconds_until_time(check_time)
                await asyncio.sleep(wait_seconds)
                
                # Perform check
                await self.check_and_notify()
                
                # Wait until next day (slight over-wait to avoid immediate re-check)
                await asyncio.sleep(60)
            except Exception:
                await asyncio.sleep(3600)  # On error, retry in 1 hour
    
    def start(self):
        """Start the background update checker task."""
        if self.check_task is None or self.check_task.done():
            self.check_task = asyncio.create_task(self.run_scheduled_checks())
    
    def stop(self):
        """Stop the background update checker task."""
        if self.check_task and not self.check_task.done():
            self.check_task.cancel()
