# Satellite APIs comparison for GlanceRF

This document compares APIs that can provide satellite list, position, pass predictions, and ground track data for the satellite_pass module.

## Our current needs

| Need | Description | Current usage |
|------|-------------|---------------|
| **Satellite list** | NORAD ID + name, ham/amateur only (stations + amateur) | 1 request per 6 h (cached), 2 groups |
| **TLE** | Two-line elements per NORAD for SGP4 | 1 request per satellite per passes/tracks call |
| **Pass data** | Current position (az, el, up) + next pass (rise/set, max el, duration) | Up to 20 NORADs per request; we fetch TLE per sat then compute with Skyfield |
| **Ground track** | Past (tail) + future (lead) + current [lat,lon] for map | Up to 15 NORADs; we fetch TLE per sat then compute with Skyfield |

So a single dashboard load can trigger: 1 list (cached) + up to 20 TLE (passes) + up to 15 TLE (tracks) = up to 35 TLE requests to CelesTrak, plus in-memory Skyfield computation.

---

## API comparison

### 1. CelesTrak (current)

| Aspect | Details |
|--------|---------|
| **URL** | https://celestrak.org/NORAD/elements/gp.php |
| **List** | `GROUP=stations` and `GROUP=amateur`, `FORMAT=json`. Curated ham/ISS list. |
| **TLE** | `CATNR=<norad>&FORMAT=tle`. One NORAD per request. |
| **Position / pass / track** | Not provided; we compute with Skyfield from TLE. |
| **Rate limits** | Not documented. Heavy use can result in 403 and ~2 h IP block. |
| **Auth** | None. |
| **Pros** | Free, no key, authoritative TLE source; we control pass/track logic. |
| **Cons** | No published limits; 403 risk; many TLE requests (one per sat per passes and per tracks). |

**Fit:** Good for list + TLE. Pass and track are computed locally, so we are only limited by TLE request volume and 403 risk.

---

### 2. N2YO

| Aspect | Details |
|--------|---------|
| **URL** | https://api.n2yo.com/rest/v1/satellite/ |
| **List** | No curated “ham only” list. Large catalog (33k+ objects). We would still use CelesTrak (or our cache) for the dropdown list. |
| **TLE** | `/tle/{id}` – 1000 requests/hour. |
| **Positions** | `/positions/{id}/{lat}/{lng}/{alt}/{seconds}` – ground track (lat/lon per second) + azimuth/elevation vs observer. 1000/hour. **One satellite per request.** |
| **Passes** | `/radiopasses/{id}/{lat}/{lng}/{alt}/{days}/{min_elevation}` – radio (ham) passes. **100 requests/hour.** One satellite per request. |
| **Auth** | Free API key required (apiKey=). |
| **Pros** | Documented hourly limits; radiopasses are ham-oriented; positions give both ground track and az/el in one call per sat. |
| **Cons** | One sat per request for positions and radiopasses. Pass limit 100/h: with 20 sats per page we could do 5 full page loads per hour. Need to keep list from CelesTrak (or filter N2YO). |

**Fit:** Best if we want to **replace** our own pass/track computation with API calls and are okay with one request per satellite and the 100 passes/hour cap. We could use N2YO for passes + positions (track) and keep CelesTrak for list (and optionally TLE as fallback).

---

### 3. SatChecker (IAU CPS) Ephemeris API

| Aspect | Details |
|--------|---------|
| **URL** | https://satchecker.cps.iau.org/ (ephemeris: `/ephemeris/name-jdstep/`) |
| **List** | We previously used `tools/tles-at-epoch` for list; could use again or keep CelesTrak for list. |
| **TLE** | SatChecker uses CelesTrak/Space-Track TLEs internally; no direct “TLE only” endpoint in the same way. |
| **Position / pass / track** | `/ephemeris/name-jdstep/`: name (CelesTrak name), lat/lon/elevation, startjd/stopjd, stepjd. Returns positions over time (RADEC, alt/az, range, illuminated). **One satellite per request** (by name). We could derive pass and ground track from this. |
| **Rate limit** | 1 request per second per IP (~3600/hour). |
| **Auth** | None. |
| **Pros** | Free, no key; predictable rate limit; alt/az and time series; same TLE sources as CelesTrak. |
| **Cons** | Query by **name** (must match CelesTrak), not NORAD; one sat per request; we must map NORAD→name and request small stepjd for 1‑min-style track. |

**Fit:** Good if we want to move position/pass/track off CelesTrak and our server, with a clear 1 req/s limit. Requires name↔NORAD mapping and parsing ephemeris into our pass/track shape.

---

## Recommendation summary

| Goal | Suggested approach |
|------|--------------------|
| **Minimal change, reduce 403 risk** | Keep current design; add **TLE caching** (e.g. by NORAD, 1–2 h TTL) to cut repeated TLE requests. List stays CelesTrak, 6 h cache. |
| **Documented limits, less CelesTrak dependency** | Use **N2YO** for passes (`/radiopasses`) and positions/ground track (`/positions`). Keep **CelesTrak for list only** (cached 6 h). Accept one request per satellite and 100 passes/hour; add N2YO API key to config. |
| **No API key, predictable limit** | Use **SatChecker ephemeris** for position + pass + track derivation. Keep **CelesTrak for list** (and NORAD→name mapping). One request per satellite per time range, 1 req/s. |
| **Keep full control, no new dependencies** | Stay with **CelesTrak + Skyfield**; add **TLE cache** and consider a short in-memory cache for pass/track results (we already cache at HTTP layer for 45s/90s). |

**Best for our needs (list + pass + track, friendly limits):**  
- **N2YO** if we are okay with a free API key and 100 passes/hour (and one request per sat).  
- **SatChecker ephemeris** if we prefer no key and a fixed 1 req/s limit and are okay deriving pass/track from ephemeris and using satellite name.

**Quick win without switching provider:**  
Add **TLE caching** in `satellite_service` (e.g. by NORAD, 1–2 h) so repeated passes/tracks for the same sats do not hit CelesTrak every time.
