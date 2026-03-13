"""
GPS service supporting multiple sources: GPSD, direct serial (NMEA), and auto-detection.
"""

import glob
import platform
import re
import socket
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from glancerf.config import get_config, get_logger

_log = get_logger("gps_service")

_GPS_READ_TIMEOUT_SEC = 2.0
_GPS_HOST = "127.0.0.1"
_GPS_PORT = 2947
_SERIAL_PROBE_BAUD = 9600
_SERIAL_PROBE_TIMEOUT = 2.0
_NMEA_LAT_RE = re.compile(r"^(\d{2})(\d{2}\.\d+)$")   # ddmm.mmmm
_NMEA_LON_RE = re.compile(r"^(\d{3})(\d{2}\.\d+)$")   # dddmm.mmmm


def _detect_devices_linux() -> list[dict[str, str]]:
    """Detect potential GPS serial devices on Linux."""
    devices: list[dict[str, str]] = []
    patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS*", "/dev/ttyAMA*"]
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            devices.append({"path": path, "description": path})
    return devices


def _detect_devices_windows() -> list[dict[str, str]]:
    """Detect COM ports on Windows. Requires pyserial for list_ports."""
    devices: list[dict[str, str]] = []
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            desc = port.description or port.device
            devices.append({"path": port.device, "description": desc})
    except ImportError:
        _log.debug("pyserial not installed; COM port detection unavailable on Windows")
    except Exception as e:
        _log.debug("COM port enumeration failed: %s", e)
    return devices


def _detect_devices() -> list[dict[str, str]]:
    """Detect potential GPS devices for current OS."""
    system = platform.system().lower()
    if system == "linux":
        return _detect_devices_linux()
    if system == "windows":
        return _detect_devices_windows()
    # Darwin (macOS), etc. - try Linux-style paths
    return _detect_devices_linux()


def _nmea_lat_to_decimal(nmea: str, ns: str) -> Optional[float]:
    """Convert NMEA lat (ddmm.mmmm) + N/S to decimal degrees."""
    m = _NMEA_LAT_RE.match((nmea or "").strip())
    if not m:
        return None
    d, rest = int(m.group(1)), float(m.group(2))
    deg = d + rest / 60.0
    if ns and ns.upper() == "S":
        deg = -deg
    return deg if -90 <= deg <= 90 else None


def _nmea_lon_to_decimal(nmea: str, ew: str) -> Optional[float]:
    """Convert NMEA lon (dddmm.mmmm) + E/W to decimal degrees."""
    m = _NMEA_LON_RE.match((nmea or "").strip())
    if not m:
        return None
    d, rest = int(m.group(1)), float(m.group(2))
    deg = d + rest / 60.0
    if ew and ew.upper() == "W":
        deg = -deg
    return deg if -180 <= deg <= 180 else None


def _parse_nmea_line(line: str) -> Optional[dict]:
    """Parse NMEA sentence to dict with lat, lon, time. Returns None if invalid."""
    line = (line or "").strip()
    if not line.startswith("$") or "*" not in line:
        return None
    parts = line.split("*")[0].split(",")
    if len(parts) < 10:
        return None
    sentence = parts[0]
    result: dict[str, Any] = {}
    if "GPRMC" in sentence or "GNRMC" in sentence:
        # $GPRMC,hhmmss.ss,A,lat,N/S,lon,E/W,speed,course,ddmmyy,,,*cs
        if len(parts) < 7:
            return None
        if parts[2] != "A":
            return None
        lat = _nmea_lat_to_decimal(parts[3], parts[4])
        lon = _nmea_lon_to_decimal(parts[5], parts[6])
        if lat is not None and lon is not None:
            result["lat"] = lat
            result["lon"] = lon
        if len(parts) >= 8 and parts[7]:
            try:
                result["speed"] = float(parts[7]) * 0.514444  # knots to m/s
            except (ValueError, TypeError):
                pass
        if len(parts) >= 9 and parts[8]:
            try:
                result["track"] = float(parts[8])
            except (ValueError, TypeError):
                pass
        if len(parts) >= 2 and parts[1]:
            t = parts[1][:6]
            if len(t) == 6 and t.isdigit():
                h, m, s = int(t[:2]), int(t[2:4]), int(t[4:6])
                if len(parts) >= 10 and parts[9]:
                    d = parts[9][:6]
                    if len(d) == 6 and d.isdigit():
                        day, month, year = int(d[:2]), int(d[2:4]), int(d[4:6])
                        year += 2000 if year < 80 else 1900
                        result["time"] = datetime(year, month, day, h, m, s, tzinfo=timezone.utc)
    elif "GPGGA" in sentence or "GNGGA" in sentence:
        # $GPGGA,hhmmss.ss,lat,N/S,lon,E/W,quality,numsats,hdop,alt,M,,,*cs
        if len(parts) < 7:
            return None
        if parts[6] == "0":
            return None
        lat = _nmea_lat_to_decimal(parts[2], parts[3])
        lon = _nmea_lon_to_decimal(parts[4], parts[5])
        if lat is not None and lon is not None:
            result["lat"] = lat
            result["lon"] = lon
        if len(parts) >= 2 and parts[1]:
            t = parts[1][:6]
            if len(t) >= 6:
                h = int(t[:2]) if len(t) > 0 else 0
                m = int(t[2:4]) if len(t) > 4 else 0
                s = int(t[4:6]) if len(t) > 6 else 0
                today = datetime.now(timezone.utc).date()
                result["time"] = datetime(today.year, today.month, today.day, h, m, s, tzinfo=timezone.utc)
        if len(parts) >= 8 and parts[7]:
            try:
                result["satellites"] = int(parts[7])
            except (ValueError, TypeError):
                pass
        if len(parts) >= 10 and parts[9]:
            try:
                result["alt"] = float(parts[9])
            except (ValueError, TypeError):
                pass
    return result if result else None


