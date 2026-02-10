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
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _prune(timestamps: List[float], window: int) -> None:
    cutoff = time.monotonic() - window
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)


def _check_rate_limit(ip: str) -> bool:
    now = time.monotonic()
    timestamps = _store[ip]
    _prune(timestamps, RATE_LIMIT_WINDOW)
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return False
    timestamps.append(now)
    return True


async def rate_limit_dependency(request: Request) -> None:
    ip = _get_client_ip(request)
    if not _check_rate_limit(ip):
        _log.debug("Rate limit exceeded for IP %s", ip)
        raise RateLimitExceeded()
    _log.debug("Rate limit OK for IP %s", ip)


class RateLimitExceeded(Exception):
    """Raised when client exceeds rate limit."""
    pass


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
        headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
    )
