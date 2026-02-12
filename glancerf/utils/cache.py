"""
Universal in-memory TTL cache for GlanceRF. All modules can use this to cache
API responses or computed data so multiple screens/tabs get the same result
from the server instead of each calling external APIs or heavy computation.

Usage:
    from glancerf.utils.cache import get_cache

    cache = get_cache()

    # Simple get/set
    data = cache.get("contests:list:wa7bnm")
    if data is None:
        data = fetch_contests()
        cache.set("contests:list:wa7bnm", data, ttl_seconds=900)

    # Or use get_or_set (compute once, then serve from cache)
    data = cache.get_or_set(
        "satellite:passes:25544,49044|51.5|-0.1|0",
        ttl_seconds=45,
        factory=lambda: compute_passes([25544, 49044], 51.5, -0.1, 0),
    )

Key convention: use a prefix per module to avoid collisions, e.g. "contests:...",
"dxpeditions:...", "satellite:passes:...", "satellite:tracks:...".
"""

import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_DEFAULT_MAX_ENTRIES = 500


class TTLCache:
    """
    Thread-safe in-memory cache with TTL.
    Keys are strings; values are any object (stored by reference).
    """

    __slots__ = ("_store", "_expiry", "_lock", "_max_entries")

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES):
        self._store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._lock = threading.Lock()
        self._max_entries = max(1, max_entries)

    def get(self, key: str) -> Any | None:
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
        """Store value under key for ttl_seconds. Overwrites existing."""
        with self._lock:
            self._maybe_evict()
            self._store[key] = value
            self._expiry[key] = time.time() + ttl_seconds

    def get_or_set(self, key: str, ttl_seconds: float, factory: Callable[[], T]) -> T:
        """
        Return cached value if present and not expired. Otherwise call factory(),
        store the result, and return it. Thread-safe. On miss, factory() may be
        called more than once if several requests hit at once; last write wins.
        """
        value = self.get(key)
        if value is not None:
            return value
        computed = factory()
        self.set(key, computed, ttl_seconds)
        return computed

    def _maybe_evict(self) -> None:
        if len(self._store) < self._max_entries:
            return
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
        """Remove all entries. Mainly for tests."""
        with self._lock:
            self._store.clear()
            self._expiry.clear()


_global_cache: TTLCache | None = None
_global_lock = threading.Lock()


def get_cache(max_entries: int | None = None) -> TTLCache:
    """Return the shared cache instance. All modules use this same cache."""
    global _global_cache
    with _global_lock:
        if _global_cache is None:
            _global_cache = TTLCache(max_entries=max_entries or _DEFAULT_MAX_ENTRIES)
        return _global_cache
