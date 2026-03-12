"""
Global in-memory TTL cache for GlanceRF.
All modules share this cache for API responses and computed data.

Usage:
    from glancerf.utils.cache import get_cache, cache_key

    cache = get_cache()

    # Build keys with module prefix (avoids collisions)
    key = cache_key("contests", "list", "wa7bnm")
    data = cache.get(key)
    if data is None:
        data = fetch_contests()
        cache.set(key, data, ttl_seconds=900)

    # Or: compute once, serve from cache (single-flight: only one thread computes)
    data = cache.get_or_set(key, ttl_seconds=45, factory=lambda: compute())

Key convention: use cache_key(module_id, *parts) for "module:part1:part2".
"""

import threading
import time
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")

_DEFAULT_MAX_ENTRIES = 500


def cache_key(module_id: str, *parts: Union[str, int, float]) -> str:
    """
    Build a cache key with module prefix. Avoids collisions between modules.
    Example: cache_key("rss", "feed", url_hash) -> "rss:feed:abc123"
    """
    if not module_id or not isinstance(module_id, str):
        raise ValueError("module_id must be a non-empty string")
    safe = []
    for p in parts:
        if p is None:
            continue
        s = str(p).strip()
        if ":" in s:
            s = s.replace(":", "_")
        if s:
            safe.append(s)
    return module_id + ":" + ":".join(safe) if safe else module_id


class TTLCache:
    """Thread-safe in-memory cache with TTL, LRU eviction, and single-flight get_or_set."""

    __slots__ = ("_store", "_expiry", "_lock", "_max_entries", "_populate_locks", "_populate_locks_lock")

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES):
        self._store: dict = {}
        self._expiry: dict = {}
        self._lock = threading.Lock()
        self._max_entries = max(1, max_entries)
        self._populate_locks: dict = {}
        self._populate_locks_lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired, else None."""
        with self._lock:
            if key not in self._store:
                return None
            if time.time() > self._expiry[key]:
                del self._store[key]
                del self._expiry[key]
                return None
            return self._store[key]

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Store value under key for ttl_seconds."""
        with self._lock:
            self._maybe_evict()
            self._store[key] = value
            self._expiry[key] = time.time() + ttl_seconds

    def get_or_set(self, key: str, ttl_seconds: float, factory: Callable[[], T]) -> T:
        """
        Return cached value or compute via factory, store, and return.
        Single-flight: only one thread computes per key; others wait and then read.
        """
        value = self.get(key)
        if value is not None:
            return value
        with self._populate_locks_lock:
            key_lock = self._populate_locks.setdefault(key, threading.Lock())
        with key_lock:
            value = self.get(key)
            if value is not None:
                return value
            computed = factory()
            self.set(key, computed, ttl_seconds)
            return computed

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all entries whose key starts with prefix. Returns count removed."""
        if not prefix:
            return 0
        with self._lock:
            to_del = [k for k in self._store if k.startswith(prefix)]
            for k in to_del:
                del self._store[k]
                del self._expiry[k]
            return len(to_del)

    def _maybe_evict(self) -> None:
        """Evict expired entries, then oldest if still over limit."""
        now = time.time()
        expired = [k for k, t in self._expiry.items() if now > t]
        for k in expired:
            del self._store[k]
            del self._expiry[k]
        if len(self._store) >= self._max_entries:
            oldest = min(self._expiry, key=self._expiry.get)
            del self._store[oldest]
            del self._expiry[oldest]

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()
            self._expiry.clear()


_global_cache: Optional[TTLCache] = None
_global_lock = threading.Lock()


def get_cache(max_entries: Optional[int] = None) -> TTLCache:
    """Return the shared global cache instance. All modules use this same cache."""
    global _global_cache
    with _global_lock:
        if _global_cache is None:
            _global_cache = TTLCache(max_entries=max_entries or _DEFAULT_MAX_ENTRIES)
        return _global_cache
