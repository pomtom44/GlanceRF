"""
Register RSS API routes. Called by core at startup if this module is present.
"""

import hashlib
import time
from urllib.parse import urlparse

import feedparser
import httpx
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from glancerf.config import get_logger
from glancerf.utils.cache import get_cache

_log = get_logger("rss.api_routes")

_RSS_MAX_ITEMS = 50
_RSS_TIMEOUT_SEC = 15
_RSS_CACHE_TTL = 600


async def fetch_rss_feed(url: str) -> dict | None:
    """Fetch and parse an RSS feed; return dict with title, link, items or None on error. Used by API and cache warmer."""
    url = (url or "").strip()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    try:
        async with httpx.AsyncClient(timeout=_RSS_TIMEOUT_SEC) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            body = resp.text
    except httpx.HTTPError as e:
        _log.debug("RSS fetch failed: %s", e)
        return None
    try:
        feed = feedparser.parse(body)
    except Exception as e:
        _log.debug("RSS parse failed: %s", e)
        return None
    title = (feed.feed.get("title") or "").strip() or None
    link = (feed.feed.get("link") or "").strip() or None
    items = []
    for entry in feed.entries[: _RSS_MAX_ITEMS]:
        entry_title = (entry.get("title") or "").strip() or ""
        entry_link = (entry.get("link") or "").strip() or ""
        entry_published = entry.get("published") or entry.get("updated") or ""
        if not isinstance(entry_published, str):
            parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
            if parsed_time:
                entry_published = time.strftime(
                    "%Y-%m-%dT%H:%M:%S", parsed_time
                )
            else:
                entry_published = ""
        summary = entry.get("summary") or entry.get("description") or ""
        if hasattr(summary, "strip"):
            summary = summary.strip()
        else:
            summary = str(summary)[:500]
        items.append({
            "title": entry_title,
            "link": entry_link,
            "published": entry_published,
            "description": summary[:500] if summary else "",
        })
    return {"title": title, "link": link, "items": items}


def register_routes(app: FastAPI) -> None:
    """Register GET /api/rss."""

    @app.get("/api/rss")
    async def get_rss(url: str = Query(..., description="RSS feed URL")):
        """Fetch and parse an RSS feed, return JSON. Proxies the request to avoid CORS."""
        _log.debug("API: GET /api/rss url=%s", url[:80] if url else "")
        url = (url or "").strip()
        if not url:
            return JSONResponse(
                {"error": "Missing or empty url"}, status_code=400
            )
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return JSONResponse(
                {"error": "URL must be http or https"}, status_code=400
            )
        cache_key = "rss:" + hashlib.sha256(url.encode()).hexdigest()
        cache = get_cache()
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        out = await fetch_rss_feed(url)
        if out is None:
            return JSONResponse(
                {"error": "Failed to fetch feed", "detail": "Fetch or parse failed"},
                status_code=502,
            )
        cache.set(cache_key, out, _RSS_CACHE_TTL)
        return out
