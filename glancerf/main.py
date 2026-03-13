"""
FastAPI application for GlanceRF.
Main web server and API endpoints.
"""

import asyncio
import logging
import os
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from glancerf import __version__
from glancerf.config import DETAILED_LEVEL, get_config, get_logger, setup_logging
from glancerf.routes.gpio_routes import register_gpio_routes
from glancerf.routes.layout_routes import register_layout_routes
from glancerf.routes.pages import register_pages
from glancerf.routes.readonly import run_readonly_server
from glancerf.routes.root import register_root
from glancerf.routes.setup_routes import register_setup_routes
from glancerf.routes.websocket import register_websocket_routes
from glancerf.web import ConnectionManager
from glancerf.services import (
    TelemetrySender,
    send_telemetry,
    start_cache_warmer,
    stop_cache_warmer,
    start_aprs_cache,
    stop_aprs_cache,
    start_satellite_services,
    stop_satellite_services,
)
from glancerf.updates.update_checker import (
    UpdateChecker,
    check_for_updates,
    compare_versions,
    get_latest_release_info,
    is_version_ahead,
)
from glancerf.utils import get_current_time, rate_limit_dependency, rate_limit_exceeded_handler, trigger_restart
from glancerf.utils.rate_limit import RateLimitExceeded

_log = get_logger("main")


def _register_module_api_routes():
    """Register API routes from modules that provide api_routes.py."""
    from glancerf.modules import get_module_api_packages
    import importlib
    for pkg in get_module_api_packages():
        try:
            mod = importlib.import_module(pkg + ".api_routes")
            register_routes = getattr(mod, "register_routes", None)
            if callable(register_routes):
                register_routes(app)
                _log.debug("Registered API routes for module: %s", pkg.split(".")[-1])
        except Exception as e:
            _log.warning("Failed to register API routes for %s: %s", pkg, e)

# Load config and set up logging at startup (before first request)
config = get_config()
setup_logging(config)

app = FastAPI(title="GlanceRF")
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

telemetry_sender = TelemetrySender()
connection_manager = ConnectionManager()
update_checker = UpdateChecker(connection_manager)

_project_dir = Path(__file__).resolve().parent.parent


