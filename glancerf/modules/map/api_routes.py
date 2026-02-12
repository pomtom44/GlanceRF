"""Register map module API routes (propagation data for overlay)."""

import asyncio

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from glancerf.utils.cache import get_cache
from .aprs_client import get_aprs_locations_from_cache
from .propagation_service import get_propagation_coordinates

_log = get_logger("map.api_routes")

_PROPAGATION_CACHE_TTL = 300
_APRS_CACHE_TTL = 300


def register_routes(app: FastAPI) -> None:
    """Register GET /api/map/propagation-data."""

    @app.get("/api/map/propagation-data")
    async def propagation_data(source: str | None = None, hours: float | None = Query(None)):
        """Return propagation coordinates for data-driven overlay. source: kc2g_muf, kc2g_fof2, tropo, or vhf_aprs. For vhf_aprs uses local cache only (no live APRS-IS)."""
        _log.debug("API: GET /api/map/propagation-data source=%s hours=%s", source, hours)
        if source not in ("kc2g_muf", "kc2g_fof2", "tropo", "vhf_aprs"):
            return JSONResponse(
                {"error": "Invalid source", "coordinates": [], "valueLabel": ""},
                status_code=400,
            )
        cache_key = f"map:propagation:{source}|{hours}"
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = await asyncio.to_thread(get_propagation_coordinates, source, hours=hours)
            cache.set(cache_key, result, _PROPAGATION_CACHE_TTL)
            return result
        except Exception as e:
            _log.debug("Propagation data failed: %s", e)
            return JSONResponse(
                {"error": "Failed to fetch propagation data", "coordinates": [], "valueLabel": ""},
                status_code=502,
            )

    @app.get("/api/map/aprs-locations")
    async def aprs_locations(hours: float | None = Query(None)):
        """Return APRS station locations from local cache only (no live APRS-IS). Data from config_dir/cache/aprs.db."""
        _log.debug("API: GET /api/map/aprs-locations hours=%s (cache only)", hours)
        cache_key = f"map:aprs:{hours}"
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            result = await asyncio.to_thread(get_aprs_locations_from_cache, hours=hours)
            cache.set(cache_key, result, _APRS_CACHE_TTL)
            return result
        except Exception as e:
            _log.debug("APRS locations failed: %s", e)
            return JSONResponse({"error": "Failed to fetch APRS locations", "locations": []}, status_code=502)
