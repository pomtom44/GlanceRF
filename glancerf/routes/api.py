"""
API routes for GlanceRF
"""

from fastapi import FastAPI

from glancerf.logging_config import DETAILED_LEVEL, get_logger
from glancerf.telemetry import send_telemetry
from glancerf.time_utils import get_current_time

_log = get_logger("api")


def register_api_routes(app: FastAPI):
    """Register API routes"""

    @app.get("/api/time")
    async def get_time():
        """API endpoint to get current time"""
        _log.log(DETAILED_LEVEL, "API: GET /api/time")
        return get_current_time()
    
    @app.post("/api/telemetry/test")
    async def test_telemetry():
        """Test endpoint to manually trigger telemetry (for debugging)"""
        try:
            result = await send_telemetry("test", {"manual_trigger": True})
            if result:
                return {"status": "success", "message": "Telemetry sent successfully"}
            else:
                return {"status": "failed", "message": "Telemetry send failed (check console for details)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
