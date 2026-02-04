"""
DXpedition list from multiple open sources (NG3K ADXO, NG3K RSS, DXCAL iCal).
Fetches from each source, merges and deduplicates by call + start date. No Clear Sky dependency.
"""

import html
import re
import time
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from glancerf.logging_config import get_logger

_log = get_logger("dxpeditions.dxpedition_service")

_NG3K_PLAIN_URL = "https://www.ng3k.com/Misc/adxoplain.html"
_NG3K_RSS_URL = "http://www.ng3k.com/adxo.xml"
_DXCAL_ICS_URL = "https://www.danplanet.com/dxcal.ics"
_FETCH_TIMEOUT = 20
_CACHE_MAX_AGE_SEC = 21600  # 6 hours
_MONTH_NAMES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

_cached_result: list[dict[str, Any]] | None = None
_cached_time: float = 0


def _strip_html(raw: str) -> str:
    """Remove HTML tags; preserve links as [text](url), bold as **text**, and newlines for blocks."""
    text = raw
    text = re.sub(r'<a\s+href="([^"]*)"[^>]*>([^<]*)</a>', r"[\2](\1)", text, flags=re.I)
    text = re.sub(r"<b>([^<]*)</b>", r"**\1**", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _parse_date_range(s: str) -> tuple[str | None, str | None]:
    """Parse 'Nov 20-Dec 31, 2025' or 'Dec 7, 2025-Jan 5, 2026' into (start_iso, end_iso)."""
    s = s.strip()
    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s*(\d{4}))?\s*-\s*"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s*(\d{4})",
        s,
        re.I,
    )
    if not m:
        return None, None
    smon, sday, syear, emon, eday, eyear = m.groups()
    syear = syear or eyear
    try:
        sm = _MONTH_NAMES.get(smon[:3].capitalize())
        em = _MONTH_NAMES.get(emon[:3].capitalize())
        if sm is None or em is None:
            return None, None
        start_d = datetime(int(syear), sm, int(sday), 0, 0, 0, tzinfo=timezone.utc)
        end_d = datetime(int(eyear), em, int(eday), 23, 59, 59, tzinfo=timezone.utc)
        return start_d.isoformat().replace("+00:00", "Z"), end_d.isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError):
        return None, None


def _parse_blocks(plain: str, source: str) -> list[dict[str, Any]]:
    """Parse NG3K plain text into list of expedition dicts with source tag."""
    lines = [ln.strip() for ln in plain.splitlines() if ln.strip()]
    result: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Contest" in line and "Check here" in line:
            i += 1
            continue
        if re.match(r"^\[.*\]\s*\(.*Contest", line, re.I):
            i += 1
            continue
        start_utc, end_utc = _parse_date_range(line)
        if start_utc is None:
            i += 1
            continue
        location = ""
        call = ""
        url = ""
        info = ""
        i += 1
        while i < len(lines):
            cur = lines[i]
            if re.match(
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s*\d{4})?\s*-\s*",
                cur,
                re.I,
            ):
                break
            if cur.startswith("DXCC:"):
                location = cur.replace("DXCC:", "").strip()
            elif cur.startswith("Callsign:"):
                call_part = cur.replace("Callsign:", "").strip()
                call_part = re.sub(r"\*\*", "", call_part)
                link = re.search(r"\[([^\]]*)\]\(([^)]+)\)", call_part)
                if link:
                    call = (link.group(1) or "").strip()
                    url = (link.group(2) or "").strip()
                    if url and not url.startswith("http"):
                        url = "https://www.ng3k.com/Misc/" + url.lstrip("/")
                else:
                    call = re.sub(r"!?\[NEW[^\]]*\]", "", call_part).strip()
            elif cur.startswith("Info:"):
                info = cur.replace("Info:", "").strip()[:200]
            i += 1
        if call:
            result.append({
                "start_utc": start_utc,
                "end_utc": end_utc,
                "location": html.unescape(location or ""),
                "call": call,
                "url": url or "",
                "info": html.unescape(info or ""),
                "source": source,
            })
    return result


