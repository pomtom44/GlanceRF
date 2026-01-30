"""
Auto-updater for GlanceRF
Downloads and installs updates from GitHub releases
"""

import asyncio
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import httpx

from glancerf import __version__
from glancerf.logging_config import get_logger

_log = get_logger("updater")

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
    
    Args:
        release_url: URL to the ZIP file (from GitHub release assets)
        target_path: Where to save the downloaded file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream('GET', release_url) as response:
                response.raise_for_status()
                with open(target_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        return True
    except Exception as e:
        _log.debug("Download failed: %s", e)
        return False


async def get_release_zip_url(version: str) -> Optional[str]:
    """
    Get the ZIP download URL for a GitHub release.
    
    Args:
        version: Version string (e.g., "0.2.0")
    
    Returns:
        URL to the source code ZIP, or None if not found
    """
    try:
        # GitHub provides source code ZIP at: https://github.com/owner/repo/archive/refs/tags/vX.Y.Z.zip
        # Or we can get it from the release API
        repo = "pomtom44/GlanceRF"
        tag = f"v{version}" if not version.startswith("v") else version
        
        # Try the direct source code archive URL
        zip_url = f"https://github.com/{repo}/archive/refs/tags/{tag}.zip"
        
        # Verify it exists
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(zip_url)
            if response.status_code == 200:
                return zip_url
        
        # Fallback: try without 'v' prefix
        zip_url = f"https://github.com/{repo}/archive/refs/tags/{version}.zip"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(zip_url)
            if response.status_code == 200:
                return zip_url
        
        return None
    except Exception as e:
        import logging
        _log.debug(f"Failed to get release URL: {e}")
        return None


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """
    Extract a ZIP file to a directory.
    
    Args:
        zip_path: Path to the ZIP file
        extract_to: Directory to extract to
    
    Returns:
        True if successful, False otherwise
    """
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        _log.debug("Extract failed: %s", e)
        return False


def get_extracted_root(extract_dir: Path) -> Optional[Path]:
    """
    Find the root directory inside the extracted ZIP (the app root with glancerf/ and run.py).
    GitHub source ZIPs extract to a folder named like "GlanceRF-0.2.0" or "GlanceRF-main".

    Args:
        extract_dir: Directory where ZIP was extracted

    Returns:
        Path to the directory containing glancerf/ and run.py, or None if not found
    """
    # Look for Project/ directory (app root in this repo)
    project_dir = extract_dir / "Project"
    if project_dir.exists() and project_dir.is_dir():
        if (project_dir / "run.py").exists() and (project_dir / "glancerf").exists():
            return project_dir
    # Look in subdirectories (GitHub ZIPs create a versioned folder)
    for item in extract_dir.iterdir():
        if item.is_dir():
            project_in_sub = item / "Project"
            if project_in_sub.exists() and project_in_sub.is_dir():
                if (project_in_sub / "run.py").exists() and (project_in_sub / "glancerf").exists():
                    return project_in_sub
            # Fallback: repo root might be app root (run.py and glancerf at top level)
            if (item / "run.py").exists() and (item / "glancerf").exists():
                return item
    return None


def backup_current_installation(backup_dir: Path) -> bool:
    """
    Backup the current installation for rollback.
    
    Args:
        backup_dir: Directory to store backup
    
    Returns:
        True if successful, False otherwise
    """
    try:
        app_root = get_app_root()
        
        # Clear old backup
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy essential files/directories
        for item in ITEMS_TO_BACKUP:
            src = app_root / item
            if src.exists():
                dst = backup_dir / item
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # Save version info
        version_info = {
            "version": __version__,
            "backup_timestamp": time.time()
        }
        with open(backup_dir / "version.json", 'w') as f:
            json.dump(version_info, f)
        
        return True
    except Exception as e:
        import logging
        _log.error(f"Backup failed: {e}", exc_info=True)
        return False


def apply_update(extracted_root: Path) -> Tuple[bool, str]:
    """
    Apply the update by copying files from extracted update to app root.
    
    Args:
        extracted_root: Root of extracted update (Modern/ directory)
    
    Returns:
        (success, error_message)
    """
    try:
        app_root = get_app_root()
        
        # Copy each item to update
        for item in ITEMS_TO_UPDATE:
            src = extracted_root / item
            dst = app_root / item
            
            if not src.exists():
                continue
            
            # Remove destination if it exists
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            
            # Copy from extracted source
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        return True, ""
    except Exception as e:
        _log.error("Update apply failed: %s", e, exc_info=True)
        return False, str(e)


async def perform_auto_update(version: str) -> Tuple[bool, str]:
    """
    Perform automatic update: download, extract, backup, and apply.
    
    Args:
        version: Version to update to (e.g., "0.2.0")
    
    Returns:
        (success, message)
    """
    try:
        staging_dir = get_staging_dir()
        backup_dir = get_backup_dir()
        
        # Step 1: Get download URL
        zip_url = await get_release_zip_url(version)
        if not zip_url:
            return False, "Could not find release download URL"
        
        # Step 2: Download ZIP
        zip_path = staging_dir / f"update_{version}.zip"
        if not await download_release_zip(zip_url, zip_path):
            return False, "Failed to download update"
        
        # Step 3: Extract ZIP
        extract_dir = staging_dir / f"extracted_{version}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        
        if not extract_zip(zip_path, extract_dir):
            return False, "Failed to extract update"
        
        # Step 4: Find Modern/ directory in extracted files
        extracted_root = get_extracted_root(extract_dir)
        if not extracted_root:
            return False, "Could not find Modern directory in update"
        
        # Step 5: Backup current installation
        if not backup_current_installation(backup_dir):
            return False, "Failed to backup current installation"
        
        # Step 6: Apply update
        success, error = apply_update(extracted_root)
        if not success:
            # Try to restore from backup
            restore_from_backup(backup_dir)
            return False, f"Failed to apply update: {error}"
        
        # Step 7: Clean up staging
        try:
            shutil.rmtree(staging_dir)
        except Exception as e:
            _log.debug("Failed to clean staging directory: %s", e)
        
        return True, f"Update to {version} installed successfully. Restart required."
        
    except Exception as e:
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
