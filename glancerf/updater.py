"""
Auto-updater for GlanceRF
Downloads and installs updates from GitHub releases
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
from glancerf.logging_config import DETAILED_LEVEL, get_logger

_log = get_logger("updater")

# GitHub API (same as update_checker) for release-by-tag
GITHUB_RELEASE_BY_TAG = "https://api.github.com/repos/pomtom44/GlanceRF/releases/tags/{tag}"
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GlanceRF-updater"}

# Constants
ITEMS_TO_UPDATE = ["glancerf", "run.py", "requirements.txt"]
ITEMS_TO_BACKUP = ["glancerf", "run.py", "requirements.txt", "glancerf_config.json"]
RESTART_DELAY_SECONDS = 10


def get_app_root() -> Path:
    """Get the root directory of the application."""
    # This file is in glancerf/, so go up one level to Project/
    return Path(__file__).parent.parent.resolve()


def get_staging_dir() -> Path:
    """Get the staging directory for updates."""
    app_root = get_app_root()
    staging = app_root / ".update_staging"
    staging.mkdir(exist_ok=True)
    return staging


def get_backup_dir() -> Path:
    """Get the backup directory for rollback."""
    app_root = get_app_root()
    backup = app_root / ".update_backup"
    backup.mkdir(exist_ok=True)
    return backup


async def download_release_zip(release_url: str, target_path: Path) -> bool:
    """
    Download a release ZIP file from GitHub.
    """
    _log.debug("Downloading update from %s to %s", release_url[:80], target_path)
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream('GET', release_url) as response:
                _log.debug("Download response status=%s headers=%s", response.status_code, dict(response.headers))
                response.raise_for_status()
                with open(target_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        _log.debug("Download complete: %s (%s bytes)", target_path, target_path.stat().st_size if target_path.exists() else 0)
        return True
    except Exception as e:
        _log.debug("Download failed: %s", e, exc_info=True)
        return False


async def get_release_zip_url(version: str) -> Optional[str]:
    """
    Get the ZIP download URL for a GitHub release.
    Uses GitHub API release-by-tag (zipball_url); fallback to archive URL with HEAD check.
    """
    tag = f"v{version}" if not version.startswith("v") else version
    try:
        # 1) Prefer GitHub API: get release by tag and use zipball_url (follows redirects on GET)
        api_url = GITHUB_RELEASE_BY_TAG.format(tag=tag)
        _log.debug("Getting release zip URL for %s via API: %s", version, api_url)
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(api_url, headers=GITHUB_HEADERS)
            _log.debug("GitHub API release-by-tag response: status=%s", response.status_code)
            if response.status_code == 200:
                data = response.json()
                zip_url = data.get("zipball_url")
                if zip_url:
                    _log.debug("Using zipball_url: %s", zip_url)
                    return zip_url
                _log.debug("Release JSON has no zipball_url")
            else:
                _log.debug("GitHub API returned %s: %s", response.status_code, response.text[:200] if response.text else "")

        # 2) Fallback: construct archive URL and verify with HEAD (accept 200 or 302)
        repo = "pomtom44/GlanceRF"
        for candidate_tag in (tag, version):
            zip_url = f"https://github.com/{repo}/archive/refs/tags/{candidate_tag}.zip"
            _log.debug("Fallback: HEAD %s", zip_url)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.head(zip_url)
                _log.debug("HEAD response: status=%s", response.status_code)
                if response.status_code in (200, 302):
                    return zip_url
        return None
    except Exception as e:
        _log.debug("Failed to get release URL: %s", e, exc_info=True)
        return None


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a ZIP file to a directory."""
    _log.debug("Extracting %s to %s", zip_path, extract_to)
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            names = zip_ref.namelist()
            _log.debug("ZIP contains %s entries (first few: %s)", len(names), names[:5] if names else [])
            zip_ref.extractall(extract_to)
        _log.debug("Extract complete; extract_to contents: %s", [p.name for p in extract_to.iterdir()] if extract_to.exists() else [])
        return True
    except Exception as e:
        _log.debug("Extract failed: %s", e, exc_info=True)
        return False