def _fetch_ng3k_plain() -> list[dict[str, Any]]:
    """Fetch NG3K plain text page and parse. Source: NG3K."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(_NG3K_PLAIN_URL)
        resp.raise_for_status()
        plain = _strip_html(resp.text)
    return _parse_blocks(plain, "NG3K")


def _fetch_ng3k_rss() -> list[dict[str, Any]]:
    """Fetch NG3K RSS and parse items into expedition entries. Source: NG3K RSS."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(_NG3K_RSS_URL)
        resp.raise_for_status()
        body = resp.text
    feed = feedparser.parse(body)
    result: list[dict[str, Any]] = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        summary = entry.get("summary") or entry.get("description") or ""
        if hasattr(summary, "strip"):
            summary = summary.strip()
        else:
            summary = str(summary)[:300]
        published = entry.get("published") or entry.get("updated") or ""
        if not published and getattr(entry, "published_parsed", None):
            try:
                published = time.strftime("%Y-%m-%dT00:00:00Z", entry.published_parsed)
            except (TypeError, ValueError):
                published = ""
        if not title:
            continue
        start_utc = published[:10] + "T00:00:00Z" if len(published) >= 10 else ""
        end_utc = published[:10] + "T23:59:59Z" if len(published) >= 10 else ""
        date_m = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s*(\d{4}))?\s*-\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s*(\d{4})",
            summary,
            re.I,
        )
        if date_m:
            start_utc, end_utc = _parse_date_range(date_m.group(0))
            start_utc = start_utc or ""
            end_utc = end_utc or ""
        call = title
        location = ""
        info_bits: list[str] = []
        segments = [s.strip() for s in title.split(" -- ") if s.strip()]
        if len(segments) >= 1:
            first = segments[0]
            if ":" in first:
                location = first.split(":", 1)[0].strip()
            if len(segments) >= 2:
                call = segments[1]
            if len(segments) >= 3:
                info_bits.append(segments[2])
        summary_clean = _strip_html(summary) if summary else ""
        source_m = re.search(r"Source:\s*[^\s].{0,80}", summary_clean, re.I) if summary_clean else None
        if source_m:
            info_bits.append(source_m.group(0).strip())
        info = " -- ".join(info_bits)[:120] if info_bits else ""
        result.append({
            "start_utc": start_utc,
            "end_utc": end_utc,
            "location": location,
            "call": call,
            "url": link or "",
            "info": info,
            "source": "NG3K RSS",
        })
    return result


def _parse_ics_events(ics_text: str) -> list[dict[str, Any]]:
    """Parse iCalendar text for VEVENTs; return list of expedition dicts with source DXCAL."""
    result: list[dict[str, Any]] = []
    event_blocks = re.split(r"BEGIN:VEVENT\s*", ics_text, flags=re.I)
    for block in event_blocks[1:]:
        end_m = re.search(r"\s*END:VEVENT", block, re.I)
        if end_m:
            block = block[:end_m.start()]
        lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        dtstart = ""
        dtend = ""
        summary = ""
        url = ""
        desc = ""
        for line in lines:
            if ":" not in line:
                continue
            if line.startswith(" "):
                continue
            key, _, value = line.partition(":")
            key = key.upper().strip()
            value = value.strip()
            if key == "DTSTART":
                dtstart = value
            elif key == "DTEND":
                dtend = value
            elif key == "SUMMARY":
                summary = value
            elif key == "URL":
                url = value
            elif key == "DESCRIPTION":
                desc = value[:200]
        if not summary:
            continue
        start_utc = ""
        end_utc = ""
        dtstart = re.sub(r"[^0-9TZ]", "", dtstart)
        dtend = re.sub(r"[^0-9TZ]", "", dtend)
        if len(dtstart) >= 15 and "T" in dtstart:
            start_utc = dtstart if dtstart.endswith("Z") else dtstart + "Z"
        elif len(dtstart) >= 8:
            start_utc = dtstart[:4] + "-" + dtstart[4:6] + "-" + dtstart[6:8] + "T00:00:00Z"
        if len(dtend) >= 15 and "T" in dtend:
            end_utc = dtend if dtend.endswith("Z") else dtend + "Z"
        elif len(dtend) >= 8:
            end_utc = dtend[:4] + "-" + dtend[4:6] + "-" + dtend[6:8] + "T23:59:59Z"
        if not end_utc and start_utc:
            end_utc = start_utc
        call = summary
        location = ""
        if " " in summary or "-" in summary:
            parts = re.split(r"\s+|\s*-\s*", summary, 1)
            call = parts[0].strip()
            if len(parts) > 1:
                location = parts[1].strip()[:80]
        result.append({
            "start_utc": start_utc,
            "end_utc": end_utc,
            "location": location,
            "call": call,
            "url": url or "",
            "info": desc or "",
            "source": "DXCAL",
        })
    return result


