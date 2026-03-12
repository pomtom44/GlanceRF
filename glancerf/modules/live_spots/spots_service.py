"""
Fetch live spot data from various sources (RBN, PSK Reporter, DX cluster).
Probe functions return raw and parsed data to inspect what each service provides.
"""

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from glancerf.config import get_logger

_log = get_logger("live_spots.spots_service")

_TIMEOUT = 15.0
_RAW_PREVIEW_BYTES = 2048

_RBN_URLS = [
    "https://www.reversebeacon.net/raw_data/rbn_raw_data.php",
    "https://beta.reversebeacon.net/raw_data/rbn_raw_data.php",
]

_PSKREPORTER_BASE = "https://retrieve.pskreporter.info/query"
_DXWATCH_SPOTS = "https://dxwatch.com/dxsd1/dxsd1.php?f=0&t=dx"


def _fetch_and_log(source_id: str, url: str, method: str = "GET") -> dict[str, Any]:
    out: dict[str, Any] = {"source": source_id, "url": url, "ok": False, "status": None, "content_type": "", "length": 0, "preview": ""}
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            if method.upper() == "GET":
                r = client.get(url)
            else:
                r = client.request(method, url)
        out["status"] = r.status_code
        out["ok"] = 200 <= r.status_code < 400
        out["content_type"] = (r.headers.get("content-type") or "").split(";")[0].strip()
        body = r.content
        out["length"] = len(body)
        try:
            text = body.decode("utf-8", errors="replace")
            preview = text[:400].replace("\r", "").replace("\n", " ")
            if len(text) > 400:
                preview += "..."
            out["preview"] = preview
        except Exception:
            out["preview"] = "(binary)"
        _log.debug("live_spots fetch %s: status=%s content_type=%s length=%s", source_id, out["status"], out["content_type"], out["length"])
        return out
    except Exception as e:
        _log.debug("live_spots fetch %s failed: %s", source_id, e)
        out["error"] = str(e)
        return out


def _parse_pskreporter_xml(body: bytes) -> dict[str, Any]:
    result: dict[str, Any] = {"record_count": 0, "records": [], "sample_records": [], "fields_seen": set(), "parse_error": None}
    try:
        text = body.decode("utf-8", errors="replace")
        root = ET.fromstring(text)
    except ET.ParseError as e:
        result["parse_error"] = str(e)
        return result
    except Exception as e:
        result["parse_error"] = str(e)
        return result

    def iter_reports():
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "receptionReport":
                yield elem

    records = []
    for elem in iter_reports():
        attrs = dict(elem.attrib)
        for k in attrs:
            result["fields_seen"].add(k)
        records.append(attrs)

    result["record_count"] = len(records)
    result["records"] = records
    result["sample_records"] = records[:10]
    result["fields_seen"] = sorted(result["fields_seen"])
    return result


def probe_pskreporter(
    flow_start_seconds: int = -3600,
    rpt_limit: int = 50,
    sender_callsign: str | None = None,
    receiver_callsign: str | None = None,
    rronly: int = 1,
) -> dict[str, Any]:
    params: dict[str, str | int] = {
        "flowStartSeconds": flow_start_seconds,
        "rptlimit": rpt_limit,
        "rronly": rronly,
    }
    if sender_callsign:
        params["senderCallsign"] = sender_callsign.strip()
    if receiver_callsign:
        params["receiverCallsign"] = receiver_callsign.strip()
    url = _PSKREPORTER_BASE
    out: dict[str, Any] = {
        "source": "PSK Reporter",
        "url": url,
        "params": dict(params),
        "ok": False,
        "status": None,
        "content_type": "",
        "length": 0,
        "raw_preview": "",
        "parsed": None,
        "error": None,
    }
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            r = client.get(url, params=params)
        out["status"] = r.status_code
        out["ok"] = 200 <= r.status_code < 400
        out["content_type"] = (r.headers.get("content-type") or "").split(";")[0].strip()
        body = r.content
        out["length"] = len(body)
        try:
            out["raw_preview"] = body.decode("utf-8", errors="replace")[:_RAW_PREVIEW_BYTES]
            if len(body) > _RAW_PREVIEW_BYTES:
                out["raw_preview"] += "\n... (truncated)"
        except Exception:
            out["raw_preview"] = "(binary)"
        if out["ok"] and body:
            parsed = _parse_pskreporter_xml(body)
            out["parsed"] = parsed
        return out
    except Exception as e:
        out["error"] = str(e)
        _log.debug("live_spots probe_pskreporter failed: %s", e)
        return out


