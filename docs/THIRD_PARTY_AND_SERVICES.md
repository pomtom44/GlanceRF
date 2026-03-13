# Third-Party Dependencies and External Services

This document lists third-party libraries, CDNs, and external services that GlanceRF may use. It is intended as open transparency for end users: what your installation connects to, what data is fetched, and what is required versus optional.

---

## 1. Frontend (browser) dependencies

These are loaded in the browser when you use certain modules or features.

| What | Source | Used by | Required? |
|------|--------|--------|-----------|
| **SunCalc** (sun/moon calculations) | `cdnjs.cloudflare.com` (v1.9.0) | Sun times module, Moon module | Only if you use Sun times or Moon |
| **Leaflet** (maps) | `unpkg.com` (v1.9.4) – CSS and JS | Map module | Only if you use the Map module |
| **APRS symbol sprites** (icons for map/callsign) | `cdn.jsdelivr.net` (GitHub: hessu/aprs-symbols) | Map (QTH icon), APRS module, Callsign | Only if you show QTH on map, APRS icons, or use APRS module |
| **Moon phase images** | `img.icons8.com` (Icons8) | Moon module | Only if you use Moon module (fallback: built-in SVG) |

- **SunCalc** computes sunrise, sunset, moonrise, and moonset from your location; no data is sent to a server.
- **Leaflet** is the mapping library; map tiles and overlays come from the services listed in section 3.
- **APRS symbols** and **Icons8** moon images are read-only assets; no tracking is performed by GlanceRF (Icons8 may have its own policies; see icons8.com).

---

## 2. Map tiles and overlay services

When you use the **Map** module, the following external services may be used depending on your settings.

| Service | URL / source | Data | Required? |
|---------|----------------|------|------------|
| **Carto** | `basemaps.cartocdn.com` | Map tiles (Voyager, Positron, Dark Matter) | Only if you choose Carto as map source |
| **OpenTopoMap** | `tile.opentopomap.org` | Map tiles | Only if you choose OpenTopoMap |
| **Esri** | `server.arcgisonline.com` | Satellite/aerial imagery tiles | Only if you choose Esri |
| **NASA GIBS** | `gibs.earthdata.nasa.gov` | Night lights (VIIRS) tiles | Only if you choose NASA GIBS |
| **NOAA** | `services.swpc.noaa.gov` | Aurora forecast (OVATION) JSON | Only if you turn on Aurora overlay |
| **KC2G** | `prop.kc2g.com` | HF propagation (MUF, foF2) SVG and stations JSON | Only if you turn on KC2G propagation overlay |
| **Open-Meteo** | `api.open-meteo.com` | Weather for propagation (backend) | Only if you use KC2G propagation overlay |

Map tiles are requested by the browser based on the visible map area and zoom. Aurora and propagation overlays are fetched when those overlays are enabled.

---

## 3. Weather and sun/moon data

| Service | URL | Data | Used by | Required? |
|---------|-----|------|--------|-----------|
| **Open-Meteo** | `api.open-meteo.com` | Weather forecast, sunrise/sunset (optional) | Weather module, Sun times module (fallback) | Only if you use Weather or Sun times (Sun times can use SunCalc only) |
| **SunCalc** (see section 1) | Loaded from CDN, runs in browser | Sunrise, sunset, moonrise, moonset computed locally | Sun times, Moon | Only if you use those modules |

- **Sun times**: Can work entirely with SunCalc in the browser (no server request). If Open-Meteo is used, only latitude, longitude, and request for daily sunrise/sunset are sent.
- **Weather**: Uses Open-Meteo for forecast (location and weather parameters only).
- **Moon**: Rise/set and phase use SunCalc in the browser; no server call for moon data.

---

## 4. Contests and DXpeditions

When you use **Contests** or **DXpeditions** modules, the app fetches from the following sources depending on layout and source selection.

| Source | URL | Data | Required? |
|--------|-----|------|------------|
| **WA7BNM Contest Calendar** | `contestcalendar.com` (RSS, iCal) | Contest list | Only if you use Contests with this source |
| **SSA (Sweden)** | `contest.ssa.se` (RSS, iCal) | Contest list | Only if you use Contests with SSA |
| **RSGB (UK)** | `calendar.google.com` (iCal) | Contest list | Only if you use Contests with RSGB |
| **Custom RSS/iCal** | URL you configure | Your chosen feed | Only if you add a custom source |
| **NG3K ADXO** | `ng3k.com` (HTML, RSS) | DXpedition list | Only if you use DXpeditions with NG3K |
| **DXCAL** | `danplanet.com/dxcal.ics` | DXpedition list (iCal) | Only if you use DXpeditions with DXCAL |

Only the contest or DXpedition feed content is requested; no personal data is sent to these sites by GlanceRF.

---

## 5. Live spots (RBN, PSK Reporter, DXWatch)

The **Live spots** module (if enabled) can request data from:

