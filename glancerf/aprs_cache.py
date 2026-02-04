"""
APRS-IS full-feed cache. Connects to APRS-IS (no filter), stores every packet
in SQLite under config_dir/cache/aprs.db. Uses setup_callsign and setup_ssid
(callsign-SSID for login). Started on app startup, stopped on shutdown.
"""

import socket
import sqlite3
import threading
import time
from pathlib import Path

from glancerf.logging_config import get_logger

_log = get_logger("aprs_cache")

_APRS_SERVER = "rotate.aprs.net"
_APRS_FULL_FEED_PORT = 10152
_RECV_SIZE = 4096
_RECONNECT_DELAY = 30
_DB_FILENAME = "aprs.db"
_CACHE_DIR = "cache"


def _get_cache_db_path() -> Path | None:
    from glancerf.config import get_config
    config = get_config()
    callsign = (config.get("setup_callsign") or "").strip()
    if not callsign:
        return None
    cache_dir = config.config_dir / _CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / _DB_FILENAME


def _get_login() -> tuple[str, int] | None:
    from glancerf.config import get_config
    config = get_config()
    callsign = (config.get("setup_callsign") or "").strip()
    if not callsign:
        return None
    ssid = (config.get("setup_ssid") or "01").strip()
    if not ssid:
        ssid = "01"
    call_ssid = f"{callsign}-{ssid}"
    passcode = config.get("aprs_passcode")
    if passcode is None:
        passcode = -1
    try:
        passcode = int(passcode)
    except (TypeError, ValueError):
        passcode = -1
    return (call_ssid, passcode)


def _create_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS packets (id INTEGER PRIMARY KEY AUTOINCREMENT, received_at REAL NOT NULL, raw TEXT NOT NULL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON packets(received_at)")
    conn.commit()


def _run_aprs_cache_thread() -> None:
    login_info = _get_login()
    db_path = _get_cache_db_path()
    if not login_info or not db_path:
        _log.debug("APRS cache: no callsign or cache path, skipping")
        return
    call_ssid, passcode = login_info
    login = f"user {call_ssid} pass {passcode} vers GlanceRF 1.0\n"
    insert_count = 0
    sock = None
    conn = None
    while True:
        try:
            conn = sqlite3.connect(str(db_path))
            _create_db(conn)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60.0)
            sock.connect((_APRS_SERVER, _APRS_FULL_FEED_PORT))
            sock.settimeout(300.0)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            buf = b""
            sock.sendall(login.encode("ascii", errors="replace"))
            _log.debug("APRS cache connected as %s, writing to %s", call_ssid, db_path)

            while True:
                data = sock.recv(_RECV_SIZE)
                if not data:
                    break
                buf += data
                while b"\n" in buf or b"\r" in buf:
                    line, _, buf = buf.partition(b"\n")
                    line = line.replace(b"\r", b"").decode("ascii", errors="replace").strip()
                    if not line or line.startswith("#"):
                        continue
                    now = time.time()
                    try:
                        conn.execute("INSERT INTO packets (received_at, raw) VALUES (?, ?)", (now, line))
                        insert_count += 1
                    except sqlite3.Error:
                        pass
                if insert_count and insert_count % 500 == 0:
                    conn.commit()
        except (socket.error, OSError) as e:
            _log.debug("APRS cache connection error: %s", e)
        except Exception as e:
            _log.debug("APRS cache error: %s", e)
        finally:
            try:
                if conn is not None:
                    conn.commit()
                    conn.close()
            except Exception:
                pass
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass
            sock = None
        time.sleep(_RECONNECT_DELAY)


_thread: threading.Thread | None = None


def start_aprs_cache() -> None:
    """Start the APRS full-feed cache in a background thread (if callsign is set)."""
    global _thread
    if _get_login() is None:
        return
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run_aprs_cache_thread, daemon=True)
    _thread.start()
    _log.debug("APRS cache thread started")


def stop_aprs_cache() -> None:
    """No-op; thread is daemon and exits with process."""
    pass
