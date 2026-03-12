"""
In-memory rate limiter for sensitive POST endpoints.
Limits by client IP: 10 requests per minute per IP.
"""

import time
from collections import defaultdict
from typing import List

from fastapi import Request
from fastapi.responses import JSONResponse

from glancerf.config import get_logger

_log = get_logger("rate_limit")

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60

_store: defaultdict = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune(timestamps: List[float], window: int) -> None:
    """Remove timestamps outside the window."""
    cutoff = time.monotonic() - window
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)


def _check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.monotonic()
    timestamps = _store[ip]
    _prune(timestamps, RATE_LIMIT_WINDOW)
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return False
    timestamps.append(now)
    return True


async def rate_limit_dependency(request: Request) -> None:
    """FastAPI dependency: raises RateLimitExceeded if client is over limit."""
    ip = _get_client_ip(request)
    if not _check_rate_limit(ip):
        _log.debug("Rate limit exceeded for IP %s", ip)
        raise RateLimitExceeded()


class RateLimitExceeded(Exception):
    """Raised when client exceeds rate limit."""

    pass


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """FastAPI exception handler for RateLimitExceeded."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
        headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
    )
