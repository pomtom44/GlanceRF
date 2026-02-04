"""
API routes for GlanceRF. Core routes only; module-owned API routes are registered via register_module_api_routes.
"""

import importlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from glancerf.logging_config import DETAILED_LEVEL, get_logger
from glancerf.modules import get_module_api_packages
from glancerf.telemetry import send_telemetry
from glancerf.time_utils import get_current_time

_log = get_logger("api")


def register_module_api_routes(app: FastAPI) -> None:
    """Register API routes provided by modules (e.g. satellite_pass). Each module's api_routes.register_routes(app) is called."""
    for pkg in get_module_api_packages():
        try:
            mod = importlib.import_module(pkg + ".api_routes")
            register_routes = getattr(mod, "register_routes", None)
            if callable(register_routes):
                register_routes(app)
                _log.debug("Registered API routes for module package: %s", pkg)
        except Exception as e:
            _log.warning("Failed to register API routes for %s: %s", pkg, e)


def register_api_routes(app: FastAPI):
    """Register API routes"""

    @app.get("/api/time")
    async def get_time():
        """API endpoint to get current time"""
        _log.log(DETAILED_LEVEL, "API: GET /api/time")
        return get_current_time()

    register_module_api_routes(app)

    @app.post("/api/telemetry/test")
    async def test_telemetry():
        """Test endpoint to manually trigger telemetry (for debugging)"""
        _log.debug("POST /api/telemetry/test")
        try:
            result = await send_telemetry("test", {"manual_trigger": True})
            _log.debug("Telemetry test result: %s", result)
            if result:
                return {"status": "success", "message": "Telemetry sent successfully"}
            else:
                return {"status": "failed", "message": "Telemetry send failed (check console for details)"}
        except Exception as e:
            _log.debug("Telemetry test error: %s", e)
            return {"status": "error", "message": str(e)}
