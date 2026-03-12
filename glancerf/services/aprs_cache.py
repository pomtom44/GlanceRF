"""
APRS-IS cache. Connects to APRS-IS full feed (rotate.aprs.net:10152), captures all packets,
stores in SQLite under config_dir/cache/aprs.db. Uses aprs_cache_max_size_mb and
aprs_cache_max_age_hours to purge old records. Uses setup_callsign and setup_ssid for login.
Broadcasts aprs_update via WebSocket when new packets arrive (debounced).
Started on app startup, stopped on shutdown.
"""

import asyncio
import socket
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional, Tuple

from glancerf.config import get_config, get_logger
from glancerf.utils.cache import get_cache

_log = get_logger("aprs_cache")

_APRS_BROADCAST_DEBOUNCE_SEC = 0.5
_broadcast_cm: Any = None
_broadcast_loop: Optional[asyncio.AbstractEventLoop] = None
_last_broadcast_at: float = 0


def set_aprs_broadcast(connection_manager: Any, loop: asyncio.AbstractEventLoop) -> None:
    """Set connection manager and event loop for APRS update broadcast. Call from main at startup."""
    global _broadcast_cm, _broadcast_loop
    _broadcast_cm = connection_manager
    _broadcast_loop = loop


def _maybe_broadcast_aprs_update() -> None:
    """Broadcast aprs_update so clients refetch. Debounced to at most once per _APRS_BROADCAST_DEBOUNCE_SEC."""
    global _last_broadcast_at
    if _broadcast_cm is None or _broadcast_loop is None:
        return
    now = time.time()
    if now - _last_broadcast_at < _APRS_BROADCAST_DEBOUNCE_SEC:
        return
    _last_broadcast_at = now
    # Invalidate API cache so next refetch gets fresh DB data (not 5‑min‑old cached response)
    try:
        n = get_cache().invalidate_prefix("map:aprs:")
        if n:
            _log.debug("APRS cache: invalidated %d API cache entries", n)
    except Exception as e:
        _log.debug("APRS cache invalidation failed: %s", e)
    try:
        asyncio.run_coroutine_threadsafe(
            _broadcast_cm.broadcast_aprs_update(),
            _broadcast_loop,
        )
    except Exception as e:
        _log.debug("APRS broadcast failed: %s", e)

_APRS_SERVER = "rotate.aprs.net"
_APRS_PORT = 10152
_RECV_SIZE = 65536  # Larger buffer for full feed throughput
_RECONNECT_DELAY = 30
_DB_FILENAME = "aprs.db"
_CACHE_DIR = "cache"
_DEFAULT_MAX_SIZE_MB = 500
_DEFAULT_MAX_AGE_HOURS = 168  # 7 days
_PURGE_CHECK_EVERY = 1000  # check purge every N inserts
_COMMIT_EVERY = 50  # commit frequently so displayed data is fresh


def _aprs_passcode_from_callsign(callsign: str) -> int:
    """Compute APRS-IS passcode from callsign (without SSID). Standard algorithm."""
    call = (callsign or "").upper().split("-")[0].strip()
    if not call:
        return -1
    call = call.ljust(9)[:9]
    hash_val = 0x73E2  # 29666
    for i in range(0, 9, 2):
        hash_val ^= ord(call[i + 1]) if i + 1 < len(call) else 0
        hash_val ^= (ord(call[i]) if i < len(call) else 0) << 8
    return hash_val & 0x7FFF


def _get_cache_db_path() -> Optional[Path]:
    config = get_config()
    callsign = (config.get("setup_callsign") or "").strip()
    if not callsign:
        return None
    cache_dir = config.config_dir / _CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / _DB_FILENAME


def _get_login() -> Optional[Tuple[str, int]]:
    config = get_config()
    callsign = (config.get("setup_callsign") or "").strip()
    if not callsign:
        return None
    ssid = (config.get("setup_ssid") or "01").strip()
    if not ssid:
        ssid = "01"
    call_ssid = f"{callsign}-{ssid}"
    passcode = config.get("aprs_passcode")
    if passcode is None or passcode == "":
        passcode = _aprs_passcode_from_callsign(callsign)
    else:
        try:
            passcode = int(passcode)
        except (TypeError, ValueError):
            passcode = _aprs_passcode_from_callsign(callsign)
    return (call_ssid, passcode)


