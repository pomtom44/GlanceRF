"""
Contest list from multiple open sources (worldwide and regional).
Fetches from each source, merges and deduplicates by title + start date. No Clear Sky dependency.

Sources: WA7BNM (worldwide), SSA (Sweden), RSGB (UK). We use only known RSS/iCal feeds.
We do not crawl or scan the entire web for contest lists: that would be fragile, slow,
and resource-heavy; we rely on curated feeds from contest calendar providers instead.
"""

import re
import time
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from glancerf.logging_config import get_logger

_log = get_logger("contests.contest_service")

_WA7BNM_RSS_URL = "https://www.contestcalendar.com/calendar.rss"
_WA7BNM_ICAL_URL = "https://www.contestcalendar.com/weeklycontcustom.php"
_SSA_RSS_URL = "https://contest.ssa.se/rss/"
_SSA_ICAL_URL = "https://contest.ssa.se/ical/"
_RSGB_HF_ICAL_URL = "https://calendar.google.com/calendar/ical/a5ff31ebb1b4834dc7fff4c5415ae8251c6a9aa11f98c6af6e472b6c552b1915%40group.calendar.google.com/public/basic.ics"
_FETCH_TIMEOUT = 25
_CACHE_MAX_AGE_SEC = 3600  # 1 hour
_CUSTOM_SOURCE_TIMEOUT = 15
_ALLOWED_URL_SCHEMES = ("http://", "https://")
_MONTH_NAMES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

_cached_result: list[dict[str, Any]] | None = None
_cached_time: float = 0


def _parse_z_date(s: str) -> str | None:
    """Parse '1500Z, Dec 27' or 'Dec 27' or '1500Z, Dec 27, 2025' into ISO start_utc date."""
    s = (s or "").strip()
    # Try "HHMMZ, Mon DD, YYYY" or "HHMMZ, Mon DD"
    m = re.search(
        r"(?:(\d{4})Z?,?\s*)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s*(\d{4}))?",
        s,
        re.I,
    )
    if not m:
        return None
    _, mon, day, year = m.groups()
    year = year or str(datetime.now(timezone.utc).year)
    try:
        mo = _MONTH_NAMES.get(mon[:3].capitalize())
        if mo is None:
            return None
        return f"{year}-{mo:02d}-{int(day):02d}T00:00:00Z"
    except (ValueError, TypeError):
        return None


def _parse_date_range_in_text(text: str) -> tuple[str | None, str | None]:
    """Find first date range like '1500Z, Dec 27 to 1500Z, Dec 28' or 'Dec 27 to Dec 28'."""
    text = (text or "").replace("\n", " ")
    # "to" or "-" between two dates
    m = re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s*(\d{4}))?\s*(?:to|-)\s*"
        r"(?:(\d{4})Z?,?\s*)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,\s*(\d{4}))?",
        text,
        re.I,
    )
    if not m:
        start_utc = _parse_z_date(text)
        return (start_utc, start_utc)
    smon, sday, syear, _, emon, eday, eyear = m.groups()
    syear = syear or eyear or str(datetime.now(timezone.utc).year)
    eyear = eyear or syear
    try:
        sm = _MONTH_NAMES.get(smon[:3].capitalize())
        em = _MONTH_NAMES.get(emon[:3].capitalize())
        if sm is None or em is None:
            return (_parse_z_date(text), None)
        start_utc = f"{syear}-{sm:02d}-{int(sday):02d}T00:00:00Z"
        end_utc = f"{eyear}-{em:02d}-{int(eday):02d}T23:59:59Z"
        return (start_utc, end_utc)
    except (ValueError, TypeError):
        return (_parse_z_date(text), None)


def _fetch_wa7bnm_rss() -> list[dict[str, Any]]:
    """Fetch WA7BNM Contest Calendar RSS. Source: WA7BNM."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(_WA7BNM_RSS_URL)
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
            summary = str(summary)
        published = entry.get("published") or entry.get("updated") or ""
        if not published and getattr(entry, "published_parsed", None):
            try:
                published = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.published_parsed)
            except (TypeError, ValueError):
                published = ""
        if not title:
            continue
        start_utc, end_utc = _parse_date_range_in_text(summary)
        if not start_utc and published:
            start_utc = published[:10] + "T00:00:00Z" if len(published) >= 10 else ""
        if not end_utc:
            end_utc = start_utc or ""
        result.append({
            "title": title,
            "start_utc": start_utc or "",
            "end_utc": end_utc or "",
            "url": link or "",
            "info": (summary or "")[:200],
            "source": "WA7BNM",
        })
    return result


def _parse_ics_events(ics_text: str, source_label: str) -> list[dict[str, Any]]:
    """Parse iCalendar text for VEVENTs; return list of contest dicts (title, start_utc, end_utc, url, source)."""
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
        result.append({
            "title": summary,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "url": url or "",
            "info": desc or "",
            "source": source_label,
        })
    return result


def _fetch_wa7bnm_ical() -> list[dict[str, Any]]:
    """Fetch WA7BNM weekly iCal. Source: WA7BNM iCal."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(_WA7BNM_ICAL_URL)
        resp.raise_for_status()
        text = resp.text
    if "BEGIN:VCALENDAR" not in text.upper() and "BEGIN:VEVENT" not in text.upper():
        return []
    return _parse_ics_events(text, "WA7BNM iCal")