| Source | URL | Data | Required? |
|--------|-----|------|------------|
| **Reverse Beacon Network (RBN)** | `reversebeacon.net`, `beta.reversebeacon.net` (raw_data PHP) | RBN spot data | Only if you use Live spots with RBN. Note: these endpoints may return 404; RBN provides historical data as zips at reversebeacon.net/raw_data/. |
| **PSK Reporter** | `retrieve.pskreporter.info` | PSK reception reports (XML) | Only if you use Live spots with PSK Reporter |
| **DXWatch** | `dxwatch.com` | DX cluster spots (HTML) | Only if you use Live spots with DXWatch |

Requests are made from the GlanceRF server (backend), not directly from the browser. No personal data is sent; only the query parameters required by each service.

---

## 6. Satellites

| Service | URL | Data | Used by | Required? |
|---------|-----|------|--------|-----------|
| **CelesTrak** | `celestrak.org` (NORAD elements) | TLE / satellite orbits | Satellite pass module | Only if you use Satellite pass module |

Used to compute pass times and (optionally) ground tracks. No personal data is sent.

---

## 7. APRS (optional)

If you configure a **callsign** in Setup and the APRS cache is enabled:

| Service | Host / URL | Data | Required? |
|---------|------------|------|------------|
| **APRS-IS** | `rotate.aprs.net` (port 10152) | Full-feed APRS packets (receive only) | No; only if you want local APRS cache for map/APRS module |

The app connects as a client and stores packets in a local SQLite database (`config_dir/cache/aprs.db`). No data is sent to APRS-IS except login (callsign-SSID and passcode; passcode is auto-computed from your callsign). See your APRS-IS provider for their terms.

---

## 8. Updates and telemetry (optional)

| Service | URL | Data | Required? |
|---------|-----|------|------------|
| **GitHub** | `api.github.com` (repos/pomtom44/GlanceRF/releases) | Release list / version check, update zip | Only if you enable update check or run an update |
| **Telemetry** | `glancerf-telemetry.zl4st.com` | Anonymous usage (version, grid size, module IDs, etc.) | No; enabled by default, opt-out in Setup |

- **Updates**: When update check is enabled, the app requests the latest release metadata and, if you choose to update, the release zip from GitHub.
- **Telemetry**: Described in [TELEMETRY.md](TELEMETRY.md). You can opt out; no callsign, location, or personal data is collected.

---

## 9. Python (server) dependencies

The server runs on Python and uses these main third-party packages (see `requirements/requirements-*.txt`):

| Package | Purpose |
|---------|---------|
| **FastAPI** | Web framework |
| **Uvicorn** | ASGI server |
| **httpx** | HTTP client for backend requests (contests, DXpeditions, spots, propagation, satellites, etc.) |
| **feedparser** | RSS/Atom parsing (contests, DXpeditions, RSS module) |
| **Skyfield** | Astronomy (sun position for GPIO, satellite passes, ground tracks) |
| **aprslib** | APRS packet parsing (APRS module, map overlay) |
| **PyQt5 / PyQtWebEngine** | Desktop window (optional) |

These do not by themselves contact external services; they are used when the features above (e.g. contests, satellites, APRS) are used.

---

## 10. What is required?

- **To run GlanceRF at all**: Only the Python dependencies and your config. No external service is strictly required for the app to start.
- **Per-module**: Each module that uses an external service only contacts that service when the module is in use and the feature is enabled (e.g. Map tiles when the Map module is shown, SunCalc when Sun times or Moon is shown).
- **Optional features**: APRS cache, telemetry, update checks, and each overlay or data source (contests, DXpeditions, live spots, propagation, aurora, etc.) are optional and can be disabled or not configured.

---

## 11. User-configured URLs

Some features let you enter your own URLs:

- **Contests**: Custom RSS or iCal feed URL.
- **DXpeditions**: Choice of built-in sources.
- **RSS module**: Your RSS feed URL.
- **Webbrowser / Webcam**: Optional remote URL.

When you provide a URL, GlanceRF will request that URL according to the feature. Only the URL you supply is used; no other third parties are added by GlanceRF for that request.

---

## 12. Summary table (quick reference)

| Category | Examples | Required? |
|----------|----------|-----------|
| Frontend libs (SunCalc, Leaflet, APRS sprites, Icons8) | cdnjs, unpkg, jsDelivr, Icons8 | Only when using the module that needs them |
| Map tiles | Carto, OpenTopoMap, Esri, NASA GIBS | Only when using Map with that source |
| Weather / sun | Open-Meteo, SunCalc (local) | Only when using Weather or Sun times |
| Contests / DXpeditions | WA7BNM, SSA, RSGB, NG3K, DXCAL | Only when using those modules and sources |
| Live spots | RBN, PSK Reporter, DXWatch | Only when using Live spots |
| Satellites | CelesTrak | Only when using Satellite pass |
| Propagation / aurora | KC2G, NOAA, Open-Meteo | Only when using Map overlays |
| APRS-IS | rotate.aprs.net | Only if APRS cache enabled (callsign set) |
| Updates / telemetry | GitHub, telemetry server | Only if you enable them |

If you want to minimise external access: disable optional features (telemetry, update check), leave APRS callsign unset, and use only modules that do not need external APIs (e.g. Clock, Date, Callsign without map).