def _get_limits() -> Tuple[int, float]:
    """Return (max_size_bytes, max_age_hours)."""
    config = get_config()
    max_size_mb = config.get("aprs_cache_max_size_mb")
    if max_size_mb is None or max_size_mb == "":
        old_size = config.get("aprs_cache_max_size")
        if old_size is not None and old_size != "":
            try:
                records = int(old_size)
                max_size_mb = max(100, min(10000, records * 150 // (1024 * 1024)))
            except (TypeError, ValueError):
                max_size_mb = _DEFAULT_MAX_SIZE_MB
        else:
            max_size_mb = _DEFAULT_MAX_SIZE_MB
    try:
        mb = float(max_size_mb) if isinstance(max_size_mb, (int, float)) else float(max_size_mb)
        mb = max(100.0, min(10000.0, mb))
    except (TypeError, ValueError):
        mb = _DEFAULT_MAX_SIZE_MB
    max_age = config.get("aprs_cache_max_age_hours")
    try:
        age = float(max_age) if max_age is not None and max_age != "" else _DEFAULT_MAX_AGE_HOURS
        age = max(1.0, min(8760, age))
    except (TypeError, ValueError):
        age = _DEFAULT_MAX_AGE_HOURS
    return (int(mb * 1024 * 1024), age)


def _create_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS packets (id INTEGER PRIMARY KEY AUTOINCREMENT, received_at REAL NOT NULL, raw TEXT NOT NULL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_received_at ON packets(received_at)")
    conn.commit()


def _purge_if_needed(conn: sqlite3.Connection, db_path: Optional[Path]) -> None:
    """Purge oldest records when file size or age limit is exceeded."""
    max_size_bytes, max_age_hours = _get_limits()
    cutoff_age = time.time() - (max_age_hours * 3600)
    try:
        deleted_age = conn.execute(
            "DELETE FROM packets WHERE received_at < ?", (cutoff_age,)
        ).rowcount
        if deleted_age:
            conn.commit()
            _log.debug("APRS cache: purged %d records older than %.1f h", deleted_age, max_age_hours)
        if db_path is None or not db_path.is_file():
            return
        file_size = db_path.stat().st_size
        if file_size <= max_size_bytes:
            return
        count = conn.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
        if count == 0:
            return
        avg_bytes_per_row = file_size / count
        to_remove = max(1, int(count - max_size_bytes / avg_bytes_per_row))
        cursor = conn.execute(
            "SELECT id FROM packets ORDER BY received_at ASC LIMIT ?", (to_remove,)
        )
        ids = [row[0] for row in cursor.fetchall()]
        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(f"DELETE FROM packets WHERE id IN ({placeholders})", ids)
            conn.commit()
            conn.execute("VACUUM")
            conn.commit()
            _log.debug("APRS cache: purged %d oldest records (size limit %.1f MB)", len(ids), max_size_bytes / (1024 * 1024))
    except sqlite3.Error as e:
        _log.debug("APRS cache purge error: %s", e)


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
            conn = sqlite3.connect(str(db_path), timeout=30.0)
            _create_db(conn)
            _purge_if_needed(conn, db_path)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60.0)
            sock.connect((_APRS_SERVER, _APRS_PORT))
            sock.settimeout(300.0)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            buf = b""
            login_sent = False
            # Wait for server identification (# line) before login per APRS-IS spec
            while not login_sent:
                data = sock.recv(_RECV_SIZE)
                if not data:
                    raise OSError("Connection closed before server ID")
                buf += data
                while b"\n" in buf or b"\r" in buf:
                    line, _, buf = buf.partition(b"\n")
                    line = line.replace(b"\r", b"").decode("ascii", errors="replace").strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        sock.sendall(login.encode("ascii", errors="replace"))
                        login_sent = True
                        _log.debug(
                            "APRS cache connected: %s full feed -> %s",
                            call_ssid, db_path,
                        )
                        break
            if not login_sent:
                raise OSError("No server ID received")

            session_start = time.time()
            last_stats_at = session_start
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
                        for attempt in range(3):
                            try:
                                conn.execute("INSERT INTO packets (received_at, raw) VALUES (?, ?)", (now, line))
                                break
                            except sqlite3.OperationalError as oe:
                                if "locked" in str(oe).lower() and attempt < 2:
                                    time.sleep(0.05 * (attempt + 1))
                                    continue
                                raise
                        insert_count += 1
                        if get_config().get("aprs_debug"):
                            _log.info("APRS << %s", line[:120] + ("..." if len(line) > 120 else ""))
                        _maybe_broadcast_aprs_update()
                        if insert_count % _COMMIT_EVERY == 0:
                            conn.commit()
                        if insert_count % _PURGE_CHECK_EVERY == 0:
                            conn.commit()
                            _purge_if_needed(conn, db_path)
                        # Log stats every 60s for verification (packets/sec)
                        if now - last_stats_at >= 60:
                            elapsed = now - session_start
                            rate = insert_count / elapsed if elapsed > 0 else 0
                            _log.debug("APRS cache: %d packets received, %.1f/sec", insert_count, rate)
                            last_stats_at = now
                    except sqlite3.Error as e:
                        _log.warning("APRS cache: SQLite error dropping packet: %s", e)
                if insert_count and insert_count % _COMMIT_EVERY == 0:
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


_thread: Optional[threading.Thread] = None


def start_aprs_cache() -> None:
    """Start the APRS full-feed cache in a background thread (if callsign is set)."""
    global _thread
    login = _get_login()
    db_path = _get_cache_db_path()
    if login is None:
        _log.debug("APRS cache: not started (no setup_callsign in config). Cache would be at config_dir/cache/aprs.db")
        return
    if db_path is None:
        _log.debug("APRS cache: not started (no cache path)")
        return
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run_aprs_cache_thread, daemon=True)
    _thread.start()
    _log.debug("APRS cache started: %s (file created on first packet)", db_path)


def stop_aprs_cache() -> None:
    """No-op; thread is daemon and exits with process."""
    pass