def probe_rbn() -> dict[str, Any]:
    out: dict[str, Any] = {"source": "RBN", "urls_tried": _RBN_URLS, "results": [], "best": None}
    for url in _RBN_URLS:
        one: dict[str, Any] = {"url": url, "ok": False, "status": None, "content_type": "", "length": 0, "raw_preview": "", "first_lines": [], "error": None}
        try:
            with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
                r = client.get(url)
            one["status"] = r.status_code
            one["ok"] = 200 <= r.status_code < 400
            one["content_type"] = (r.headers.get("content-type") or "").split(";")[0].strip()
            body = r.content
            one["length"] = len(body)
            try:
                text = body.decode("utf-8", errors="replace")
                one["raw_preview"] = text[:_RAW_PREVIEW_BYTES]
                if len(text) > _RAW_PREVIEW_BYTES:
                    one["raw_preview"] += "\n... (truncated)"
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:15]
                one["first_lines"] = lines
            except Exception:
                one["raw_preview"] = "(binary)"
            out["results"].append(one)
            if one["ok"] and out["best"] is None:
                out["best"] = one
        except Exception as e:
            one["error"] = str(e)
            out["results"].append(one)
    return out


def probe_dxwatch() -> dict[str, Any]:
    out: dict[str, Any] = {"source": "DXWatch", "url": _DXWATCH_SPOTS, "ok": False, "status": None, "content_type": "", "length": 0, "raw_preview": "", "error": None}
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            r = client.get(_DXWATCH_SPOTS)
        out["status"] = r.status_code
        out["ok"] = 200 <= r.status_code < 400
        out["content_type"] = (r.headers.get("content-type") or "").split(";")[0].strip()
        body = r.content
        out["length"] = len(body)
        try:
            text = body.decode("utf-8", errors="replace")
            out["raw_preview"] = text[:_RAW_PREVIEW_BYTES]
            if len(body) > _RAW_PREVIEW_BYTES:
                out["raw_preview"] += "\n... (truncated)"
        except Exception:
            out["raw_preview"] = "(binary)"
        return out
    except Exception as e:
        out["error"] = str(e)
        _log.debug("live_spots probe_dxwatch failed: %s", e)
        return out


def probe_all_sources(
    psk_flow_seconds: int = -3600,
    psk_limit: int = 50,
    psk_sender: str | None = None,
    psk_receiver: str | None = None,
) -> dict[str, Any]:
    return {
        "pskreporter": probe_pskreporter(
            flow_start_seconds=psk_flow_seconds,
            rpt_limit=psk_limit,
            sender_callsign=psk_sender,
            receiver_callsign=psk_receiver,
        ),
        "rbn": probe_rbn(),
        "dxwatch": probe_dxwatch(),
    }


def fetch_rbn() -> list[dict[str, Any]]:
    results = []
    for url in _RBN_URLS:
        r = _fetch_and_log("RBN", url)
        results.append(r)
        if r.get("ok"):
            break
    return results


def fetch_pskreporter() -> dict[str, Any]:
    url = f"{_PSKREPORTER_BASE}?flowStartSeconds=-600&rronly=1&rptlimit=20"
    return _fetch_and_log("PSK Reporter", url)


def fetch_dxwatch() -> dict[str, Any]:
    return _fetch_and_log("DXWatch", _DXWATCH_SPOTS)


def fetch_all_sources() -> dict[str, Any]:
    _log.debug("live_spots: fetching all sources")
    out: dict[str, Any] = {
        "rbn": fetch_rbn(),
        "pskreporter": fetch_pskreporter(),
        "dxwatch": fetch_dxwatch(),
    }
    return out


_PSK_CACHE_TTL_SEC = 300


def fetch_pskreporter_for_config(
    filter_mode: str,
    callsign_or_grid: str,
    flow_seconds: int = -3600,
    rpt_limit: int = 200,
) -> list[dict[str, Any]]:
    value = (callsign_or_grid or "").strip()
    if not value:
        return []
    mode = (filter_mode or "received").strip().lower()
    sender: str | None = value if mode == "sent" else None
    receiver: str | None = value if mode == "received" else None
    result = probe_pskreporter(
        flow_start_seconds=flow_seconds,
        rpt_limit=rpt_limit,
        sender_callsign=sender,
        receiver_callsign=receiver,
        rronly=1,
    )
    if not result.get("ok") or not result.get("parsed"):
        return []
    parsed = result["parsed"]
    return parsed.get("records") or []


def get_pskreporter_cached(
    filter_mode: str,
    callsign_or_grid: str,
    flow_seconds: int = -3600,
    rpt_limit: int = 200,
) -> list[dict[str, Any]]:
    value = (callsign_or_grid or "").strip()
    if not value:
        return []
    mode = (filter_mode or "received").strip().lower()
    key_value = value.upper()
    cache_key = f"live_spots:psk:{mode}:{key_value}:{flow_seconds}"

    from glancerf.utils.cache import get_cache

    def fetch() -> list[dict[str, Any]]:
        return fetch_pskreporter_for_config(
            filter_mode=mode,
            callsign_or_grid=value,
            flow_seconds=flow_seconds,
            rpt_limit=rpt_limit,
        )

    return get_cache().get_or_set(cache_key, _PSK_CACHE_TTL_SEC, fetch)