def _fetch_rss_generic(url: str, source_label: str) -> list[dict[str, Any]]:
    """Fetch any RSS feed and parse as contest list (title, link, start/end from summary). Source: source_label."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(url)
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
            summary = str(summary)
        published = entry.get("published") or entry.get("updated") or ""
        if not published and getattr(entry, "published_parsed", None):
            try:
                published = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.published_parsed)
            except (TypeError, ValueError):
                published = ""
        if not title:
            continue
        start_utc, end_utc = _parse_date_range_in_text(summary)
        if not start_utc and published:
            start_utc = published[:10] + "T00:00:00Z" if len(published) >= 10 else ""
        if not end_utc:
            end_utc = start_utc or ""
        result.append({
            "title": title,
            "start_utc": start_utc or "",
            "end_utc": end_utc or "",
            "url": link or "",
            "info": (summary or "")[:200],
            "source": source_label,
        })
    return result


def _fetch_ssa_rss() -> list[dict[str, Any]]:
    """Fetch SSA (Swedish) contest RSS. Source: SSA (SE)."""
    return _fetch_rss_generic(_SSA_RSS_URL, "SSA (SE)")


def _fetch_ical_generic(url: str, source_label: str) -> list[dict[str, Any]]:
    """Fetch any iCal URL and parse VEVENTs. Source: source_label."""
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        text = resp.text
    if "BEGIN:VCALENDAR" not in text.upper() and "BEGIN:VEVENT" not in text.upper():
        return []
    return _parse_ics_events(text, source_label)


def _fetch_ssa_ical() -> list[dict[str, Any]]:
    """Fetch SSA (Swedish) contest iCal. Source: SSA (SE) iCal."""
    return _fetch_ical_generic(_SSA_ICAL_URL, "SSA (SE) iCal")


def _fetch_rsgb_ical() -> list[dict[str, Any]]:
    """Fetch RSGB (UK) HF contest calendar iCal. Source: RSGB (UK)."""
    return _fetch_ical_generic(_RSGB_HF_ICAL_URL, "RSGB (UK)")


def _is_safe_url(url: str) -> bool:
    """Allow only http/https URLs."""
    u = (url or "").strip().lower()
    return any(u.startswith(s) for s in _ALLOWED_URL_SCHEMES)


def _label_from_url(url: str) -> str:
    """Derive a short label from URL hostname."""
    u = (url or "").strip()
    if not u:
        return "Custom"
    try:
        if "://" in u:
            u = u.split("://", 1)[1]
        host = u.split("/")[0].split(":")[0]
        if host:
            return host[:40]
    except Exception:
        pass
    return "Custom"


def _fetch_custom_source(url: str, kind: str, label: str | None) -> list[dict[str, Any]]:
    """Fetch one custom source by URL. kind is 'rss' or 'ical'. Returns list of contest dicts."""
    url = (url or "").strip()
    if not url or not _is_safe_url(url):
        return []
    source_label = (label or "").strip() or _label_from_url(url)
    kind = (kind or "rss").strip().lower()
    try:
        if kind in ("ical", "ics", "icalendar"):
            return _fetch_ical_generic(url, source_label)
        return _fetch_rss_generic(url, source_label)
    except Exception as e:
        _log.debug("Contests custom source %s failed: %s", url[:50], e)
        return []


def _normalize_title(title: str) -> str:
    """Normalize contest title for dedup key."""
    return (title or "").strip().upper()[:80]


def _deduplicate_and_merge(sourced_lists: list[tuple[str, list[dict[str, Any]]]]) -> list[dict[str, Any]]:
    """Merge contest lists. Deduplicate by (normalized_title, start_date). Combine source labels."""
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for source_label, items in sourced_lists:
        for d in items:
            title_n = _normalize_title(d.get("title") or "")
            start = (d.get("start_utc") or "")[:10]
            if not title_n or not start:
                continue
            key = (title_n, start)
            if key in by_key:
                existing = by_key[key]
                existing_sources = (existing.get("source") or "").split("; ")
                if source_label not in existing_sources:
                    existing_sources.append(source_label)
                existing["source"] = "; ".join(existing_sources)
                if d.get("url") and not existing.get("url"):
                    existing["url"] = d["url"]
                if d.get("info") and len(d.get("info") or "") > len(existing.get("info") or ""):
                    existing["info"] = d["info"]
            else:
                rec = dict(d)
                rec["source"] = source_label
                by_key[key] = rec
    return list(by_key.values())


def get_contests_cached(
    enabled_sources: list[str] | None = None,
    custom_sources: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Return list of contests from enabled and custom sources. Cached 1 hour for built-in only.
    If enabled_sources is None, all built-in sources are used. If enabled_sources is [] (empty list), no built-in items.
    custom_sources: list of { "url", "type" ("rss"|"ical"), "label" (optional) }. Only http/https URLs are fetched.
    Each item: title, start_utc, end_utc, url, info, source. Deduplicated by title + start date.
    """
    global _cached_result, _cached_time
    now = time.time()
    if _cached_result is not None and (now - _cached_time) < _CACHE_MAX_AGE_SEC:
        result = list(_cached_result)
    else:
        sourced: list[tuple[str, list[dict[str, Any]]]] = []
        try:
            rss_list = _fetch_wa7bnm_rss()
            sourced.append(("WA7BNM", rss_list))
            _log.debug("Contests: WA7BNM RSS %d", len(rss_list))
        except Exception as e:
            _log.debug("Contests WA7BNM RSS failed: %s", e)
        try:
            ical_list = _fetch_wa7bnm_ical()
            if ical_list:
                sourced.append(("WA7BNM iCal", ical_list))
                _log.debug("Contests: WA7BNM iCal %d", len(ical_list))
        except Exception as e:
            _log.debug("Contests WA7BNM iCal failed: %s", e)
        try:
            ssa_rss = _fetch_ssa_rss()
            if ssa_rss:
                sourced.append(("SSA (SE)", ssa_rss))
                _log.debug("Contests: SSA RSS %d", len(ssa_rss))
        except Exception as e:
            _log.debug("Contests SSA RSS failed: %s", e)
        try:
            ssa_ical = _fetch_ssa_ical()
            if ssa_ical:
                sourced.append(("SSA (SE) iCal", ssa_ical))
                _log.debug("Contests: SSA iCal %d", len(ssa_ical))
        except Exception as e:
            _log.debug("Contests SSA iCal failed: %s", e)
        try:
            rsgb_ical = _fetch_rsgb_ical()
            if rsgb_ical:
                sourced.append(("RSGB (UK)", rsgb_ical))
                _log.debug("Contests: RSGB iCal %d", len(rsgb_ical))
        except Exception as e:
            _log.debug("Contests RSGB iCal failed: %s", e)
        merged = _deduplicate_and_merge(sourced)
        cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _cached_result = [d for d in merged if (d.get("end_utc") or "") >= cutoff]
        _cached_result.sort(key=lambda d: (d.get("start_utc") or "", d.get("title") or ""))
        _cached_time = now
        _log.debug("Contests: merged %d after dedup, %d future/active", len(merged), len(_cached_result))
        result = list(_cached_result)
    if enabled_sources is not None:
        allowed = set(enabled_sources)
        result = [
            d for d in result
            if allowed.intersection((s.strip() for s in (d.get("source") or "").split(";")))
        ]
    # Merge custom sources (fetched every time; not cached)
    custom_list = custom_sources or []
    if custom_list:
        custom_sourced: list[tuple[str, list[dict[str, Any]]]] = []
        for c in custom_list:
            if not isinstance(c, dict):
                continue
            url = c.get("url") or c.get("URL") or ""
            kind = c.get("type") or c.get("kind") or "rss"
            label = c.get("label") or c.get("name") or ""
            items = _fetch_custom_source(url, kind, label or None)
            if items:
                lab = (label or "").strip() or _label_from_url(url)
                custom_sourced.append((lab, items))
        if custom_sourced:
            # Present built-in result as single-source pairs so dedup can merge with custom
            builtin_pairs = [((d.get("source") or "?").split(";")[0].strip() or "Built-in", [d]) for d in result]
            result = _deduplicate_and_merge(builtin_pairs + custom_sourced)
            cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            result = [d for d in result if (d.get("end_utc") or "") >= cutoff]
            result.sort(key=lambda d: (d.get("start_utc") or "", d.get("title") or ""))
    return result
