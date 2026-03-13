# Modules

Cell modules are folders under `glancerf/modules/` (built-in) or `glancerf/modules/_custom/` (user modules; survive updates).

**Folders whose names start with `_` are skipped** and not loaded. Use this for templates (e.g. `_example`) that you copy to create new modules.

## Built-in modules

| Module | Description |
|--------|-------------|
| `analog_clock` | Analog clock face, timezone, optional seconds |
| `callsign` | Callsign, grid, comment; On The Air indicator; QTH on map |
| `clock` | Local, UTC, optional third timezone, optional date |
| `contests` | Contest calendar from multiple sources |
| `countdown` | Countdown, stopwatch, or live stopwatch; GPIO + keyboard start/stop/reset |
| `date` | Current date (dmy/mdy/ymd) |
| `dxpeditions` | DXpedition alerts |
| `gps` | GPS stats when connected (position, time, altitude, speed, satellites) |
| `live_spots` | PSK Reporter spots (list or table by band) |
| `map` | Map with tiles, grid, terminator, overlays |
| `moon` | Moon phase, moonrise, moonset |
| `on_the_air` | On/Off The Air; GPIO + keyboard shortcut |
| `rss` | RSS/Atom feed |
| `satellite_pass` | Satellite positions, passes, map overlays |
| `sun_times` | Sunrise/sunset; optional moon; GPIO sun_up |
| `weather` | Open-Meteo weather |
| `webcam` | Webcam stream (device or remote) |
| `webbrowser` | Embedded web page (iframe or proxy) |

Map overlay modules (`satellite_pass`, etc.) can appear in the grid or in `map_overlay_layout`; both feed the map when it is in the layout.

## Module Structure

Each module is a folder with `module.py` (required), `index.html`, `style.css`, `script.js`, and optional `api_routes.py`, `layout_settings.js`, `warmer.py`. See [CREATING_A_MODULE.md](CREATING_A_MODULE.md) for a step-by-step guide.

## Map overlay modules

Modules in `map_overlay_layout` (configured via Map only modules page) feed data to the map when the map is in the layout. The core:

- Loads their CSS/JS when the map is in the layout
- Warms their caches (via warmer.py)
- Passes `window.GLANCERF_MAP_OVERLAY_MODULES` to the frontend

The map module uses this to show overlays from both grid cells (e.g. satellite_pass in layout) and map-only modules.

**Note:** Map overlay modules currently have no per-module settings UI on the Map only modules page. For modules that need settings (e.g. satellite_pass with satellite selection), add the module to the main grid layout as well, or use it only in the grid. The cache warmer passes empty settings to map-only modules.

## Files

| File | Purpose |
|------|---------|
| `module.py` | MODULE dict; required |
| `index.html` | Inner HTML for the cell |
| `style.css` | CSS injected once per page |
| `script.js` | JS injected once per page |
| `layout_settings.js` | Custom UI in layout editor (loaded per module) |
| `api_routes.py` | `register_routes(app)` to add API endpoints |
| `warmer.py` | `async def warm(settings, config)` for cache warming |

## API Routes

If your module needs API endpoints:

```python
# api_routes.py
from fastapi import FastAPI

def register_routes(app: FastAPI) -> None:
    @app.get("/api/my_module/data")
    async def get_data():
        return {"items": []}
```

Routes are auto-registered at startup.

## Cache Warmer

For modules that fetch external data, add `warmer.py`:

```python
# warmer.py
async def warm(settings: dict, config) -> None:
    # Pre-fetch data so first page load is fast
    pass
```

Set `MODULE["cache_warmer"] = True`. The cache warmer runs periodically when headless.

## Custom Layout Settings

`layout_settings.js` is loaded in the layout editor. It can add custom UI and sync values into hidden inputs with `name="ms_<row>_<col>__<setting_id>"`.

## Discovery

- Built-in: `glancerf/modules/<name>/`
- Custom: `glancerf/modules/_custom/<name>/`
- Custom overrides built-in when same `id`
- Folders starting with `_` are skipped
