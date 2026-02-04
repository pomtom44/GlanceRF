"""
FastAPI application for GlanceRF
Main web server and API endpoints
"""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from glancerf.config import get_config
from glancerf.logging_config import DETAILED_LEVEL, get_logger, setup_logging
from glancerf.rate_limit import RateLimitExceeded, rate_limit_exceeded_handler
from glancerf.websocket_manager import ConnectionManager
from glancerf import __version__
from glancerf.update_checker import UpdateChecker, check_for_updates, get_latest_release_info, compare_versions
from glancerf.telemetry import TelemetrySender
from glancerf.aprs_cache import start_aprs_cache
from glancerf.routes import api, websocket, layout_routes, setup_routes
from glancerf.routes.root import register_root
from glancerf.routes.readonly import run_readonly_server
from glancerf.routes.modules_routes import register_modules_routes

# Initialize FastAPI app
app = FastAPI(title="GlanceRF")
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Request logging: one [DETAILED] line per request when log_level is detailed or verbose
_log = get_logger("main")


@app.middleware("http")
async def _request_logging(request: Request, call_next):
    if _log.isEnabledFor(DETAILED_LEVEL):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        _log.log(DETAILED_LEVEL, "%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
        return response
    return await call_next(request)

# Serve static assets (CSS, JS) from glancerf/web/static
_web_static = Path(__file__).resolve().parent / "web" / "static"
if _web_static.is_dir():
    app.mount("/static", StaticFiles(directory=str(_web_static)), name="static")


@app.on_event("startup")
def _set_connection_reset_handler():
    """Suppress ConnectionResetError when client closes WebSocket (e.g. desktop close)."""
    import asyncio
    import logging

    def handler(loop, ctx):
        ex = ctx.get("exception")
        if ex is not None and isinstance(ex, (ConnectionResetError, OSError)):
            if getattr(ex, "winerror", None) == 10054 or "10054" in str(ex):
                return
            if "forcibly closed" in str(ex).lower() or "Connection reset" in str(ex):
                return
        if ex is not None:
            logging.getLogger("asyncio").exception(
                "Exception in async callback: %s", ctx.get("message", ""),
                exc_info=(type(ex), ex, getattr(ex, "__traceback__", None)),
            )
        else:
            logging.getLogger("asyncio").error("Async context: %s", ctx)

    try:
        asyncio.get_running_loop().set_exception_handler(handler)
    except RuntimeError:
        pass


# Config is loaded on first get_config(); if file is missing, default config is used and saved
config = get_config()
setup_logging(config)

# Global connection manager
connection_manager = ConnectionManager()

# Global update checker
update_checker = UpdateChecker(connection_manager)

# Global telemetry sender
telemetry_sender = TelemetrySender()

# Register all routes
register_root(app)
layout_routes.register_layout_routes(app, connection_manager)
setup_routes.register_setup_routes(app, connection_manager)
register_modules_routes(app, connection_manager)
api.register_api_routes(app)
websocket.register_websocket_routes(app, connection_manager)

_UPDATES_TEMPLATE_PATH = Path(__file__).resolve().parent / "web" / "templates" / "updates" / "index.html"
_updates_template_cache = None


@app.get("/updates", response_class=HTMLResponse)
async def updates_page():
    """Updates page: check for updates, show current/latest version and release notes, trigger update."""
    global _updates_template_cache
    if _updates_template_cache is None and _UPDATES_TEMPLATE_PATH.is_file():
        _updates_template_cache = _UPDATES_TEMPLATE_PATH.read_text(encoding="utf-8")
    if _updates_template_cache is None:
        return HTMLResponse(content="<h1>Updates</h1><p>Template not found.</p>", status_code=500)
    return HTMLResponse(content=_updates_template_cache)


@app.get("/api/update-status")
async def get_update_status():
    """Return current version, latest version (if any), update_available, and release_notes. No broadcast."""
    _log.debug("GET /api/update-status")
    info = await get_latest_release_info()
    current = __version__
    if not info:
        _log.debug("update-status: no release info; current=%s", current)
        return {"current_version": current, "latest_version": None, "update_available": False, "release_notes": ""}
    latest = info["version"]
    release_notes = info.get("release_notes") or ""
    update_available = compare_versions(current, latest)
    _log.debug("update-status: current=%s latest=%s update_available=%s", current, latest, update_available)
    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": update_available,
        "release_notes": release_notes,
    }


@app.post("/api/check-updates")
async def manual_check_updates():
    """Trigger a manual update check. Returns JSON; if update available also broadcasts via WebSocket."""
    _log.debug("POST /api/check-updates")
    latest = await check_for_updates()
    if latest:
        _log.debug("check-updates: update available %s, sending notification", latest)
        await update_checker.send_update_notification(latest, "notify")
        return {"update_available": True, "current_version": __version__, "latest_version": latest}
    _log.debug("check-updates: no update available (current=%s)", __version__)
    return {"update_available": False, "current_version": __version__}


@app.post("/api/apply-update")
async def trigger_apply_update():
    """If an update is available, download and apply it (then restart). Returns JSON status."""
    from glancerf.updater import perform_auto_update

    _log.debug("POST /api/apply-update")
    latest = await check_for_updates()
    if not latest:
        _log.debug("apply-update: no update available (current=%s)", __version__)
        return {"success": False, "message": "No update available", "current_version": __version__}
    _log.debug("apply-update: starting update to %s", latest)
    success, message = await perform_auto_update(latest)
    _log.debug("apply-update: success=%s message=%s", success, message)
    if success:
        await update_checker.schedule_restart(delay_seconds=10)
        _log.debug("apply-update: restart scheduled")
    return {
        "success": success,
        "message": message,
        "current_version": __version__,
        "latest_version": latest,
    }


@app.on_event("startup")
async def _start_background_tasks():
    """Start background tasks."""
    update_checker.start()
    telemetry_sender.start()
    start_aprs_cache()


@app.on_event("shutdown")
async def _stop_background_tasks():
    """Stop background tasks."""
    update_checker.stop()
    telemetry_sender.stop()


def run_server(host: str = "0.0.0.0", port: int = 8080, quiet: bool = False):
    """Run the FastAPI server"""
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="error",
        access_log=False
    )
