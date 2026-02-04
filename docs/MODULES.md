## Map module

### Map center (grid square or coordinates)

In **"Map center (grid square or lat,lng)"** you can use either:

- **Maidenhead grid square** – 2, 4, or 6 characters (e.g. `JF96`, `JF96re`). The map is centered on the **centre** of that grid square. Case does not matter.
- **Latitude, longitude** – Decimal degrees, comma-separated (e.g. `52.5,-1.5` or `-43.2, 170.1`).

Leave the field empty to use the default center (20°N, 0°E).

### Map source and tile style

- **Map source** – Choose **Carto**, **OpenTopoMap**, **Esri (satellite)**, or **NASA GIBS**.
- **Tile style** – Second dropdown; options depend on the source:
  - **Carto**: Voyager, Positron, Positron (no labels), Dark Matter, Dark Matter (no labels).
  - **OpenTopoMap**: Default (only option).
  - **Esri (satellite)**: World Imagery (satellite/aerial, no API key).
  - **NASA GIBS**: Night Lights (VIIRS).

### Zoom level

- **Zoom level** – 0–18 for Carto, OpenTopoMap, and Esri. NASA GIBS Night Lights is limited to zoom 8; the map will clamp to the allowed range.

### Map overlays

- **Grid overlay** – **None**, **Tropics** (Cancer/Capricorn lines), **Lat/Long** (30° grid), or **Maidenhead**.
- **Day/night terminator line** – On/Off. Shows the current day/night boundary with a soft twilight gradient.
- **Sun and moon on map** – On/Off. Shows the subsolar and sublunar positions as markers on the map.
- **Aurora forecast overlay** – On/Off. Shows NOAA OVATION aurora probability as a colour overlay (low to high chance).
- **Aurora overlay opacity** – 0–100%. Slider to adjust how strong the aurora overlay appears (100% = fully opaque).
- **Propagation overlay** – **None**, **HF: KC2G MUF (3000 km)**, **HF: KC2G foF2 (NVIS)**, **VHF/UHF: Tropo**, or **VHF: APRS (144 MHz cache)**. Colour overlay for band conditions; APRS uses local cache data only.
- **Propagation overlay opacity** – 0–100%. Slider for propagation overlay strength.
- **APRS data age (H:MM)** – How far back to show APRS stations (e.g. `0:30` for 30 minutes, `6:00` for 6 hours). Used for propagation history and for hiding older APRS locations.
- **APRS station locations** – On/Off. When on, shows APRS stations from the local cache on the map (no live APRS-IS connection).
- **APRS display** – **Dots (age: green to red)** or **Icons (APRS symbol)**. Dots colour by how recently the station was seen; icons use the APRS symbol from the packet (e.g. house, car, node).
- **APRS filter (locations display only)** – Optional p/ prefix filter (e.g. `p/ZL`) so only stations whose callsign starts with the given prefix are shown. Does not change API or propagation data.

---

## Clock module

When you select the **Clock** module for a cell:

- **Show date** – On/Off. When on, the current date (e.g. Mon 27 Jan 2025) is shown above the times.
- **Local time** – On/Off.
- **UTC time** – On/Off.
- **Third time (timezone or city)** – Dropdown: **None** or a timezone (e.g. London, Tokyo). If set to **None**, no third line is shown.

If only one of local/UTC/third is on, that line is shown as the primary (larger) time. If none are on, the cell will effectively be empty.

---

## Date module

A cell that shows only the current date (weekday, day, month, year).

- **Date format** – **Day Month Year** (e.g. 27 Jan 2025), **Month Day Year** (e.g. Jan 27, 2025), or **Year Month Day** (e.g. 2025 Jan 27).

The date updates once per minute (no seconds). Use the **Clock** module if you need both time and date in one cell.

---

## Callsign / QTH module

A cell that shows your callsign, grid square (QTH), and an optional comment. All text comes from the module settings; no live data or APIs.

- **Callsign** – Your amateur radio callsign (e.g. AB1CD). Shown on the first line in bold.
- **Grid square / QTH** – Maidenhead grid (e.g. RE78hk) or any location text. If 2–6 characters, it is shown as "Grid: XX00xx"; otherwise the text is shown as entered.
- **Comment (optional)** – Free text (e.g. "Home station", "Portable"). Shown in smaller italic text below; leave empty to hide.

---

## Countdown / Stopwatch module

A cell that either counts down to a target date/time or shows elapsed time from a start date/time. All times are in local time; the display updates every second.

- **Mode** – **Countdown (to target)** or **Stopwatch (elapsed from start)**.
- **Date (YYYY-MM-DD)** – For countdown: the target date. For stopwatch: the start date. Use format `YYYY-MM-DD` (e.g. `2025-12-31`).
- **Time (optional, HH:MM or HH:MM:SS)** – For countdown: target time on that day (default midnight if omitted). For stopwatch: start time (default midnight if omitted). Examples: `23:59`, `14:30:00`.
- **Label (optional)** – Shown above the timer. For countdown, when the target has passed the label is shown (or "Expired" if label is empty).