def get_extracted_root(extract_dir: Path) -> Optional[Path]:
    """Find the root directory inside the extracted ZIP (app root with glancerf/ and run.py)."""
    _log.debug("Finding extracted root in %s; top-level items: %s", extract_dir, [p.name for p in extract_dir.iterdir()] if extract_dir.exists() else [])
    project_dir = extract_dir / "Project"
    if project_dir.exists() and project_dir.is_dir():
        if (project_dir / "run.py").exists() and (project_dir / "glancerf").exists():
            _log.debug("Found Project at %s", project_dir)
            return project_dir
    for item in extract_dir.iterdir():
        if item.is_dir():
            project_in_sub = item / "Project"
            if project_in_sub.exists() and project_in_sub.is_dir():
                if (project_in_sub / "run.py").exists() and (project_in_sub / "glancerf").exists():
                    _log.debug("Found Project in subdir: %s", project_in_sub)
                    return project_in_sub
            if (item / "run.py").exists() and (item / "glancerf").exists():
                _log.debug("Found app root at subdir: %s", item)
                return item
    _log.debug("No Project or app root found in %s", extract_dir)
    return None


def backup_current_installation(backup_dir: Path) -> bool:
    """Backup the current installation for rollback."""
    _log.debug("Backing up current installation to %s", backup_dir)
    try:
        app_root = get_app_root()
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        for item in ITEMS_TO_BACKUP:
            src = app_root / item
            if src.exists():
                dst = backup_dir / item
                _log.debug("Backup item: %s -> %s", src, dst)
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        version_info = {"version": __version__, "backup_timestamp": time.time()}
        with open(backup_dir / "version.json", 'w') as f:
            json.dump(version_info, f)
        _log.debug("Backup complete; version=%s", __version__)
        return True
    except Exception as e:
        _log.error("Backup failed: %s", e, exc_info=True)
        return False


def _merge_glancerf_dir(src: Path, dst: Path) -> None:
    """
    Copy src (extracted glancerf/) to dst (app glancerf/).
    For glancerf/modules/ we merge: copy each built-in module from src over dst,
    but do not delete dst/modules subfolders that are not in src (e.g. _custom/).
    """
    for entry in src.iterdir():
        dst_entry = dst / entry.name
        if entry.is_file():
            if dst_entry.exists():
                dst_entry.unlink()
            shutil.copy2(entry, dst_entry)
        elif entry.is_dir():
            if entry.name == "modules":
                # Merge modules: copy each subdir from update over existing; preserve _custom/
                dst.mkdir(parents=True, exist_ok=True)
                modules_dst = dst / "modules"
                modules_dst.mkdir(parents=True, exist_ok=True)
                for sub in entry.iterdir():
                    if sub.is_dir():
                        sub_dst = modules_dst / sub.name
                        if sub_dst.exists():
                            shutil.rmtree(sub_dst)
                        shutil.copytree(sub, sub_dst)
            else:
                if dst_entry.exists():
                    shutil.rmtree(dst_entry)
                shutil.copytree(entry, dst_entry)


def apply_update(extracted_root: Path) -> Tuple[bool, str]:
    """Apply the update by copying files from extracted update to app root."""
    _log.debug("Applying update from %s", extracted_root)
    try:
        app_root = get_app_root()
        for item in ITEMS_TO_UPDATE:
            src = extracted_root / item
            dst = app_root / item
            if not src.exists():
                _log.debug("Skip (missing): %s", src)
                continue
            _log.debug("Apply item: %s -> %s", src, dst)
            if item == "glancerf" and src.is_dir():
                if dst.exists() and dst.is_dir():
                    _merge_glancerf_dir(src, dst)
                else:
                    if dst.exists():
                        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
                    shutil.copytree(src, dst)
                continue
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        _log.debug("Apply update complete")
        return True, ""
    except Exception as e:
        _log.error("Update apply failed: %s", e, exc_info=True)
        return False, str(e)


def install_requirements(app_root: Path) -> Tuple[bool, str]:
    """
    Run pip install -r requirements.txt from app_root so new dependencies
    (e.g. feedparser) are installed after an update.
    Uses the same Python executable that is running the app.
    """
    req_file = app_root / "requirements.txt"
    if not req_file.is_file():
        _log.debug("No requirements.txt at %s, skipping pip install", req_file)
        return True, ""
    _log.debug("Installing requirements from %s", req_file)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            cwd=str(app_root),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            _log.debug("pip install -r requirements.txt succeeded")
            return True, ""
        err = (result.stderr or result.stdout or "").strip() or "pip install failed"
        _log.warning("pip install -r requirements.txt failed: %s", err[:500])
        return False, err[:500]
    except subprocess.TimeoutExpired:
        _log.warning("pip install -r requirements.txt timed out")
        return False, "pip install timed out"
    except Exception as e:
        _log.warning("pip install -r requirements.txt error: %s", e)
        return False, str(e)


