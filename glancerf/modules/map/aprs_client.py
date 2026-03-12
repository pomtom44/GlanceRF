"""
APRS cache reader for VHF propagation overlay (144 MHz), similar to vhf.dxview.org.
Reads from the local cache DB (config_dir/cache/aprs.db) only; no live APRS-IS connection.
Uses aprslib when available for full format support (compressed, @, Mic-E, etc.); falls back
to built-in parser for ! and = uncompressed only.
"""

import math
import sqlite3
import time
from typing import Any

from glancerf.config import get_logger

_log = get_logger("map.aprs_client")

_APRSLIB_AVAILABLE = False
try:
    import aprslib
    _APRSLIB_AVAILABLE = True
except ImportError:
    pass

_DEFAULT_PROPAGATION_HOURS = 6
_MIN_PATH_KM = 20

# Path entries we ignore (not real station callsigns)
_PATH_SKIP = frozenset({"APRS", "TCPIP", "TCPXX", "RELAY", "GATE", "WIDE", "qAR", "qAO", "qAS"})


def _is_skip_call(call: str) -> bool:
    if not call or len(call) < 2:
        return True
    c = call.upper().split("-")[0]
    if c in _PATH_SKIP:
        return True
    if c.startswith("WIDE") or c.startswith("RELAY") or c.startswith("GATE"):
        return True
    if call.startswith("q"):
        return True
    return False


def _parse_aprs_symbol_from_body(body: str) -> tuple[str, str]:
    """Parse APRS symbol table and symbol from position body. Returns (table_char, symbol_char) or ('/', '?') as default."""
    if not body or len(body) < 16:
        return ("/", "?")
    rest = body[1:].strip() if body[0] in ("!", "=") else body.strip()
    sep = rest.find("/")
    if sep < 7 or sep + 10 >= len(rest):
        return ("/", "?")
    table_char = rest[sep] if rest[sep] in ("/", "\\") else "/"
    symbol_char = rest[sep + 10]
    return (table_char, symbol_char)


def _parse_aprs_line_to_position(
    line: str,
) -> tuple[str, float, float, str, str, float | None] | None:
    """
    Parse full TNC2 line to (callsign, lat, lon, symbol_table, symbol, packet_timestamp).
    packet_timestamp: Unix timestamp from packet if present, else None (caller uses received_at).
    Uses aprslib when available (handles compressed, @, Mic-E, etc.); else fallback to built-in.
    Returns None if no position found.
    """
    if _APRSLIB_AVAILABLE:
        try:
            packet = aprslib.parse(line)
            # Skip object/item: position is the reported entity's, not the sender's.
            # Including them causes stations to jump hundreds of km between object positions.
            fmt = packet.get("format") or ""
            if fmt in ("object", "item"):
                return None
            if packet.get("latitude") is not None and packet.get("longitude") is not None:
                lat = float(packet["latitude"])
                lon = float(packet["longitude"])
                if -90 <= lat <= 90 and -180 <= lon <= 180 and (abs(lat) >= 0.02 or abs(lon) >= 0.02):
                    call = (packet.get("from") or "").strip()
                    if call:
                        tbl = packet.get("symbol_table") or "/"
                        sym = packet.get("symbol") or "?"
                        pkt_ts = packet.get("timestamp")
                        if pkt_ts is not None:
                            try:
                                pkt_ts = float(pkt_ts)
                            except (TypeError, ValueError):
                                pkt_ts = None
                        return (call, lat, lon, tbl, sym, pkt_ts)
        except (aprslib.ParseError, aprslib.UnknownFormat):
            pass
        except Exception:
            pass
    parsed = _parse_tnc2(line)
    if not parsed:
        return None
    srccall, _, body = parsed
    pos = _parse_nmea_lat_lon(body)
    if pos is None:
        return None
    lat, lon = pos
    table_char, symbol_char = _parse_aprs_symbol_from_body(body)
    return (srccall, lat, lon, table_char, symbol_char, None)


