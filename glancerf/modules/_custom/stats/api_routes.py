"""
Stats module API: fetches total installs from the telemetry server stats endpoint.
URL and key are hardcoded below; edit this file to match your telemetry server.
"""

from urllib.parse import quote

import httpx
from fastapi import FastAPI

from glancerf.config import get_logger

_log = get_logger("stats.api_routes")

_STATS_TIMEOUT = 10.0
# Obfuscated path under telemetry server (must match telemetry-server/.../installs.php)
_STATS_PATH = "aeiursldkghaslkejfghapeirughadkfjghaldkfjghx9k2m4p6r8s"

# Hardcoded: telemetry server base URL (no trailing slash) and stats secret key (same as $stats_secret_key in installs.php)
TELEMETRY_BASE_URL = "https://glancerf-telemetry.zl4st.com"
STATS_KEY = "KuLp0MfUDtjAyY6r-lfwH0xWAVCf4UrTBtTqljZwuzA"


def _get_stats_api_url() -> str:
    """Stats API URL built from hardcoded base URL, path, and key."""
    base = TELEMETRY_BASE_URL.strip().rstrip("/")
    key = STATS_KEY.strip()
    return f"{base}/{_STATS_PATH}/installs.php?key={quote(key, safe='')}"


def _error_response(message: str):
    return {
        "total_installs": None,
        "seen_24h": None,
        "seen_7d": None,
        "seen_30d": None,
        "countries_seen": None,
        "countries": [],
        "version_breakdown": [],
        "platform_breakdown": [],
        "error": message,
    }


def register_routes(app: FastAPI) -> None:
    """Register GET /api/stats/installs."""

    @app.get("/api/stats/installs")
    async def get_stats_installs():
        """Return total installs from the telemetry server stats endpoint (hardcoded URL + key)."""
        url = _get_stats_api_url()
        try:
            async with httpx.AsyncClient(timeout=_STATS_TIMEOUT) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as e:
            _log.warning("Stats API request failed: %s", e)
            return _error_response("Stats API unavailable")
        except Exception as e:
            _log.warning("Stats API parse failed: %s", e)
            return _error_response("Invalid stats response")
        def _int(v):
            if v is None or not isinstance(v, (int, float)):
                return None
            return int(v)
        def _list(name, default=None):
            val = data.get(name)
            if val is None:
                return default if default is not None else []
            return val if isinstance(val, list) else []
        return {
            "total_installs": _int(data.get("total_installs")),
            "seen_24h": _int(data.get("seen_24h")),
            "seen_7d": _int(data.get("seen_7d")),
            "seen_30d": _int(data.get("seen_30d")),
            "countries_seen": _int(data.get("countries_seen")),
            "countries": _list("countries"),
            "version_breakdown": _list("version_breakdown"),
            "platform_breakdown": _list("platform_breakdown"),
        }