def _read_serial_nmea(port: str) -> Optional[dict]:
    """Read NMEA from serial port. Returns dict with lat, lon, time, speed, track, alt, satellites or None."""
    try:
        import serial
    except ImportError:
        _log.debug("pyserial not installed; direct serial GPS unavailable")
        return None
    result: list[Optional[dict]] = [None]

    def _reader():
        try:
            import time as _t
            merged: dict[str, Any] = {}
            with serial.Serial(port, _SERIAL_PROBE_BAUD, timeout=1.0) as ser:
                end = _t.monotonic() + _SERIAL_PROBE_TIMEOUT
                buf = ""
                while _t.monotonic() < end:
                    if ser.in_waiting:
                        buf += ser.read(ser.in_waiting).decode("ascii", errors="ignore")
                    lines = buf.split("\n")
                    buf = lines[-1]
                    for line in lines[:-1]:
                        parsed = _parse_nmea_line(line)
                        if parsed:
                            merged.update({k: v for k, v in parsed.items() if v is not None})
                            if "lat" in merged and "lon" in merged:
                                result[0] = merged
                                return
                    _t.sleep(0.1)
        except Exception as e:
            _log.debug("Serial read %s failed: %s", port, e)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=_SERIAL_PROBE_TIMEOUT + 0.5)
    return result[0]


def _probe_serial_for_gps(port: str) -> bool:
    """Probe serial port for NMEA output. Returns True if GPS detected."""
    return _read_serial_nmea(port) is not None


def _check_gpsd_connection() -> tuple[bool, bool]:
    """Check if GPSD is reachable and has a fix. Returns (connected, has_fix)."""
    try:
        from gpsdclient import GPSDClient
    except ImportError:
        return (False, False)
    result: list[Optional[dict]] = [None]

    def _reader():
        try:
            with GPSDClient(host=_GPS_HOST, port=_GPS_PORT) as client:
                for report in client.dict_stream(convert_datetime=True, filter=["TPV"]):
                    result[0] = report
                    return
        except Exception:
            pass

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=_GPS_READ_TIMEOUT_SEC)
    if result[0] is None:
        return (False, False)
    mode = result[0].get("mode", 0)
    has_fix = mode >= 2 and result[0].get("lat") is not None and result[0].get("lon") is not None
    return (True, has_fix)


