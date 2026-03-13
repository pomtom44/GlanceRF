"""
Auto-updater for GlanceRF.
Downloads and installs updates from GitHub releases.
In Docker (GLANCERF_DOCKER=1): perform_auto_update returns early with a message to pull new image.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import httpx

from glancerf import __version__
from glancerf.config import DETAILED_LEVEL, get_logger

_log = get_logger("updater")

GITHUB_RELEASE_BY_TAG = "https://api.github.com/repos/pomtom44/GlanceRF/releases/tags/{tag}"
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GlanceRF-updater"}

ITEMS_TO_UPDATE = ["glancerf", "run.py", "requirements"]
ITEMS_TO_BACKUP = ["glancerf", "run.py", "requirements", "glancerf_config.json"]
PROTECTED_APP_ROOT_FILES = ["glancerf_config.json"]

_update_progress = {
    "running": False,
    "step": "",
    "message": "",
    "success": None,
    "final_message": None,
}


def get_update_progress() -> dict:
    """Return a copy of current update progress for the web UI."""
    return dict(_update_progress)


def _set_progress(step: str, message: str = "") -> None:
    _update_progress["step"] = step
    _update_progress["message"] = message


def get_app_root() -> Path:
    """Get the root directory of the application (Project/)."""
    return Path(__file__).resolve().parent.parent.parent


def get_staging_dir() -> Path:
    """Get the staging directory for updates."""
    staging = get_app_root() / ".update_staging"
    staging.mkdir(exist_ok=True)
    return staging


def get_backup_dir() -> Path:
    """Get the backup directory for rollback."""
    backup = get_app_root() / ".update_backup"
    backup.mkdir(exist_ok=True)
    return backup


async def download_release_zip(release_url: str, target_path: Path) -> bool:
    """Download a release ZIP file from GitHub."""
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", release_url) as response:
                response.raise_for_status()
                with open(target_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        return True
    except Exception as e:
        _log.debug("Download failed: %s", e)
        return False


async def get_release_zip_url(version: str) -> Optional[str]:
    """Get the ZIP download URL for a GitHub release."""
    tag = f"v{version}" if not version.startswith("v") else version
    try:
        api_url = GITHUB_RELEASE_BY_TAG.format(tag=tag)
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(api_url, headers=GITHUB_HEADERS)
            if response.status_code == 200:
                data = response.json()
                zip_url = data.get("zipball_url")
                if zip_url:
                    return zip_url
        for candidate_tag in (tag, version):
            zip_url = f"https://github.com/pomtom44/GlanceRF/archive/refs/tags/{candidate_tag}.zip"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                r = await client.head(zip_url)
                if r.status_code in (200, 302):
                    return zip_url
    except Exception as e:
        _log.debug("Failed to get release URL: %s", e)
    return None


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a ZIP file to a directory."""
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_to)
        return True
    except Exception as e:
        _log.debug("Extract failed: %s", e)
        return False


def get_extracted_root(extract_dir: Path) -> Optional[Path]:
    """Find the Project directory inside the extracted ZIP (handles V2/Project or Project at root)."""
    # Direct Project/ at root
    project_dir = extract_dir / "Project"
    if project_dir.exists() and (project_dir / "run.py").exists() and (project_dir / "glancerf").exists():
        return project_dir
    # V2/Project (repo structure with V2 folder)
    v2_project = extract_dir / "V2" / "Project"
    if v2_project.exists() and (v2_project / "run.py").exists() and (v2_project / "glancerf").exists():
        return v2_project
    # Top-level dirs (e.g. pomtom44-GlanceRF-xxx or GlanceRF-main)
    for item in extract_dir.iterdir():
        if item.is_dir():
            sub_project = item / "Project"
            if sub_project.exists() and (sub_project / "run.py").exists():
                return sub_project
            v2_sub = item / "V2" / "Project"
            if v2_sub.exists() and (v2_sub / "run.py").exists():
                return v2_sub
            if (item / "run.py").exists() and (item / "glancerf").exists():
                return item
    return None


