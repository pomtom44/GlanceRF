"""
Update checker for GlanceRF.
Checks GitHub releases for new versions.
"""

import asyncio
import os
import re
from datetime import datetime, timedelta, time as dt_time
from typing import Any, Dict, Optional, Tuple

import httpx

from glancerf import __version__
from glancerf.config import get_config, get_logger

_log = get_logger("update_checker")

GITHUB_RELEASES_URL = "https://api.github.com/repos/pomtom44/GlanceRF/releases/latest"
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GlanceRF-update-checker"}


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string (e.g. '2.0.0') into (major, minor, patch)."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str.strip())
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return (0, 0, 0)


def compare_versions(current: str, latest: str) -> bool:
    """Return True if latest > current."""
    return parse_version(latest) > parse_version(current)


def is_version_ahead(current: str, latest: str) -> bool:
    """Return True if current > latest (e.g. local dev ahead of GitHub)."""
    return parse_version(current) > parse_version(latest)


async def get_latest_release_info() -> Optional[Dict[str, Any]]:
    """Fetch latest release from GitHub. Returns dict with version, release_notes, or None."""
    _log.debug("Fetching latest release from %s", GITHUB_RELEASES_URL)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(GITHUB_RELEASES_URL, headers=GITHUB_HEADERS)
            if response.status_code == 200:
                data = response.json()
                tag = data.get("tag_name", "")
                version = tag.lstrip("v") if tag else None
                if version and re.match(r"^\d+\.\d+\.\d+", version):
                    body = data.get("body") or ""
                    return {"version": version, "release_notes": (body.strip() if body else "")}
    except Exception as e:
        _log.debug("GitHub release check failed: %s", e)
    return None


async def check_for_updates() -> Optional[str]:
    """Check for updates. Returns latest version string if available, else None."""
    _log.debug("Checking for updates (current=%s)", __version__)
    info = await get_latest_release_info()
    if info and compare_versions(__version__, info["version"]):
        return info["version"]
    return None


def _parse_check_time(time_str: str) -> Optional[dt_time]:
    """Parse HH:MM time string into time object."""
    match = re.match(r"^(\d{1,2}):(\d{2})$", (time_str or "").strip())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return dt_time(hour, minute)
    return None


def _seconds_until_time(target_time: dt_time) -> float:
    """Seconds until next occurrence of target_time."""
    now = datetime.now()
    target_dt = datetime.combine(now.date(), target_time)
    if target_dt <= now:
        target_dt = target_dt + timedelta(days=1)
    return (target_dt - now).total_seconds()


class UpdateChecker:
    """Background update checker; broadcasts update_available when found."""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self._task: Optional[asyncio.Task] = None

    async def _check_and_notify(self) -> None:
        try:
            config = get_config()
            if (config.get("update_mode") or "none") == "none":
                return
            latest = await check_for_updates()
            if latest:
                _log.debug("Update available: %s (current %s)", latest, __version__)
                await self.connection_manager.broadcast_update_notification({
                    "type": "update_available",
                    "data": {
                        "current_version": __version__,
                        "latest_version": latest,
                        "docker_mode": bool(os.environ.get("GLANCERF_DOCKER")),
                    },
                })
        except Exception as e:
            _log.debug("Update check failed: %s", e)

    async def _run_scheduled(self) -> None:
        while True:
            try:
                config = get_config()
                mode = config.get("update_mode") or "none"
                if mode == "none":
                    await asyncio.sleep(3600)
                    continue
                check_time = _parse_check_time(config.get("update_check_time") or "03:00") or dt_time(3, 0)
                wait = _seconds_until_time(check_time)
                await asyncio.sleep(wait)
                await self._check_and_notify()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(3600)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_scheduled())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def schedule_restart(self, latest_version: str, delay_seconds: int = 10) -> None:
        """
        Schedule application restart after update.
        Broadcasts restart_pending to clients, waits, then restarts.
        """
        import os
        import subprocess
        import sys

        from glancerf.updates.updater import create_restart_script

        await self.connection_manager.broadcast_update_notification({
            "type": "update_available",
            "data": {
                "current_version": __version__,
                "latest_version": latest_version,
                "restart_pending": True,
                "restart_in_seconds": delay_seconds,
                "docker_mode": bool(os.environ.get("GLANCERF_DOCKER")),
            },
        })
        await asyncio.sleep(delay_seconds)
        restart_script = create_restart_script()
        if restart_script:
            try:
                subprocess.Popen([str(restart_script)], shell=True, cwd=str(restart_script.parent))
            except Exception as e:
                _log.error("Failed to start restart script: %s", e)
        os._exit(0)
