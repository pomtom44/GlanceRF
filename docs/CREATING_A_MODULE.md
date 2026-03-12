# How to Create a Module

This guide explains how to add a new **cell module** to GlanceRF. A module is a self-contained block that can be placed in any grid cell (e.g. Clock, Weather, Map). You provide a folder with the required files; the app discovers it automatically and injects its HTML, CSS, and JS into the page.

**Where to put your module:** Put your module in **`glancerf/modules/_custom/`**. Modules in `_custom/` are **not overwritten** when you update GlanceRF. Modules outside `_custom/` can be overwritten during an update. See [Custom modules (survive updates)](#11-custom-modules-survive-updates).

---

## Table of contents

1. [Quick start](#1-quick-start)
2. [Folder structure and files](#2-folder-structure-and-files)
3. [module.py – define the module](#3-modulepy--define-the-module)
4. [index.html – cell content](#4-indexhtml--cell-content)
5. [style.css – module styles](#5-stylecss--module-styles)
6. [script.js – behaviour and updates](#6-scriptjs--behaviour-and-updates)
7. [Naming conventions (important)](#7-naming-conventions-important)
8. [How the core uses your module](#8-how-the-core-uses-your-module)
9. [Settings in JavaScript](#9-settings-in-javascript)
10. [Global variables (callsign and location)](#10-global-variables-callsign-and-location)
11. [Custom modules (survive updates)](#11-custom-modules-survive-updates)
12. [Module API routes (optional)](#12-module-api-routes-optional)
13. [GPIO support (optional)](#13-gpio-support-optional)
14. [Map overlay modules](#14-map-overlay-modules)
15. [Checklist](#15-checklist)

---

## 1. Quick start

1. Copy the **`_example`** folder from **`glancerf/modules/_custom/_example/`**. Rename the copy to your module id (e.g. `my_timer`) and keep it inside **`glancerf/modules/_custom/`** (e.g. `glancerf/modules/_custom/my_timer/`). Folder names must **not** start with `_` (those are skipped).
2. Edit **module.py**: set `id`, `name`, and `color` to match your module.
3. Edit **index.html**: put the HTML structure for one cell, using classes that start with your module id + underscore (e.g. `my_timer_label`).
4. Edit **style.css**: scope all rules under `.grid-cell-{id}`.
5. Edit **script.js**: use `document.querySelectorAll('.grid-cell-{id}')` to find your cells and update content.

Restart the app (or reload the page). Your module appears in the layout editor and can be placed in any cell.

---

## 2. Folder structure and files

Each module is a **folder**. You can put it in one of two places:

| Location | Behaviour on GlanceRF updates |
|----------|-------------------------------|
| **`glancerf/modules/`** (outside `_custom/`) | May be overwritten. Use only for quick local testing. |
| **`glancerf/modules/_custom/`** | **Not overwritten.** Always use this for your own modules. |

Folders whose names start with `_` are skipped (except `_custom` itself).

| File | Purpose |
|------|---------|
| **module.py** | Required. Defines `id`, `name`, `color`, and optional `settings`. |
| **index.html** | Optional. HTML fragment injected inside each grid cell. |
| **style.css** | Optional. CSS for this module; scope under `.grid-cell-{id}`. |
| **script.js** | Optional. JavaScript for this module. |
| **api_routes.py** | Optional. Define `register_routes(app)` to add API endpoints. |
| **layout_settings.js** | Optional. Custom setting UI in the layout editor. |
| **warmer.py** | Optional. Cache warmer: `async def warm(settings, config)`. |

If you don't set `inner_html`, `css`, or `js` in module.py, the core auto-loads from `index.html`, `style.css`, `script.js`. You can use `load_assets(__file__)` from `glancerf.modules.loader` to load them explicitly.

---

## 3. module.py – define the module

Define a dict named **`MODULE`** with at least:

- **`id`** (str) – Unique identifier. Use lowercase letters, numbers, underscores (e.g. `my_timer`). Forms the CSS class `grid-cell-{id}`.
- **`name`** (str) – Label shown in the UI.
- **`color`** (str) – Background colour for the cell (e.g. `"#333333"`).

Optional:

- **`settings`** (list) – Per-cell setting definitions. Each item: `id`, `label`, `type` (`text`, `select`, `number`, `range`), `default`, and for select: `options`.
- **`gpio`** (dict) – `inputs` and/or `outputs` for GPIO support. See [GPIO support](#13-gpio-support-optional).

Example:

```python
from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "my_timer",
    "name": "My Timer",
    "color": "#1a1a2e",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "label", "label": "Label", "type": "text", "default": ""},
        {"id": "mode", "label": "Mode", "type": "select", "options": [
            {"value": "up", "label": "Count up"},
            {"value": "down", "label": "Count down"},
        ], "default": "down"},
    ],
}
```

---

## 4. index.html – cell content

- This file is the **inner HTML** of the cell. The core creates a `<div class="grid-cell grid-cell-{id}" data-row="..." data-col="...">`; your HTML is inserted **inside** that div.
- Use only the structure you need. Do not add `<html>` or `<body>`.
- Give elements classes that start with your **module id + underscore** (e.g. `my_timer_label`).

---

## 5. style.css – module styles

- Scope all rules under **`.grid-cell-{id}`** so they only affect your module's cells.
- Use the same class names as in index.html.

Example:

```css
.grid-cell-my_timer {
    display: flex;
    align-items: center;
    justify-content: center;
}
.grid-cell-my_timer .my_timer_value {
    font-size: 1.5em;
    font-weight: bold;
}
```

---

## 6. script.js – behaviour and updates

- Use **`document.querySelectorAll('.grid-cell-{id}')`** to find every cell that uses your module.
- Use **`cell.querySelector('.my_timer_label')`** to get elements inside each cell.
- Use **`cell.getAttribute('data-row')`** and **`data-col`** to build a per-cell key for settings.

Example:

```javascript
(function() {
    function update() {
        document.querySelectorAll('.grid-cell-my_timer').forEach(function(cell) {
            var valueEl = cell.querySelector('.my_timer_value');
            if (valueEl) valueEl.textContent = new Date().toLocaleTimeString();
        });
    }
    update();
    setInterval(update, 1000);
})();
```

---

## 7. Naming conventions (important)

| What | Convention | Example |
|------|------------|---------|
| **Folder name** | Same as module `id`; no leading `_` | `my_timer` |
| **Cell class** | Added by core: **`grid-cell-{id}`** | `.grid-cell-my_timer` |
| **Your classes** | **`{id}_`** + name | `.my_timer_display`, `.my_timer_value` |

---

## 8. How the core uses your module

- **Discovery:** The app scans `glancerf/modules/` for folders that do not start with `_` and contain **module.py**. It loads MODULE and, if present, reads index.html, style.css, script.js.
- **Rendering:** For each cell, the core looks up the module by id, gets `color` and `inner_html`, and builds a div with class `grid-cell grid-cell-{id}`.
- **API routes:** If your module has **api_routes.py**, the core calls `register_routes(app)` at startup (from `main.py`). Your routes are registered on the same FastAPI app.

---

## 9. Settings in JavaScript

If your module has **settings**, they are in **`window.GLANCERF_MODULE_SETTINGS`**:

- **Key:** `"row_col"` (e.g. `"0_1"`).
- **Value:** Object mapping setting id to value.

Example:

```javascript
var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
var r = cell.getAttribute('data-row');
var c = cell.getAttribute('data-col');
var cellKey = (r != null && c != null) ? r + '_' + c : '';
var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
var label = (ms.label || '').toString().trim();
```

---

## 10. Global variables (callsign and location)

From Setup, the core exposes:

| Variable | Description |
|----------|-------------|
| **`window.GLANCERF_SETUP_CALLSIGN`** | User's callsign. Empty if not set. |
| **`window.GLANCERF_SETUP_LOCATION`** | Default location (grid square or lat,lng). Empty if not set. |

Use as fallbacks when a per-cell setting is blank:

```javascript
var call = (ms.callsign || window.GLANCERF_SETUP_CALLSIGN || '').toString().trim();
var locStr = (ms.location || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
```

---

## 11. Custom modules (survive updates)

- **Modules in `_custom/`** – Preserved when you update GlanceRF.
- **Modules outside `_custom/`** – May be overwritten. Do not use for your own modules.
- If a built-in module has the same id as your custom one, your custom version takes precedence.

---

## 12. Module API routes (optional)

If your module needs API endpoints, add **api_routes.py** with a function **`register_routes(app: FastAPI) -> None`**:

```python
# glancerf/modules/_custom/my_module/api_routes.py
from fastapi import FastAPI
from glancerf.config import get_logger

_log = get_logger("my_module.api_routes")


def register_routes(app: FastAPI) -> None:
    @app.get("/api/my_module/data")
    async def get_my_module_data():
        try:
            result = {"data": "example"}
            return result
        except Exception as e:
            _log.debug("get_data failed: %s", e)
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": str(e)}, status_code=502)
```

The core discovers modules with api_routes.py and calls `register_routes(app)` at startup. Use paths under `/api/`.

For a full example with cached data and custom settings, see **satellite_pass** in `glancerf/modules/satellite_pass/`.

---

## 13. GPIO support (optional)

On systems with GPIO (e.g. Raspberry Pi), GlanceRF can assign module inputs and outputs to physical pins. Configure on the **GPIO** page (Menu → GPIO).

### Declaring GPIO in module.py

```python
MODULE = {
    "id": "my_rig",
    "name": "My Rig",
    "color": "#1a1a2e",
    "gpio": {
        "inputs": [{"id": "ptt_trigger", "name": "PTT trigger"}],
        "outputs": [{"id": "led", "name": "Status LED"}],
    },
}
```

### Handling inputs

Define **`GPIO_INPUT_HANDLERS`** in module.py:

```python
def _on_ptt_trigger(value: bool):
    if value:
        pass  # start transmitting
    else:
        pass  # stop transmitting

GPIO_INPUT_HANDLERS = {"ptt_trigger": _on_ptt_trigger}
```

### Driving outputs

```python
from glancerf.gpio import set_output

set_output("my_rig", "led", True)   # on
set_output("my_rig", "led", False)  # off
```

---

## 14. Map overlay modules

Modules that feed data to the map (e.g. **aprs**, **satellite_pass**) can appear in the main grid or in **Map only modules** (`map_overlay_layout`). Both feed the map when it is in the layout.

- Add your module to `map_overlay_layout` via the **Map only modules** page (`/map-modules`).
- The core passes `window.GLANCERF_MAP_OVERLAY_MODULES` and `window.GLANCERF_MAP_OVERLAY_LAYOUT` to the frontend.
- The map script uses `hasMapOverlayForModule(moduleId)` to decide if an overlay should show, and `getMergedModuleSettings(moduleId)` to read merged settings from all instances (grid cells and map overlay). Merge rules are uniform: booleans use OR (on wins), JSON objects merge recursively with OR for nested booleans, other settings use first non-empty. No module-specific logic in the core.

---

## 15. Checklist

- [ ] Copied `_custom/_example/` and renamed to your module id (no leading `_`).
- [ ] **module.py**: Set `id`, `name`, `color`; add `settings` if needed.
- [ ] **index.html**: Inner content only; classes use **`{id}_`** prefix.
- [ ] **style.css**: All rules scoped under **`.grid-cell-{id}`**.
- [ ] **script.js**: Find cells with `querySelectorAll('.grid-cell-{id}')`; read settings from `window.GLANCERF_MODULE_SETTINGS[cellKey]`.
- [ ] Put your module in **`glancerf/modules/_custom/`**.
- [ ] If API endpoints needed: add **api_routes.py** with `register_routes(app)`.
- [ ] If GPIO needed: add `gpio` to MODULE; define `GPIO_INPUT_HANDLERS` for inputs; use `set_output()` from `glancerf.gpio` for outputs.

For a minimal reference, see **`_custom/_example/`**. For API routes and cached data, see **satellite_pass**. For map overlay, see **aprs**.