def _parse_nmea_lat_lon(body: str) -> tuple[float, float] | None:
    """Parse NMEA-style position from body: !DDMM.MMN/DDDMM.MMW or =DDMM.MMN/DDDMM.MMW."""
    if not body or len(body) < 15:
        return None
    first = body[0]
    if first not in ("!", "="):
        return None
    rest = body[1:].strip()
    sep = rest.find("/")
    if sep < 7 or sep + 9 > len(rest):
        return None
    lat_str = rest[:sep].rstrip()
    lon_str = rest[sep + 1 : sep + 10].rstrip()
    try:
        lat_dir = ""
        if lat_str and lat_str[-1] in ("N", "n", "S", "s"):
            lat_dir = lat_str[-1].upper()
            lat_str = lat_str[:-1]
        lat_deg = int(lat_str[:2])
        lat_min = float(lat_str[2:]) if len(lat_str) > 2 else 0.0
        lat = lat_deg + lat_min / 60.0
        if lat_dir == "S":
            lat = -lat
        lon_dir = ""
        if lon_str and lon_str[-1] in ("E", "e", "W", "w"):
            lon_dir = lon_str[-1].upper()
            lon_str = lon_str[:-1]
        lon_deg = int(lon_str[:3])
        lon_min = float(lon_str[3:]) if len(lon_str) > 3 else 0.0
        lon = lon_deg + lon_min / 60.0
        if lon_dir == "W":
            lon = -lon
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            if abs(lat) < 0.02 and abs(lon) < 0.02:
                return None
            return (lat, lon)
    except (ValueError, IndexError):
        pass
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _parse_tnc2(line: str) -> tuple[str, list[str], str] | None:
    """Parse TNC2 line: SRCCALL>DST,PATH1,PATH2:body. Returns (srccall, path_calls, body) or None."""
    idx = line.find(":")
    if idx < 0:
        return None
    head = line[:idx]
    body = line[idx + 1 :].strip()
    gt = head.find(">")
    if gt < 0:
        return None
    srccall = head[:gt].strip()
    path_part = head[gt + 1 :].strip()
    path_calls = [p.strip().rstrip("*") for p in path_part.split(",") if p.strip()]
    return (srccall, path_calls, body)


