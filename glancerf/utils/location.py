"""Parse location strings (grid square or lat,lng) to (lat, lng). Used by modules that need coordinates."""

import re
from typing import Any


def parse_location(s: str) -> tuple[float, float] | None:
    """Parse grid square (Maidenhead) or 'lat,lng' to (lat, lng). Returns None if invalid."""
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", s)
    if m:
        lat, lng = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return (lat, lng)
        return None
    s_upper = s.upper()
    if len(s_upper) < 2:
        return None
    try:
        c0 = ord(s_upper[0]) - 65
        c1 = ord(s_upper[1]) - 65
        if not (0 <= c0 <= 17 and 0 <= c1 <= 17):
            return None
        lon = -180 + c0 * 20 + 10
        lat = -90 + c1 * 10 + 5
        if len(s_upper) >= 4 and s_upper[2].isdigit() and s_upper[3].isdigit():
            lon = -180 + c0 * 20 + (int(s_upper[2]) * 2) + 1
            lat = -90 + c1 * 10 + int(s_upper[3]) + 0.5
        if len(s_upper) >= 6:
            sx = s_upper[4].lower()
            sy = s_upper[5].lower()
            if "a" <= sx <= "x" and "a" <= sy <= "x":
                s0 = ord(sx) - 97
                s1 = ord(sy) - 97
                lon = -180 + c0 * 20 + (int(s_upper[2]) * 2) + (s0 + 0.5) * (2 / 24)
                lat = -90 + c1 * 10 + int(s_upper[3]) + (s1 + 0.5) * (1 / 24)
        return (lat, lon)
    except (ValueError, IndexError):
        return None


def get_effective_location(config: Any) -> tuple[float, float] | None:
    """
    Get effective system location. If gps_location_enabled and GPS has fix, use GPS.
    Otherwise use setup_location from config. Returns (lat, lon) or None.
    """
    if config.get("gps_location_enabled"):
        try:
            from glancerf.services.gps_service import get_gps_location
            coords = get_gps_location(config)
            if coords is not None:
                return coords
        except Exception:
            pass
    loc_str = (config.get("setup_location") or "").strip()
    return parse_location(loc_str)


def get_effective_location_string(config: Any) -> str:
    """
    Get effective location as string for frontend (grid square or lat,lon).
    Uses GPS when gps_location_enabled, else setup_location.
    """
    coords = get_effective_location(config)
    if coords is not None:
        return f"{coords[0]},{coords[1]}"
    return (config.get("setup_location") or "").strip()