def backup_current_installation(backup_dir: Path) -> bool:
    """Backup the current installation for rollback."""
    try:
        app_root = get_app_root()
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        for item in ITEMS_TO_BACKUP:
            src = app_root / item
            if src.exists():
                dst = backup_dir / item
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        with open(backup_dir / "version.json", "w") as f:
            json.dump({"version": __version__, "backup_timestamp": time.time()}, f)
        return True
    except Exception as e:
        _log.error("Backup failed: %s", e)
        return False


def _merge_glancerf_dir(src: Path, dst: Path) -> None:
    """Merge glancerf/ from update into dst, preserving modules/_custom/."""
    for entry in src.iterdir():
        dst_entry = dst / entry.name
        if entry.is_file():
            if dst_entry.exists():
                dst_entry.unlink()
            shutil.copy2(entry, dst_entry)
        elif entry.is_dir():
            if entry.name == "modules":
                modules_dst = dst / "modules"
                modules_dst.mkdir(parents=True, exist_ok=True)
                for sub in entry.iterdir():
                    sub_dst = modules_dst / sub.name
                    if sub.is_file():
                        if sub_dst.exists():
                            sub_dst.unlink()
                        shutil.copy2(sub, sub_dst)
                    elif sub.is_dir():
                        if sub_dst.exists():
                            shutil.rmtree(sub_dst)
                        shutil.copytree(sub, sub_dst)
            else:
                if dst_entry.exists():
                    shutil.rmtree(dst_entry)
                shutil.copytree(entry, dst_entry)
    for entry in list(dst.iterdir()):
        if (src / entry.name).exists():
            continue
        if entry.name == "modules":
            for sub in list((dst / "modules").iterdir()):
                if sub.name == "_custom":
                    continue
                if not (src / "modules" / sub.name).exists():
                    if sub.is_dir():
                        shutil.rmtree(sub)
                    else:
                        sub.unlink()
        else:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()


def apply_update(extracted_root: Path) -> Tuple[bool, str]:
    """Apply the update by copying files from extracted update to app root."""
    try:
        app_root = get_app_root()
        for item in ITEMS_TO_UPDATE:
            if item in PROTECTED_APP_ROOT_FILES:
                continue
            src = extracted_root / item
            dst = app_root / item
            if not src.exists():
                continue
            if item == "glancerf" and src.is_dir():
                if dst.exists() and dst.is_dir():
                    _merge_glancerf_dir(src, dst)
                else:
                    if dst.exists():
                        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
                    shutil.copytree(src, dst)
                continue
            if dst.exists():
                shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        return True, ""
    except Exception as e:
        _log.error("Apply failed: %s", e)
        return False, str(e)


def install_requirements(app_root: Path) -> Tuple[bool, str]:
    """Run pip install for platform-appropriate requirements file."""
    req_dir = app_root / "requirements"
    if not req_dir.is_dir():
        return True, ""
    # Install only the platform-appropriate file to avoid pywin32 on Linux/mac, etc.
    if sys.platform == "win32":
        req_file = req_dir / "requirements-windows-desktop.txt"
        if not req_file.exists():
            req_file = req_dir / "requirements-windows.txt"
    elif sys.platform == "darwin":
        req_file = req_dir / "requirements-mac.txt"
        if not req_file.exists():
            req_file = req_dir / "requirements-linux.txt"
    else:
        req_file = req_dir / "requirements-linux.txt"
    if not req_file.exists():
        return True, ""
    req_files = [req_file]
    for req_file in req_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                cwd=str(app_root),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "").strip() or "pip install failed"
                if "externally-managed-environment" in err and sys.platform != "win32":
                    result2 = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", str(req_file)],
                        cwd=str(app_root),
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if result2.returncode != 0:
                        return False, (result2.stderr or result2.stdout or "")[:500]
                else:
                    return False, err[:500]
        except subprocess.TimeoutExpired:
            return False, "pip install timed out"
        except Exception as e:
            return False, str(e)
    return True, ""


