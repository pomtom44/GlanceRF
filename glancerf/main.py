"""
FastAPI application for GlanceRF
Main web server and API endpoints
"""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from glancerf.config import get_config
from glancerf.logging_config import get_logger, setup_logging
from glancerf.rate_limit import RateLimitExceeded, rate_limit_exceeded_handler
from glancerf.websocket_manager import ConnectionManager
from glancerf.update_checker import UpdateChecker
from glancerf.telemetry import TelemetrySender
from glancerf.routes import api, websocket, layout_routes, setup_routes
from glancerf.routes.root import register_root
from glancerf.routes.readonly import run_readonly_server
from glancerf.routes.modules_routes import register_modules_routes
from glancerf.routes.config_routes import register_config_routes

# Initialize FastAPI app
app = FastAPI(title="GlanceRF")
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Request logging middleware (verbose level only: logs method, path, status, duration at DEBUG)
_log = get_logger("main")


@app.middleware("http")
async def _request_logging(request: Request, call_next):
    if _log.isEnabledFor(logging.DEBUG):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        _log.debug("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
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
register_modules_routes(app)
register_config_routes(app, connection_manager)
api.register_api_routes(app)
websocket.register_websocket_routes(app, connection_manager)


@app.on_event("startup")
async def _start_background_tasks():
    """Start background tasks."""
    update_checker.start()
    telemetry_sender.start()


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