def _check_gpsd_port_open() -> bool:
    """Quick check if something is listening on GPSD port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((_GPS_HOST, _GPS_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_gps_status(config: Optional[Any] = None) -> dict[str, Any]:
    """
    Return GPS setup status for the setup page: devices, methods (GPSD, serial), hints.
    Probes all methods and reports which work.
    """
    if config is None:
        try:
            config = get_config()
        except Exception:
            config = {}
    system = platform.system().lower()
    is_windows = system == "windows"
    is_linux = system == "linux"
    gps_source = (config.get("gps_source") or "auto").lower()
    gps_serial_port = (config.get("gps_serial_port") or "").strip()

    # Check gpsdclient
    try:
        import gpsdclient
        gpsdclient_installed = True
    except ImportError:
        gpsdclient_installed = False

    # Detect devices
    devices = _detect_devices()

    # Check GPSD
    port_open = _check_gpsd_port_open()
    gpsd_connected = False
    gpsd_has_fix = False
    if port_open and gpsdclient_installed:
        gpsd_connected, gpsd_has_fix = _check_gpsd_connection()

    # Probe serial ports for NMEA
    serial_ports_with_gps: list[dict[str, str]] = []
    try:
        import serial
        pyserial_available = True
    except ImportError:
        pyserial_available = False
    if pyserial_available and devices:
        for d in devices[:8]:
            path = d.get("path", "")
            if path and _probe_serial_for_gps(path):
                serial_ports_with_gps.append({"path": path, "description": d.get("description", path)})

    # Build methods
    methods: list[dict[str, Any]] = []
    methods.append({
        "id": "gpsd",
        "name": "GPSD",
        "available": gpsdclient_installed,
        "working": gpsd_connected,
        "has_fix": gpsd_has_fix,
        "detail": "GPSD daemon (localhost:2947)" if gpsdclient_installed else "Install gpsdclient",
    })
    methods.append({
        "id": "serial",
        "name": "Direct serial (NMEA)",
        "available": pyserial_available and bool(devices),
        "working": len(serial_ports_with_gps) > 0,
        "has_fix": len(serial_ports_with_gps) > 0,
        "ports_with_gps": [p["path"] for p in serial_ports_with_gps],
        "detail": ", ".join(p["path"] for p in serial_ports_with_gps[:5]) if serial_ports_with_gps else "No NMEA detected on serial ports",
    })

    # Overall status
    best_ok = gpsd_connected and gpsd_has_fix
    serial_ok = len(serial_ports_with_gps) > 0
    if best_ok or serial_ok:
        status = "ok"
    elif gpsd_connected or (port_open and gpsdclient_installed):
        status = "gpsd_no_fix"
    elif serial_ports_with_gps:
        status = "serial_no_fix"
    elif port_open:
        status = "gpsd_no_data"
    elif devices and (gpsdclient_installed or pyserial_available):
        status = "gpsd_not_running"
    elif not gpsdclient_installed and not pyserial_available:
        status = "gpsdclient_missing"
    elif not devices:
        status = "no_devices"
    else:
        status = "disabled"

    # Build hints
    hints: list[str] = []
    if not gpsdclient_installed:
        hints.append("Install gpsdclient for GPSD: pip install gpsdclient")
    if not pyserial_available:
        hints.append("Install pyserial for direct serial: pip install pyserial")
    if not devices:
        if is_linux:
            hints.append("No serial devices found. Connect a USB GPS receiver (e.g. /dev/ttyUSB0).")
            hints.append("Ensure udev rules allow access: sudo usermod -aG dialout $USER")
        else:
            hints.append("No COM ports detected. Connect a USB GPS receiver.")
    else:
        dev_list = ", ".join(d["path"] for d in devices[:5])
        if len(devices) > 5:
            dev_list += ", ..."
        hints.append(f"Detected devices: {dev_list}")
    if serial_ports_with_gps:
        hints.append("Direct serial found NMEA on: " + ", ".join(p["path"] for p in serial_ports_with_gps[:5]))
    if not port_open and devices and not serial_ports_with_gps:
        if is_linux:
            hints.append("Option A: Start GPSD: sudo gpsd -N -n /dev/ttyUSB0")
            hints.append("Option B: Use direct serial – set gps_source to 'serial' and choose port in Setup")
        else:
            hints.append("Option A: Use GPSD for Windows (Cygwin) or WSL")
            hints.append("Option B: Use direct serial – set gps_source to 'serial' and choose COM port")
    if port_open and not gpsd_connected:
        hints.append("GPSD port open but no data. Try direct serial or wait for fix.")
    if gpsd_connected and not gpsd_has_fix:
        hints.append("GPSD connected but no fix yet. Wait for satellite lock.")

    return {
        "status": status,
        "os": system,
        "gps_source": gps_source,
        "gps_serial_port": gps_serial_port,
        "gpsdclient_installed": gpsdclient_installed,
        "gpsd_port_open": port_open,
        "gpsd_connected": gpsd_connected,
        "gpsd_has_fix": gpsd_has_fix,
        "serial_ports_with_gps": serial_ports_with_gps,
        "methods": methods,
        "devices": devices,
        "hints": hints,
    }


def _read_gpsd_once() -> Optional[dict]:
    """Read one TPV report from GPSD. Returns dict with lat, lon, time or None."""
    try:
        from gpsdclient import GPSDClient
    except ImportError:
        return None
    result: list[Optional[dict]] = [None]

    def _reader():
        try:
            with GPSDClient(host=_GPS_HOST, port=_GPS_PORT) as client:
                for report in client.dict_stream(convert_datetime=True, filter=["TPV"]):
                    mode = report.get("mode", 0)
                    if mode >= 2:
                        lat, lon = report.get("lat"), report.get("lon")
                        if lat is not None and lon is not None:
                            result[0] = report
                            return
        except Exception as e:
            _log.debug("GPSD read failed: %s", e)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=_GPS_READ_TIMEOUT_SEC)
    return result[0]


def _read_gps_from_source(config: Optional[Any] = None) -> Optional[dict]:
    """
    Read GPS data from configured source (GPSD, serial, or auto).
    Returns dict with lat, lon, time or None.
    """
    if config is None:
        try:
            config = get_config()
        except Exception:
            config = {}
    source = (config.get("gps_source") or "auto").lower()
    serial_port = (config.get("gps_serial_port") or "").strip()

    def try_gpsd():
        return _read_gpsd_once()

    def try_serial(port: str):
        return _read_serial_nmea(port)

    # GPSD
    if source == "gpsd":
        return try_gpsd()

    # Serial (explicit port or from detected)
    if source == "serial":
        if serial_port:
            return try_serial(serial_port)
        status = get_gps_status(config)
        for p in status.get("serial_ports_with_gps", [])[:1]:
            return try_serial(p["path"])
        return None

    # Auto: try GPSD first, then serial
    report = try_gpsd()
    if report is not None:
        return report
    if serial_port:
        return try_serial(serial_port)
    status = get_gps_status(config)
    for p in status.get("serial_ports_with_gps", [])[:1]:
        return try_serial(p["path"])
    return None


def get_gps_location(config: Optional[Any] = None) -> Optional[tuple[float, float]]:
    """
    Get current location from GPS (GPSD or direct serial). Returns (lat, lon) or None.
    Uses gps_source config: gpsd, serial, or auto.
    """
    report = _read_gps_from_source(config)
    if report is None:
        return None
    lat = report.get("lat")
    lon = report.get("lon")
    if lat is not None and lon is not None:
        return (float(lat), float(lon))
    return None


def get_gps_time(config: Optional[Any] = None) -> Optional[datetime]:
    """
    Get current time from GPS (UTC). Returns datetime or None.
    Uses gps_source config: gpsd, serial, or auto.
    """
    report = _read_gps_from_source(config)
    if report is None:
        return None
    t = report.get("time")
    if t is None:
        return None
    if isinstance(t, datetime):
        if t.tzinfo is None:
            return t.replace(tzinfo=timezone.utc)
        return t
    return None


def get_gps_stats(config: Optional[Any] = None) -> Optional[dict[str, Any]]:
    """
    Get GPS stats for display (lat, lon, time, altitude, speed, track, satellites).
    Returns None if no GPS fix. Dict is JSON-serializable.
    """
    report = _read_gps_from_source(config)
    if report is None:
        return None
    lat = report.get("lat")
    lon = report.get("lon")
    if lat is None or lon is None:
        return None
    out: dict[str, Any] = {
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
    }
    t = report.get("time")
    if t is not None and isinstance(t, datetime):
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        out["time_utc"] = t.strftime("%H:%M:%S")
        out["date_utc"] = t.strftime("%Y-%m-%d")
    alt = report.get("alt")
    if alt is not None:
        out["altitude_m"] = round(float(alt), 1)
    speed = report.get("speed")
    if speed is not None:
        out["speed_ms"] = round(float(speed), 2)
        out["speed_kmh"] = round(float(speed) * 3.6, 1)
    track = report.get("track")
    if track is not None:
        out["track_deg"] = round(float(track), 1)
    sats = report.get("satellites")
    if sats is not None:
        out["satellites"] = int(sats)
    return out