Countdown shows time remaining (e.g. `2d 14h 23m 45s`) until the target; after that it shows your label or "Expired". Stopwatch shows elapsed time from the given start.

---

## Analog clock module

A cell that shows a traditional analog clock face (circle with hour, minute, and optional second hands). The clock updates every second.

- **Show seconds hand** – On/Off. When on, the red second hand is shown; when off, only hour and minute hands (fewer updates if you prefer).
- **Time zone** – **Local** (browser time) or **UTC**.

The face uses 12/3/6/9 tick marks and scales to fit the cell.

---

## Weather module

A cell that shows current weather from the Open-Meteo API (no API key). Location is set by grid square or lat,lng only (no browser geolocation).

- **Grid square or lat,lng** – Maidenhead grid (e.g. `RE78hk`) or decimal coordinates (e.g. `-43.5,172.6`).
- **Units** – **Metric** (C, km/h, hPa) or **Imperial** (F, mph, inHg).
- **Show conditions** – On/Off. Short text (e.g. Clear, Partly cloudy, Rain).
- **Show temperature** – On/Off.
- **Show feels like** – On/Off. Apparent temperature.
- **Show humidity** – On/Off.
- **Show wind** – On/Off. Speed and direction.
- **Show pressure** – On/Off. Surface pressure (hPa).

Data is refreshed about every 15 minutes. Requires network access.

---

## Sunrise / Sunset module

A cell that shows sunrise and sunset times for a location. Uses the Open-Meteo API (no API key). Times are in the location's local time.

- **Grid square or lat,lng** – Maidenhead grid (e.g. `RE78hk`) or decimal coordinates (e.g. `-43.5,172.6`).
- **Show sunrise** – On/Off.
- **Show sunset** – On/Off.
- **Show moon phase** – On/Off. When on, shows current lunar phase (e.g. Full moon, First quarter). Computed in the browser; no API.

Data is cached for 24 hours and refreshed hourly. Requires network access for sunrise/sunset.

---

## Moon module

A cell that shows the current moon phase (icon and name), illumination percentage, and optional moonrise and moonset times. Rise/set uses Open-Meteo; phase is computed in the browser.

- **Grid square or lat,lng** – Location for moonrise/moonset. Uses **Setup location** if blank.
- **Show moon phase** – On/Off.
- **Show moonrise** – On/Off.
- **Show moonset** – On/Off.

---

## RSS module

A cell that shows recent items from an RSS or Atom feed. You provide the feed URL; the backend fetches and caches it.

- **RSS feed URL** – Full URL of the RSS/Atom feed (e.g. `https://example.com/feed.xml`).
- **Max items to show** – How many items to display (1–50).
- **Refresh interval (minutes)** – How often to refetch the feed (1–120).

Requires network access.

---

## Satellite pass module

A cell that shows a HamClock-style satellite pass display: sky dome with horizon and elevation rings, next pass path, current position, and rise/set times. Data comes from CelesTrak TLEs via the backend (Skyfield).

- **Grid square or lat,lng** – Observer location for pass prediction (Maidenhead or decimal coordinates). Uses **Setup location** if blank.
- **Satellites to track** – Tickbox list of trackable satellites (space stations and amateur-radio sats from CelesTrak). Select one or more; the first in the list with pass data is shown.

**Satellite list:** The full list is stored in **satellite_list.json** (same directory as the main config). On first run or when the file is missing, it is populated from CelesTrak. The list is refreshed from CelesTrak about every 24 hours when the list API is used. **Config** stores only the **selected** NORAD IDs (per cell) in the main config file. When you open the Modules editor, all satellites from the JSON are shown; only those in config are checked. If a satellite is removed from CelesTrak and the list is refreshed, that NORAD ID is automatically removed from your selected satellites in config (so config stays in sync with the list).

The display shows: satellite name, "Rise in Xm @ AZ" or "Set in Xm @ AZ", a sky dome (horizon, 30/60 deg rings, compass, pass arc, current position dot), and Az/El. Data refreshes about every 45 seconds. Requires network access.

---

## Contests module

A cell that shows upcoming amateur radio contests from WA7BNM and other open sources (SSA Sweden, RSGB UK). You can add custom RSS or iCal URLs.

- **Max entries to show** – How many contest entries to display.
- **Data sources** – Tick which built-in sources to use (WA7BNM, SSA, RSGB).
- **Custom sources (RSS / iCal URLs)** – Optional URLs for additional contest calendars.

Requires network access.

---

## DXpeditions module

A cell that shows upcoming DXpeditions from NG3K Announced DX Operations (ADXO).

- **Max entries to show** – How many DXpedition entries to display.
- **Data sources** – Tick which built-in sources to use.

Requires network access.
