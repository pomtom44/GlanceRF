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

Each module has **HTML, CSS, JS files** and a **Python script** that loads them and does any processing:

```
glancerf/modules/
├── loader.py           # Helper: load_assets(__file__)
├── _custom/
│   └── _example/      # Example template (not loaded; copy to create new)
│       ├── module.py      # Loads assets, defines MODULE
│       ├── index.html     # HTML fragment for the cell
│       ├── style.css      # CSS (scoped)
│       ├── script.js      # JS for the page
│       ├── __init__.py    # Required if api_routes.py present
│       ├── layout_settings.js   # Optional: custom layout editor UI
│       ├── api_routes.py  # Optional: register API endpoints
│       └── warmer.py      # Optional: cache warmer (async def warm)
└── ...
```

## module.py

The Python script loads the 3 files and defines MODULE:

```python
"""Module description (used for Modules page)."""

from glancerf.modules.loader import load_assets

# Load HTML, CSS, JS from sibling files
inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "my_module",           # Required, unique
    "name": "My Module",         # Required
    "color": "#1a1a2e",          # Required, cell background
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [               # Optional, per-cell settings in layout editor
        {"id": "source", "label": "Data source", "type": "text", "default": ""},
    ],
    "cache_warmer": True,       # Optional: enable warmer.py
    "gpio": {                   # Optional: GPIO inputs/outputs
        "inputs": [{"id": "btn1", "name": "Button 1"}],
        "outputs": [{"id": "led1", "name": "LED 1"}],
    },
}
```

If you don't set `inner_html`, `css`, or `js`, the core will auto-load from `index.html`, `style.css`, `script.js`. Using `load_assets(__file__)` is the recommended pattern.

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