def _fetch_dxcal_ics() -> list[dict[str, Any]]:
    """Fetch DXCAL iCal and parse. Source: DXCAL."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(_DXCAL_ICS_URL)
        resp.raise_for_status()
        text = resp.text
    return _parse_ics_events(text)


def _normalize_call(call: str) -> str:
    """Uppercase and strip for dedup key."""
    return (call or "").upper().strip()


def _deduplicate_and_merge(sourced_lists: list[tuple[str, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    """
    Merge lists from multiple sources. Deduplicate by (normalized_call, start_date).
    When duplicate: keep entry with more info (url, info), combine source labels.
    """
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for source_label, items in sourced_lists:
        for d in items:
            call_n = _normalize_call(d.get("call") or "")
            start = (d.get("start_utc") or "")[:10]
            if not call_n or not start:
                continue
            key = (call_n, start)
            if key in by_key:
                existing = by_key[key]
                existing_sources = (existing.get("source") or "").split("; ")
                if source_label not in existing_sources:
                    existing_sources.append(source_label)
                existing["source"] = "; ".join(existing_sources)
                if (d.get("url") and not existing.get("url")) or (d.get("info") and len(d.get("info") or "") > len(existing.get("info") or "")):
                    if d.get("url"):
                        existing["url"] = d["url"]
                    if d.get("info") and len(d.get("info") or "") > len(existing.get("info") or ""):
                        existing["info"] = d["info"]
            else:
                rec = dict(d)
                rec["source"] = source_label
                by_key[key] = rec
    return list(by_key.values())


def get_dxpeditions_cached(
    enabled_sources: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Return list of DXpeditions from enabled sources (NG3K, NG3K RSS, DXCAL). Cached 6 hours.
    If enabled_sources is None, all sources are used. If enabled_sources is [] (empty list), no items are returned.
    Each item: start_utc, end_utc, location, call, url, info, source.
    Deduplicated by call + start date; source field lists which sources reported it.
    """
    global _cached_result, _cached_time
    now = time.time()
    if _cached_result is not None and (now - _cached_time) < _CACHE_MAX_AGE_SEC:
        result = _cached_result
    else:
        sourced: list[tuple[str, list[dict[str, Any]]]] = []
        try:
            ng3k = _fetch_ng3k_plain()
            sourced.append(("NG3K", ng3k))
            _log.debug("DXpeditions: NG3K plain %d", len(ng3k))
        except Exception as e:
            _log.debug("DXpeditions NG3K plain failed: %s", e)
        try:
            ng3k_rss = _fetch_ng3k_rss()
            sourced.append(("NG3K RSS", ng3k_rss))
            _log.debug("DXpeditions: NG3K RSS %d", len(ng3k_rss))
        except Exception as e:
            _log.debug("DXpeditions NG3K RSS failed: %s", e)
        try:
            dxcal = _fetch_dxcal_ics()
            sourced.append(("DXCAL", dxcal))
            _log.debug("DXpeditions: DXCAL %d", len(dxcal))
        except Exception as e:
            _log.debug("DXpeditions DXCAL failed: %s", e)
        merged = _deduplicate_and_merge(sourced)
        cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _cached_result = [d for d in merged if (d.get("end_utc") or "") >= cutoff]
        _cached_result.sort(key=lambda d: (d.get("start_utc") or "", d.get("call") or ""))
        _cached_time = now
        result = _cached_result
    if enabled_sources is not None:
        allowed = set(enabled_sources)
        result = [
            d for d in result
            if allowed.intersection((s.strip() for s in (d.get("source") or "").split(";")))
        ]
    return result
