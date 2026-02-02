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

A cell that shows the current moon phase (icon and name) and illumination percentage. No API; computed in the browser.

---

## RSS module

A cell that shows recent items from an RSS or Atom feed. You provide the feed URL; the backend fetches and caches it.

- **Feed URL** – Full URL of the RSS/Atom feed (e.g. `https://example.com/feed.xml`).

Items are shown as a list; the number of items and refresh interval are fixed. Requires network access.