def _segments_to_coords(segments: list[tuple[float, float, float, float, float, float]]) -> list[list[float]]:
    """Rasterize segments to overlay points (endpoints + midpoints, value = distance km)."""
    coords: list[list[float]] = []
    for lat1, lon1, lat2, lon2, dist, _ in segments:
        coords.append([lon1, lat1, dist])
        coords.append([lon2, lat2, dist])
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        coords.append([mid_lon, mid_lat, dist])
    return coords


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Graham scan: return hull as list of (lat, lon) in counter-clockwise order. Uses (lon, lat) as (x,y)."""
    pts = list(set(points))
    if len(pts) < 3:
        return pts
    # Bottom-most then left-most (smallest lat, then smallest lon)
    start = min(pts, key=lambda p: (p[0], p[1]))
    rest = [p for p in pts if p != start]

    def polar_key(p: tuple[float, float]) -> tuple[float, float]:
        # Sort by angle from start; use atan2(lat - start_lat, lon - start_lon)
        return (math.atan2(p[0] - start[0], p[1] - start[1]), p[0], p[1])

    rest.sort(key=polar_key)
    hull: list[tuple[float, float]] = [start]
    for p in rest:
        while len(hull) >= 2:
            a, b = hull[-2], hull[-1]
            # Cross (b - a) x (p - b) in (lon, lat) = (x, y): (b_lon - a_lon)*(p_lat - b_lat) - (b_lat - a_lat)*(p_lon - b_lon)
            cross = (b[1] - a[1]) * (p[0] - b[0]) - (b[0] - a[0]) * (p[1] - b[1])
            if cross <= 0:
                hull.pop()
            else:
                break
        hull.append(p)
    return hull


def _segments_to_blobs(segments: list[tuple[float, float, float, float, float, float]]) -> list[dict[str, Any]]:
    """
    One blob per receiving tower from segments (consecutive path hops). Used as fallback.
    """
    key_to_points: dict[tuple[float, float], set[tuple[float, float]]] = {}
    key_to_max_dist: dict[tuple[float, float], float] = {}
    for lat1, lon1, lat2, lon2, dist, _ in segments:
        k1 = (round(lat1, 4), round(lon1, 4))
        k2 = (round(lat2, 4), round(lon2, 4))
        if k1 not in key_to_points:
            key_to_points[k1] = {k1}
        key_to_points[k1].add(k2)
        if k2 not in key_to_points:
            key_to_points[k2] = {k2}
        key_to_points[k2].add(k1)
        key_to_max_dist[k1] = max(key_to_max_dist.get(k1, 0), dist)
        key_to_max_dist[k2] = max(key_to_max_dist.get(k2, 0), dist)
    blobs: list[dict[str, Any]] = []
    for (lat, lon), pts in key_to_points.items():
        if len(pts) < 3:
            continue
        hull = _convex_hull(list(pts))
        if len(hull) < 3:
            continue
        hull_list = [[float(p[0]), float(p[1])] for p in hull]
        max_dist = key_to_max_dist.get((lat, lon), 0)
        blobs.append({"lat": lat, "lon": lon, "hull": hull_list, "maxDist": max_dist})
    return blobs


def _heard_by_to_blobs(
    positions: dict[str, tuple[float, float, float]],
    digi_points: dict[tuple[float, float], set[tuple[float, float]]],
) -> list[dict[str, Any]]:
    """
    One blob per tower (station with position): for each station D that has a position,
    collect all (lat, lon) of sources S of packets where D appeared in the path (D "heard" S).
    Then convex hull of tower + heard points. Matches DXView-style coverage (many more blobs).
    """
    blobs: list[dict[str, Any]] = []
    for (lat, lon), heard in digi_points.items():
        points = {(lat, lon)} | heard
        if len(points) < 3:
            continue
        hull = _convex_hull(list(points))
        if len(hull) < 3:
            continue
        max_dist = 0.0
        for p in points:
            d = _haversine_km(lat, lon, p[0], p[1])
            if d > max_dist:
                max_dist = d
        hull_list = [[float(p[0]), float(p[1])] for p in hull]
        blobs.append({"lat": lat, "lon": lon, "hull": hull_list, "maxDist": max_dist})
    return blobs


def get_aprs_propagation_data_from_cache(hours: float | None = None) -> dict[str, Any]:
    """
    Return VHF propagation overlay data from the local APRS cache DB only (no live APRS-IS).
    Reads from config_dir/cache/aprs.db. hours: optional override (e.g. 1, 6, 12, 24); if None,
    uses config aprs_propagation_hours or default 6. Parses TNC2, builds position cache and
    long-path segments, then rasterizes to points.
    """
    from glancerf.config import get_config
    config = get_config()
    db_path = config.config_dir / "cache" / "aprs.db"
    if not db_path.is_file():
        _log.debug("APRS cache DB not found: %s", db_path)
        return {"coordinates": [], "segments": [], "towers": [], "blobs": [], "valueLabel": "VHF path km"}
    if hours is None:
        hours = config.get("aprs_propagation_hours")
    if hours is None:
        hours = _DEFAULT_PROPAGATION_HOURS
    try:
        hours = float(hours)
        hours = max(0.25, min(168, hours))
    except (TypeError, ValueError):
        hours = _DEFAULT_PROPAGATION_HOURS
    now = time.time()
    cutoff = now - (hours * 3600)
    positions: dict[str, tuple[float, float, float]] = {}
    segments: list[tuple[float, float, float, float, float, float]] = []
    rows: list[tuple[str, float]] = []
    try:
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT raw, received_at FROM packets WHERE received_at >= ? ORDER BY received_at",
            (cutoff,),
        )
        rows = [(row["raw"], row["received_at"]) for row in cur]
        conn.close()
        for line, received_at in rows:
            pos_result = _parse_aprs_line_to_position(line)
            if pos_result is None:
                continue
            srccall, lat, lon, _, _, _ = pos_result
            positions[srccall] = (lat, lon, received_at)
            parsed = _parse_tnc2(line)
            path_calls = parsed[1] if parsed else []
            path_stations = [srccall] + [p for p in path_calls if not _is_skip_call(p)]
            for i in range(len(path_stations) - 1):
                a, b = path_stations[i], path_stations[i + 1]
                pa = positions.get(a)
                pb = positions.get(b)
                if pa is None or pb is None:
                    continue
                lat1, lon1, _ = pa
                lat2, lon2, _ = pb
                dist = _haversine_km(lat1, lon1, lat2, lon2)
                segments.append((lat1, lon1, lat2, lon2, dist, received_at))
        digi_points: dict[tuple[float, float], set[tuple[float, float]]] = {}
        for line, received_at in rows:
            pos_result = _parse_aprs_line_to_position(line)
            if pos_result is None:
                continue
            srccall, lat_s, lon_s, _, _, _ = pos_result
            parsed = _parse_tnc2(line)
            path_calls = parsed[1] if parsed else []
            path_stations = [srccall] + [p for p in path_calls if not _is_skip_call(p)]
            for d in path_stations:
                if d not in positions:
                    continue
                lat_d, lon_d, _ = positions[d]
                dist_km = _haversine_km(lat_d, lon_d, lat_s, lon_s)
                if dist_km < _MIN_PATH_KM:
                    continue
                key = (round(lat_d, 3), round(lon_d, 3))
                if key not in digi_points:
                    digi_points[key] = set()
                digi_points[key].add((lat_s, lon_s))
        blobs = _heard_by_to_blobs(positions, digi_points)
        if not blobs:
            blobs = _segments_to_blobs(segments)
    except (sqlite3.Error, OSError) as e:
        _log.debug("APRS cache read failed: %s", e)
        return {"coordinates": [], "segments": [], "towers": [], "blobs": [], "valueLabel": "VHF path km"}
    coords = _segments_to_coords(segments)
    # Segments for line overlay fallback: [lon1, lat1, lon2, lat2, dist_km]
    segment_list = [[lon1, lat1, lon2, lat2, dist] for (lat1, lon1, lat2, lon2, dist, _) in segments]
    return {"coordinates": coords, "segments": segment_list, "blobs": blobs, "valueLabel": "VHF path km"}


def _apply_aprs_filter(locations: list[dict[str, Any]], filter_str: str | None) -> list[dict[str, Any]]:
    """Filter locations by APRS-IS filter (p/PREFIX, p/P1/P2, or b/PREFIX*). Returns locations where callsign starts with a prefix."""
    if not filter_str or not locations:
        return locations
    prefixes: list[str] = []
    for part in filter_str.split():
        if part.startswith("p/"):
            for p in part[2:].split("/"):
                if p:
                    prefixes.append(p.upper())
        elif part.startswith("b/"):
            for p in part[2:].split("/"):
                p = (p or "").rstrip("*").strip()
                if p:
                    prefixes.append(p.upper())
    if not prefixes:
        return locations
    result = []
    for loc in locations:
        call = (loc.get("callsign") or "").upper().split("-")[0]
        for prefix in prefixes:
            if call.startswith(prefix):
                result.append(loc)
                break
    return result


def get_aprs_locations_from_cache(
    hours: float | None = None,
    filter_str: str | None = None,
) -> dict[str, Any]:
    """
    Return APRS station locations from the local cache only (no live APRS-IS).
    Reads from config_dir/cache/aprs.db. One entry per callsign with position; uses latest position in the time window.
    filter_str: optional APRS-IS filter (e.g. p/W1 p/VE) to restrict by callsign prefix.
    """
    from glancerf.config import get_config
    config = get_config()
    db_path = config.config_dir / "cache" / "aprs.db"
    if not db_path.is_file():
        _log.debug("APRS cache DB not found: %s", db_path)
        return {"locations": []}
    if hours is None:
        hours = config.get("aprs_propagation_hours")
    if hours is None:
        hours = _DEFAULT_PROPAGATION_HOURS
    try:
        hours = float(hours)
        hours = max(0.25, min(168, hours))
    except (TypeError, ValueError):
        hours = _DEFAULT_PROPAGATION_HOURS
    cutoff = time.time() - (hours * 3600)
    positions: dict[str, tuple[float, float, float]] = {}
    try:
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id, raw, received_at FROM packets WHERE received_at >= ? ORDER BY received_at, id",
            (cutoff,),
        )
        for row in cur:
            line = row["raw"]
            received_at = row["received_at"]
            parsed = _parse_aprs_line_to_position(line)
            if parsed is None:
                continue
            srccall, lat, lon, table_char, symbol_char, packet_ts = parsed
            # Use packet timestamp when available (station transmit time) for stable ordering;
            # received_at can cause jumping when packets arrive out of order.
            effective_ts = packet_ts if packet_ts is not None else received_at
            if srccall not in positions or effective_ts > positions[srccall][2]:
                positions[srccall] = (lat, lon, effective_ts, table_char, symbol_char)
        conn.close()
    except (sqlite3.Error, OSError) as e:
        _log.debug("APRS cache read failed: %s", e)
        return {"locations": []}
    locations = [
        {
            "callsign": call,
            "lat": lat,
            "lon": lon,
            "lastSeen": ts,
            "symbolTable": table_char,
            "symbol": symbol_char,
        }
        for call, (lat, lon, ts, table_char, symbol_char) in positions.items()
    ]
    locations = _apply_aprs_filter(locations, filter_str)
    return {"locations": locations}