async def perform_auto_update(version: str) -> Tuple[bool, str]:
    """Perform automatic update: download, extract, backup, and apply."""
    _log.log(DETAILED_LEVEL, "Auto-update started: %s (current %s)", version, __version__)
    try:
        staging_dir = get_staging_dir()
        backup_dir = get_backup_dir()
        _log.debug("Staging dir=%s backup dir=%s", staging_dir, backup_dir)

        # Step 1: Get download URL
        _log.debug("Step 1: Getting release download URL for %s", version)
        zip_url = await get_release_zip_url(version)
        if not zip_url:
            _log.debug("get_release_zip_url returned None for version=%s", version)
            return False, "Could not find release download URL"

        # Step 2: Download ZIP
        zip_path = staging_dir / f"update_{version}.zip"
        _log.debug("Step 2: Downloading to %s", zip_path)
        if not await download_release_zip(zip_url, zip_path):
            return False, "Failed to download update"

        # Step 3: Extract ZIP
        extract_dir = staging_dir / f"extracted_{version}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        _log.debug("Step 3: Extracting to %s", extract_dir)
        if not extract_zip(zip_path, extract_dir):
            return False, "Failed to extract update"

        # Step 4: Find Project/ directory
        _log.debug("Step 4: Finding Project directory in extracted files")
        extracted_root = get_extracted_root(extract_dir)
        if not extracted_root:
            return False, "Could not find Project directory in update"

        # Step 5: Backup
        _log.debug("Step 5: Backing up current installation")
        if not backup_current_installation(backup_dir):
            return False, "Failed to backup current installation"

        # Step 6: Apply update
        _log.debug("Step 6: Applying update")
        success, error = apply_update(extracted_root)
        if not success:
            _log.debug("Apply failed, restoring from backup")
            restore_from_backup(backup_dir)
            return False, f"Failed to apply update: {error}"

        # Step 6b: Install/upgrade dependencies from new requirements.txt
        app_root = get_app_root()
        pip_ok, pip_err = install_requirements(app_root)
        if not pip_ok:
            _log.warning("Dependency install failed after update: %s", pip_err)
            return True, (
                f"Update to {version} installed successfully. Restart required. "
                "Dependency install failed; run manually: pip install -r requirements.txt"
            )

        # Step 7: Clean up staging
        try:
            shutil.rmtree(staging_dir)
            _log.debug("Staging directory removed")
        except Exception as e:
            _log.debug("Failed to clean staging directory: %s", e)

        _log.log(DETAILED_LEVEL, "Auto-update completed: %s", version)
        return True, f"Update to {version} installed successfully. Restart required."

    except Exception as e:
        _log.log(DETAILED_LEVEL, "Auto-update failed: %s", e)
        _log.debug("Update failed with exception: %s", e, exc_info=True)
        return False, f"Update failed: {str(e)}"


def restore_from_backup(backup_dir: Path) -> bool:
    """
    Restore installation from backup (rollback).
    
    Args:
        backup_dir: Directory containing backup
    
    Returns:
        True if successful, False otherwise
    """
    try:
        app_root = get_app_root()
        
        if not backup_dir.exists():
            return False
        
        # Restore each backed up item
        for item in backup_dir.iterdir():
            if item.name == "version.json":
                continue
            
            src = item
            dst = app_root / item.name
            
            # Remove destination if it exists
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            
            # Restore from backup
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        return True
    except Exception:
        return False


def create_restart_script() -> Optional[Path]:
    """
    Create a script to restart the application after update.
    This is platform-specific.
    
    Returns:
        Path to the restart script, or None if not supported
    """
    try:
        app_root = get_app_root()
        script_path = app_root / "restart_after_update.py"
        
        if sys.platform == "win32":
            # Windows: Create a batch script
            bat_path = app_root / "restart_after_update.bat"
            bat_content = f"""@echo off
cd /d "{app_root}"
timeout /t 2 /nobreak >nul
python run.py
"""
            with open(bat_path, 'w') as f:
                f.write(bat_content)
            return bat_path
        else:
            # Unix-like: Create a shell script
            sh_path = app_root / "restart_after_update.sh"
            sh_content = f"""#!/bin/bash
cd "{app_root}"
sleep 2
python3 run.py
"""
            with open(sh_path, 'w') as f:
                f.write(sh_content)
            os.chmod(sh_path, 0o755)
            return sh_path
    except Exception as e:
        _log.error("Failed to create restart script: %s", e)
        return None
