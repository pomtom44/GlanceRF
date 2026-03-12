"""Background services for satellite_pass module: locations and tracks fetch loops."""

from glancerf.config import get_logger

_log = get_logger("satellite_services")


def start_satellite_services() -> None:
    """Start satellite locations and tracks fetch loops (SatChecker, 1 req/s)."""
    try:
        from glancerf.modules.satellite_pass.satellite_service import (
            start_satellite_locations_fetch_loop,
            start_satellite_tracks_fetch_loop,
        )
        start_satellite_locations_fetch_loop()
        start_satellite_tracks_fetch_loop()
        _log.debug("satellite services: started")
    except ImportError as e:
        _log.debug("satellite services: not available (%s)", e)


def stop_satellite_services() -> None:
    """Stop satellite locations and tracks fetch loops."""
    try:
        from glancerf.modules.satellite_pass.satellite_service import (
            stop_satellite_locations_fetch_loop,
            stop_satellite_tracks_fetch_loop,
        )
        stop_satellite_locations_fetch_loop()
        stop_satellite_tracks_fetch_loop()
        _log.debug("satellite services: stopped")
    except ImportError:
        pass
