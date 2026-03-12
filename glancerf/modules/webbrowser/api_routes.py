"""
Web browser module API: proxy (fetch and serve without frame-blocking headers).
"""

import re
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Query
from fastapi.responses import Response

from glancerf.config import get_logger

_log = get_logger("webbrowser.api_routes")

_ALLOWED_SCHEMES = ("http", "https")
_PROXY_TIMEOUT = 15.0
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"
)


def _is_allowed_url(url: str | None) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme.lower() in _ALLOWED_SCHEMES and bool(parsed.netloc)
    except Exception:
        return False


def _strip_frame_blocking(html: str) -> str:
    """Remove or relax meta tags that prevent embedding in an iframe."""
    html = re.sub(
        r'<meta\s+http-equiv=["\']?X-Frame-Options["\']?\s+content="[^"]*"\s*/?\s*>',
        "",
        html,
        flags=re.IGNORECASE,
    )
    def _replace_csp(match: re.Match) -> str:
        content = match.group(1)
        if "frame-ancestors" in content.lower():
            return ""
        return match.group(0)
    html = re.sub(
        r'<meta\s+http-equiv=["\']?Content-Security-Policy["\']?\s+content="([^"]*)"\s*/?\s*>',
        _replace_csp,
        html,
        flags=re.IGNORECASE,
    )
    return html


def _inject_base_tag(html: bytes, base_url: str, encoding: str = "utf-8") -> bytes:
    """Inject <base href="..."> and strip frame-blocking so the page can be embedded in an iframe."""
    try:
        text = html.decode(encoding, errors="replace")
    except Exception:
        return html
    text = _strip_frame_blocking(text)
    inject = f'<base href="{base_url}" target="_blank">'
    if "<head>" in text:
        text = text.replace("<head>", "<head>" + inject, 1)
    elif "<head " in text:
        text = re.sub(r"(<head\s[^>]*>)", r"\1" + inject, text, count=1)
    else:
        text = inject + text
    return text.encode(encoding, errors="replace")


def _error_html(message: str, status: int) -> bytes:
    """Return a minimal HTML page for proxy errors so the iframe shows readable text."""
    body = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
        f"<p style='font-family:sans-serif;padding:1em;'>{message}</p>"
        f"<p style='font-family:sans-serif;padding:0 1em;font-size:0.9em;color:#666;'>Proxy error ({status})</p>"
        f"</body></html>"
    )
    return body.encode("utf-8")


def register_routes(app: FastAPI) -> None:
    """Register GET /api/webbrowser/proxy."""

    @app.get("/api/webbrowser/proxy")
    async def proxy_page(url: str = Query(..., description="Page URL to fetch and serve")):
        """Fetch the given URL and return the body with frame-blocking headers removed so it can be embedded in an iframe."""
        if not _is_allowed_url(url):
            return Response(
                content=_error_html("Invalid or disallowed URL.", 400),
                media_type="text/html; charset=utf-8",
                status_code=400,
            )
        _log.debug("Proxy: fetching %s", url)
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=_PROXY_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
        except httpx.ConnectError as e:
            _log.warning("Proxy connect error for %s: %s", url, e)
            return Response(
                content=_error_html("Could not connect to the URL. Check the address and your network.", 502),
                media_type="text/html; charset=utf-8",
                status_code=502,
            )
        except httpx.TimeoutException as e:
            _log.warning("Proxy timeout for %s: %s", url, e)
            return Response(
                content=_error_html("The request timed out. Try again or use a different URL.", 502),
                media_type="text/html; charset=utf-8",
                status_code=502,
            )
        except httpx.HTTPStatusError as e:
            _log.warning("Proxy HTTP error for %s: %s", url, e)
            return Response(
                content=_error_html(f"The site returned an error (HTTP {e.response.status_code}).", 502),
                media_type="text/html; charset=utf-8",
                status_code=502,
            )
        except httpx.HTTPError as e:
            _log.warning("Proxy fetch failed for %s: %s", url, e)
            return Response(
                content=_error_html("Failed to fetch URL. Try again or use Direct (iframe) mode.", 502),
                media_type="text/html; charset=utf-8",
                status_code=502,
            )
        content_type = (resp.headers.get("content-type") or "text/html").split(";")[0].strip()
        body = resp.content
        if "text/html" in content_type:
            body = _inject_base_tag(body, url)
        return Response(content=body, media_type=content_type)