def restore_from_backup(backup_dir: Path) -> bool:
    """Restore installation from backup (rollback)."""
    try:
        app_root = get_app_root()
        if not backup_dir.exists():
            return False
        for item in backup_dir.iterdir():
            if item.name == "version.json":
                continue
            dst = app_root / item.name
            if dst.exists():
                shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)
        return True
    except Exception:
        return False


def create_restart_script() -> Optional[Path]:
    """Create a script to restart the application after update."""
    try:
        app_root = get_app_root()
        if sys.platform == "win32":
            bat_path = app_root / "restart_after_update.bat"
            bat_content = f'@echo off\ncd /d "{app_root}"\ntimeout /t 2 /nobreak >nul\n{sys.executable} run.py\n'
            with open(bat_path, "w") as f:
                f.write(bat_content)
            return bat_path
        else:
            sh_path = app_root / "restart_after_update.sh"
            sh_content = f'#!/bin/sh\ncd "{app_root}"\nsleep 2\nexec "{sys.executable}" run.py\n'
            with open(sh_path, "w") as f:
                f.write(sh_content)
            os.chmod(sh_path, 0o755)
            return sh_path
    except Exception as e:
        _log.error("Failed to create restart script: %s", e)
        return None


async def perform_auto_update(version: str) -> Tuple[bool, str]:
    """Perform automatic update. In Docker, returns early with message to pull new image."""
    if os.environ.get("GLANCERF_DOCKER"):
        return False, "In Docker: pull the new image and recreate the container. In-app update is not supported."

    _update_progress["running"] = True
    _update_progress["success"] = None
    _update_progress["final_message"] = None
    _log.log(DETAILED_LEVEL, "Auto-update started: %s (current %s)", version, __version__)

    try:
        staging_dir = get_staging_dir()
        backup_dir = get_backup_dir()

        _set_progress("Getting download URL", "Fetching release info from GitHub...")
        zip_url = await get_release_zip_url(version)
        if not zip_url:
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = "Could not find release download URL"
            return False, "Could not find release download URL"

        zip_path = staging_dir / f"update_{version}.zip"
        _set_progress("Downloading", f"Downloading update {version}...")
        if not await download_release_zip(zip_url, zip_path):
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = "Failed to download update"
            return False, "Failed to download update"

        extract_dir = staging_dir / f"extracted_{version}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        _set_progress("Extracting", "Extracting archive...")
        if not extract_zip(zip_path, extract_dir):
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = "Failed to extract update"
            return False, "Failed to extract update"

        _set_progress("Preparing", "Locating update files...")
        extracted_root = get_extracted_root(extract_dir)
        if not extracted_root:
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = "Could not find Project directory in update"
            return False, "Could not find Project directory in update"

        _set_progress("Backing up", "Backing up current installation...")
        if not backup_current_installation(backup_dir):
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = "Failed to backup"
            return False, "Failed to backup"

        _set_progress("Applying", "Applying update files...")
        success, error = apply_update(extracted_root)
        if not success:
            restore_from_backup(backup_dir)
            _update_progress["running"] = False
            _update_progress["success"] = False
            _update_progress["final_message"] = f"Failed to apply: {error}"
            return False, f"Failed to apply: {error}"

        _set_progress("Installing dependencies", "Running pip install...")
        app_root = get_app_root()
        pip_ok, pip_err = install_requirements(app_root)
        if not pip_ok:
            msg = f"Update to {version} installed. Restart required. Dependency install failed: {pip_err}"
            _update_progress["running"] = False
            _update_progress["success"] = True
            _update_progress["final_message"] = msg
            return True, msg

        try:
            shutil.rmtree(staging_dir)
        except Exception:
            pass

        msg = f"Update to {version} installed successfully. Restart required."
        _update_progress["running"] = False
        _update_progress["success"] = True
        _update_progress["final_message"] = msg
        return True, msg

    except Exception as e:
        _log.debug("Update failed: %s", e, exc_info=True)
        _update_progress["running"] = False
        _update_progress["success"] = False
        _update_progress["final_message"] = f"Update failed: {str(e)}"
        return False, str(e)