@app.middleware("http")
async def _request_logging(request: Request, call_next):
    """Log each request when log_level is detailed or verbose."""
    if _log.isEnabledFor(DETAILED_LEVEL):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        _log.log(DETAILED_LEVEL, "%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
        return response
    return await call_next(request)


def _get_logo_path():
    """Return path to logo.png: Project/logos/logo.png or workspace root logo.png."""
    p = _project_dir / "logos" / "logo.png"
    if p.is_file():
        return p
    p = _project_dir.parent / "logo.png"
    return p if p.is_file() else None


@app.get("/logo.png", include_in_schema=False)
def _serve_logo():
    """Serve logo.png for favicon and web (taskbar/tab icon)."""
    path = _get_logo_path()
    if path is not None:
        return FileResponse(str(path), media_type="image/png")
    return Response(status_code=404)


_web_static = Path(__file__).resolve().parent / "web" / "static"
if _web_static.is_dir():
    app.mount("/static", StaticFiles(directory=str(_web_static)), name="static")

register_root(app)
register_layout_routes(app, connection_manager)
register_setup_routes(app, connection_manager)
register_gpio_routes(app)
register_pages(app, connection_manager)
register_websocket_routes(app, connection_manager)
_register_module_api_routes()


@app.on_event("startup")
async def _startup():
    """Start background services and set connection reset handler."""
    telemetry_sender.start()
    update_checker.start()
    start_cache_warmer()
    start_aprs_cache()
    start_satellite_services()
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        from glancerf.gpio import set_broadcast, start_gpio_manager
        set_broadcast(connection_manager, loop)
        start_gpio_manager()
    except ImportError:
        pass
    try:
        from glancerf.services.aprs_cache import set_aprs_broadcast
        set_aprs_broadcast(connection_manager, asyncio.get_running_loop())
    except ImportError:
        pass
    _set_connection_reset_handler()


def _set_connection_reset_handler() -> None:
    """Suppress ConnectionResetError when client closes connection (e.g. desktop close)."""
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


@app.on_event("shutdown")
async def _shutdown():
    """Stop background services."""
    telemetry_sender.stop()
    await update_checker.stop()
    stop_aprs_cache()
    stop_satellite_services()
    try:
        from glancerf.gpio import stop_gpio_manager
        stop_gpio_manager()
    except ImportError:
        pass
    stop_cache_warmer()


@app.get("/api/time")
async def get_time():
    """API endpoint for current time (used for startup check)."""
    return get_current_time(config)


@app.get("/api/gps/status")
async def get_gps_status():
    """Return GPS setup status: devices, methods (GPSD, serial), hints for setup page."""
    from glancerf.services.gps_service import get_gps_status as _get_gps_status
    return await asyncio.to_thread(_get_gps_status, config)


@app.get("/api/gps/stats")
async def get_gps_stats():
    """Return GPS stats when connected: lat, lon, time, altitude, speed, track, satellites."""
    from glancerf.services.gps_service import get_gps_stats as _get_gps_stats
    stats = await asyncio.to_thread(_get_gps_stats, config)
    if stats is None:
        return {"connected": False}
    return {"connected": True, **stats}


@app.post("/api/gps/config")
async def save_gps_config(request: Request, _: None = Depends(rate_limit_dependency)):
    """Save GPS source and serial port config."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    gps_source = (body.get("gps_source") or "auto").strip().lower()
    gps_serial_port = (body.get("gps_serial_port") or "").strip()
    if gps_source not in ("gpsd", "serial", "auto"):
        gps_source = "auto"
    config.set("gps_source", gps_source)
    config.set("gps_serial_port", gps_serial_port)
    return {"ok": True}


@app.post("/api/restart")
async def api_restart(_: None = Depends(rate_limit_dependency)):
    """Restart GlanceRF services. Returns immediately; process may exit shortly after."""
    _log.debug("POST /api/restart")
    success, message = trigger_restart()
    if success:

        async def _exit_after_delay():
            await asyncio.sleep(1)
            os._exit(0)

        asyncio.create_task(_exit_after_delay())
    return {"success": success, "message": message}


@app.post("/api/telemetry/test")
async def test_telemetry(_: None = Depends(rate_limit_dependency)):
    """Test endpoint to manually trigger telemetry (for debugging)."""
    result = await send_telemetry("test", {"manual_trigger": True})
    return {"status": "success" if result else "failed", "message": "Telemetry sent" if result else "Telemetry disabled or failed"}


@app.get("/api/update-status")
async def get_update_status():
    """Return current version, latest version (if any), update_available, and release_notes."""
    _log.debug("GET /api/update-status")
    info = await get_latest_release_info()
    current = __version__
    if not info:
        return {"current_version": current, "latest_version": None, "update_available": False, "release_notes": ""}
    latest = info["version"]
    release_notes = info.get("release_notes") or ""
    update_available = compare_versions(current, latest)
    ahead_of_github = is_version_ahead(current, latest)
    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": update_available,
        "ahead_of_github": ahead_of_github,
        "release_notes": release_notes,
        "docker_mode": bool(os.environ.get("GLANCERF_DOCKER")),
    }


@app.post("/api/check-updates")
async def manual_check_updates():
    """Trigger a manual update check. Returns JSON; if update available, broadcasts via WebSocket."""
    _log.debug("POST /api/check-updates")
    latest = await check_for_updates()
    if latest:
        try:
            await connection_manager.broadcast_update_notification({
                "type": "update_available",
                "data": {
                    "current_version": __version__,
                    "latest_version": latest,
                    "docker_mode": bool(os.environ.get("GLANCERF_DOCKER")),
                },
            })
        except Exception as e:
            _log.debug("broadcast_update_notification failed: %s", e)
        return {"update_available": True, "current_version": __version__, "latest_version": latest}
    return {"update_available": False, "current_version": __version__}


@app.get("/api/update-progress")
async def get_update_progress():
    """Return current update progress for the web UI."""
    from glancerf.updates.updater import get_update_progress as _get_progress
    return _get_progress()


@app.post("/api/apply-update")
async def trigger_apply_update(_: None = Depends(rate_limit_dependency)):
    """If an update is available, start the update in the background. Docker: returns message to pull new image."""
    _log.debug("POST /api/apply-update")
    if os.environ.get("GLANCERF_DOCKER"):
        return {
            "success": False,
            "message": "In Docker: pull the new image and recreate the container instead of in-app update.",
            "current_version": __version__,
            "started": False,
        }
    from glancerf.updates.updater import perform_auto_update, get_update_progress

    latest = await check_for_updates()
    if not latest:
        return {"success": False, "message": "No update available", "current_version": __version__, "started": False}
    progress = get_update_progress()
    if progress.get("running"):
        return {"success": False, "message": "Update already in progress", "current_version": __version__, "started": False}

    async def _run_update_then_restart():
        success, message = await perform_auto_update(latest)
        if success:
            await update_checker.schedule_restart(latest, delay_seconds=10)

    asyncio.create_task(_run_update_then_restart())
    return {"success": True, "message": "Update started", "current_version": __version__, "latest_version": latest, "started": True}


def run_server(host: str = "0.0.0.0", port: int = 8080, quiet: bool = False):
    """Run the FastAPI server with Uvicorn."""
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="error",
        access_log=False,
    )
