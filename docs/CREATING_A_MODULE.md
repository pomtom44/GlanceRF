# How to Create a Module

This guide explains how to add a new **cell module** to GlanceRF. A module is a self-contained block that can be placed in any grid cell (e.g. Clock, Weather, Map). You provide a folder with four files; the app discovers it automatically and injects its HTML, CSS, and JS into the page.

**Where to put your module:** Put your module in **`glancerf/modules/_custom/`**. Modules in `_custom/` are **not overwritten** when you update GlanceRF. Modules you add directly under `glancerf/modules/` (outside `_custom/`) **can be overwritten or removed** during an update, so use `_custom/` for anything you want to keep. See [Custom modules (survive updates)](#11-custom-modules-survive-updates) for details.

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
    - [12.5. Satellite_pass API methods (reference)](#125-satellite_pass-api-methods-reference)
    - [12.6. Using the universal cache](#126-using-the-universal-cache)
13. [GPIO support (optional)](#13-gpio-support-optional)
14. [Checklist](#14-checklist)
15. [Cache warmer (optional, headless)](#15-cache-warmer-optional-headless)

---

## 1. Quick start

1. Copy the **`_example`** template folder from **`glancerf/modules/_custom/_example/`**. Rename the copy to your module id (e.g. `my_timer`; no leading `_`) and keep it inside **`glancerf/modules/_custom/`** (e.g. `glancerf/modules/_custom/my_timer/`) so it is not overwritten when you update GlanceRF. The template includes **`__init__.py`**; keep it (required if you add api_routes.py later).
2. Rename the folder to your module **id** (e.g. `my_timer`). Use letters, numbers, and underscores only. Do **not** start the folder name with `_` (those folders are ignored).
3. Edit **module.py**: set `id`, `name`, and `color` to match your module.
4. Edit **index.html**: put the HTML structure for one cell, using classes that start with your module id + underscore (e.g. `my_timer_label`).
5. Edit **style.css**: scope all rules under `.grid-cell-{id}` and use the same class names.
6. Edit **script.js**: use `document.querySelectorAll('.grid-cell-{id}')` to find your cells, and `cell.querySelector('.my_timer_label')` (etc.) to update content.

Restart the app (or reload the page). Your module appears in the layout editor's module list and can be placed in any cell.

---

## 2. Folder structure and files

Each module is a **folder**. You can put it in one of two places:

| Location | Behaviour on GlanceRF updates |
|----------|-------------------------------|
| **`glancerf/modules/`** (outside `_custom/`) | **May be overwritten or removed.** This is where built-in modules (clock, weather, map, etc.) live. When you update the app, this tree can be replaced, so any module you add here might be lost. Use this only for quick local testing. |
| **`glancerf/modules/_custom/`** | **Not overwritten.** The updater preserves `_custom/`, so modules you put here survive updates. The app loads modules from both locations; if a custom module has the same **id** as a built-in one, the custom version is used. **Always use `_custom/` for your own modules.** See [Custom modules (survive updates)](#11-custom-modules-survive-updates). |

The folder name must **not** start with `_` (folders starting with `_` are skipped and not loaded as modules; the `_custom` folder itself is the single exception).

Required file:

| File        | Purpose |
|------------|---------|
| **module.py** | Defines the module: `id`, `name`, `color`, and optional `settings`. Required. |

Optional files (if present, the loader uses them; otherwise the module has no HTML/CSS/JS):

| File        | Purpose |
|------------|---------|
| **index.html** | HTML fragment injected **inside** each grid cell that uses this module. |
| **style.css**  | CSS for this module. Loaded once per page; scope under `.grid-cell-{id}`. |
| **script.js**  | JavaScript for this module. Loaded once per page; finds and updates this module's cells. |
| **\_\_init\_\_.py** | **Required if you have api_routes.py.** An empty or minimal file that makes the folder a Python package so the core can import `api_routes`. Without it, the module will fail to load with "is not a package" or "Missing dependency". The example template includes this file. |
| **api_routes.py** | Optional. If present, the core calls **`register_routes(app)`** at startup so your module can register its own API endpoints (e.g. GET /api/my_module/data). See [Module API routes (optional)](#12-module-api-routes-optional). **Requires \_\_init\_\_.py in the same folder.** |
| **layout_settings.js** | Optional. If present, the layout editor loads it so your module can render custom setting UIs (e.g. checkboxes from an API). See [Custom setting types](#123-custom-setting-types-layout-editor-no-core-changes). |
| **warmer.py** | Optional. If your module fetches data that is cached and you want that cache to stay warm when the server runs **headless** (no browser open), add **`"cache_warmer": True`** to MODULE and a **warmer.py** with **`async def warm(settings, config)`**. See [Cache warmer (optional, headless)](#15-cache-warmer-optional-headless). |

The loader reads `module.py` first, then overlays `inner_html`, `css`, and `js` from the files above. You do **not** put HTML/CSS/JS strings inside `module.py` when using the folder structure.

---

## 3. module.py – define the module

You must define a single dict named **`MODULE`** with at least:

- **`id`** (str) – Unique identifier. Use lowercase letters, numbers, underscores (e.g. `my_timer`). This is the value stored in the layout grid and used to form the CSS class `grid-cell-{id}`.
- **`name`** (str) – Label shown in the UI (e.g. "My Timer").
- **`color`** (str) – Background colour for the cell (e.g. `"#333333"`).

Optional:

- **`settings`** (list) – Array of setting definitions. Each item is a dict with:
  - **`id`** – Key used in the layout/settings API (e.g. `"target_date"`).
  - **`label`** – Label shown in the settings UI.
  - **`type`** – `"text"` or `"select"`.
  - **`default`** – Default value.
  - For **`type: "select"`**: **`options`** – list of `{"value": "...", "label": "..."}`.
- **`gpio`** (dict, optional) – If your module can use Raspberry Pi (or similar) GPIO pins, add **`inputs`** and/or **`outputs`** so users can assign them on the GPIO setup page. See [GPIO support (optional)](#13-gpio-support-optional).
- **`cache_warmer`** (bool, optional) – Set to **`True`** if your module has **warmer.py** and you want the core to call it when the server runs headless so the cache stays warm. See [Cache warmer (optional, headless)](#15-cache-warmer-optional-headless).

Example (no settings):

```python
MODULE = {
    "id": "my_timer",
    "name": "My Timer",
    "color": "#1a1a2e",
}
```

Example (with settings):

```python
MODULE = {
    "id": "my_timer",
    "name": "My Timer",
    "color": "#1a1a2e",
    "settings": [
        {"id": "label", "label": "Label", "type": "text", "default": ""},
        {"id": "mode", "label": "Mode", "type": "select", "options": [
            {"value": "up", "label": "Count up"},
            {"value": "down", "label": "Count down"},
        ], "default": "down"},
    ],
}
```

You can define options lists in the same file (e.g. `ON_OFF_OPTIONS`) and reference them in `settings`. See `glancerf/modules/clock/module.py` or `glancerf/modules/weather/module.py` for real examples.

---

## 4. index.html – cell content

- This file is the **inner HTML** of the cell. The core has already created a `<div class="grid-cell grid-cell-{id}" data-row="..." data-col="...">`; your HTML is inserted **inside** that div.
- Use **only** the structure you need (e.g. a wrapper div and spans). Do not repeat the cell div or add `<html>`/`<body>`.
- Give every element you need to style or script a **class** that starts with your **module id + underscore** (e.g. `my_timer_label`, `my_timer_value`). This avoids clashes with the core and other modules.

Example:

```html
<div class="my_timer_display">
  <span class="my_timer_label"></span>
  <span class="my_timer_value"></span>
</div>
```

Use the same class names in **style.css** and **script.js**.

---

## 5. style.css – module styles

- Your CSS is included **once per page**, but you must **scope** it so it only affects your module's cells.
- The core adds the class **`.grid-cell-{id}`** to each cell (e.g. `.grid-cell-my_timer`). Always scope your rules under this class.
- Use the **same** class names you used in index.html (with the `ModuleName_` prefix).

Example:

```css
.grid-cell-my_timer {
    display: flex;
    align-items: center;
    justify-content: center;
}
.grid-cell-my_timer .my_timer_display {
    display: flex;
    flex-direction: column;
    gap: 0.25em;
}
.grid-cell-my_timer .my_timer_value {
    font-size: 1.5em;
    font-weight: bold;
}
```

If you don't scope under `.grid-cell-{id}`, your styles could affect other cells or the rest of the page.

---

## 6. script.js – behaviour and updates

- Your script is included **once per page** and runs in the main document.
- To find every cell that uses your module, use **`document.querySelectorAll('.grid-cell-{id}')`** (e.g. `.grid-cell-my_timer`). The core has already added this class to the cell div.
- For each cell, use **`cell.querySelector('.my_timer_label')`** (etc.) to get the elements you defined in index.html and update their content or attributes.
- You can use **`cell.getAttribute('data-row')`** and **`cell.getAttribute('data-col')`** to build a per-cell key (e.g. `row + '_' + col`) for settings.

Example (no settings):

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

If your module has **settings**, read them from **`window.GLANCERF_MODULE_SETTINGS`** (see [Settings in JavaScript](#9-settings-in-javascript)).

---

## 7. Naming conventions (important)

| What | Convention | Example |
|------|------------|--------|
| **Folder name** | Same as module `id`; no leading `_` | `my_timer` |
| **Cell wrapper class** | Added by core: **`grid-cell-{id}`** | `.grid-cell-my_timer` |
| **Your classes** | **`{id}_`** + name, underscores only | `.my_timer_display`, `.my_timer_value` |

- The **core** adds `grid-cell` and `grid-cell-{id}` to the cell div. You **use** this in CSS and JS; you don't define it.
- **You** define all other classes used in your HTML/CSS/JS and **prefix** them with your module id + underscore so they don't clash with the core or other modules (e.g. `clock_display`, `weather_temp`, `my_timer_value`).

---

## 8. How the core uses your module

- **Discovery**  
  On startup, the app scans `glancerf/modules/` for folders that do **not** start with `_` and contain **module.py**. For each such folder it loads `MODULE` and, if present, reads **index.html**, **style.css**, and **script.js** into `inner_html`, `css`, and `js`.

- **Rendering the grid**  
  When building the main or read-only page, the core calls `build_grid_html` in `view_utils.py`. For each cell it:
  - Looks up the module by the cell value (module id).
  - Gets `color` and `inner_html` from the module dict.
  - Builds a **safe id** from the module id (alphanumeric and `_`, then ` ` → `-`) and sets the cell's class to **`grid-cell grid-cell-{safe_id}`** (e.g. `grid-cell-my_timer`).
  - Injects your **inner_html** inside that div and sets the cell's background colour.

- **CSS and JS**  
  The app collects the `css` and `js` of every module that appears in the current layout and injects them into the page (once per module). Your CSS/JS use `.grid-cell-{id}` to scope or find your cells.

---

## 9. Settings in JavaScript

If your module has **settings**, the core stores them per cell. In the browser they are in **`window.GLANCERF_MODULE_SETTINGS`**:

- **Key**: `"row_col"` (e.g. `"0_1"` for row 0, column 1).
- **Value**: Object mapping setting **id** to value (e.g. `{ "label": "Launch", "mode": "down" }`).

Example:

```javascript
var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
var r = cell.getAttribute('data-row');
var c = cell.getAttribute('data-col');
var cellKey = (r != null && c != null) ? r + '_' + c : '';
var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
var label = (ms.label || '').toString().trim();
var mode = (ms.mode || 'down').toLowerCase();
```

Use `cellKey` to read the settings for that specific cell.

---

## 10. Global variables (callsign and location)

The core exposes two **global** values from Setup (stored in config as `setup_callsign` and `setup_location`). They are available in JavaScript on the main and read-only dashboard as:

| Variable | Description |
|----------|-------------|
| **`window.GLANCERF_SETUP_CALLSIGN`** | The user's callsign from Setup. Empty string if not set. |
| **`window.GLANCERF_SETUP_LOCATION`** | The user's default location from Setup (e.g. grid square like `RE78hk` or `lat,lng` like `-43.5,172.6`). Empty string if not set. |

Use these as **fallbacks** when your module has a per-cell setting for callsign or location: if the user leaves the cell setting blank, use the global value so they don't have to re-enter it in every cell.

Example (callsign with per-cell override):

```javascript
var call = (ms.callsign || window.GLANCERF_SETUP_CALLSIGN || '').toString().trim();
```

Example (location with per-cell override):

```javascript
var locStr = (ms.location || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
```

The **callsign**, **weather**, and **sun_times** modules use these globals; see `glancerf/modules/callsign/script.js`, `glancerf/modules/weather/script.js`, and `glancerf/modules/sun_times/script.js` for reference.

---

## 11. Custom modules (survive updates)

**Custom modules path:** **`glancerf/modules/_custom/`**

- **Modules inside `_custom/`** – The updater does **not** overwrite or remove the `_custom/` folder. Anything you put here (e.g. `glancerf/modules/_custom/my_timer/`) is preserved when you install a new GlanceRF version.
- **Modules outside `_custom/`** – The rest of `glancerf/modules/` (clock, weather, map, etc.) is part of the built-in app. When you update, that tree can be replaced, so any module you add there **might be overwritten or removed**. Do not rely on it for your own modules.

Put your own modules in **`glancerf/modules/_custom/`** so that:

- They are **not overwritten** when you run an app update.
- If a future GlanceRF release adds a built-in module with the **same id** as yours, your custom version **takes precedence** (custom overrides built-in).

**Setup:**

1. The **`glancerf/modules/_custom/`** folder contains an **`_example`** template (folder name starts with `_` so it is not loaded as a module). Put all your custom module folders inside **`glancerf/modules/_custom/`**. On update, the app merges the modules folder so `_custom/` is preserved.
2. To create a new module: copy **`glancerf/modules/_custom/_example/`**, rename the copy to your module id (e.g. `my_timer`; no leading `_`), then edit `module.py`, `index.html`, `style.css`, and `script.js`. Keep the **`__init__.py`** file in the copy (needed if you add api_routes.py).
3. Restart the app. Custom modules are loaded after built-in ones; any module id that appears in both uses your custom version.

---

## 12. Module API routes (optional)

If your module needs **backend API endpoints** (e.g. to fetch data from a server, proxy an external API, or compute something in Python), you can add an **api_routes.py** file to your module folder. The core discovers any module that has this file and calls **`register_routes(app)`** at startup, so your routes are registered on the same FastAPI app as the rest of GlanceRF.

**Design:** The core handles config, display, and updates. Each module is self-contained: if it needs API endpoints, it registers them itself via **api_routes.py**. Your module should only rely on its own module files for logic; use the core only for config (e.g. `get_config()`), logging (`get_logger()`), and route registration.

### 12.1. Adding api_routes.py

1. **Add \_\_init\_\_.py** to your module folder if it is not already there. The folder must be a Python **package** (have an `__init__.py` file) so the core can import `your_module.api_routes`. Without it, you will see a startup error like "`glancerf.modules.your_module` is not a package" or "Missing dependency `glancerf.modules.your_module.api_routes`". The **example template** (`_custom/_example/`) includes `__init__.py`; keep it when you copy the template to create a new module.
2. Create **api_routes.py** in your module folder (e.g. `glancerf/modules/_custom/my_module/api_routes.py`).
3. Define a function **`register_routes(app: FastAPI) -> None`** that registers your endpoints on `app`.
4. Use **relative imports** for other code in your module (e.g. `from .my_service import fetch_data`). Put any backend logic in other files in the same folder (e.g. `my_service.py`).

Example (minimal):

```python
# glancerf/modules/_custom/my_module/api_routes.py
from fastapi import FastAPI

from glancerf.logging_config import get_logger
from .my_service import get_data

_log = get_logger("my_module.api_routes")


def register_routes(app: FastAPI) -> None:
    @app.get("/api/my_module/data")
    async def get_my_module_data():
        try:
            result = get_data()  # your module-owned logic
            return {"data": result}
        except Exception as e:
            _log.debug("get_data failed: %s", e)
            from fastapi.responses import JSONResponse
            return JSONResponse(
                {"error": "Failed to get data", "detail": str(e)},
                status_code=502,
            )
```

Your **script.js** (or the Modules page) can then call **`fetch("/api/my_module/data")`** to get data. Use paths under **`/api/`** so they are clearly API endpoints.

### 12.2. How the core discovers and registers module API routes

- On startup, after the core registers its own API routes (e.g. `/api/time`, `/api/rss`), it calls **`register_module_api_routes(app)`** (in `glancerf/routes/api.py`).
- That function uses **`get_module_api_packages()`** (in `glancerf/modules/__init__.py`) to get a list of package names for every module folder that contains **api_routes.py** (e.g. `glancerf.modules.satellite_pass`).
- For each package, it imports **`<package>.api_routes`** and, if the module defines a callable **`register_routes`**, calls **`register_routes(app)`**.
- **The module folder must contain \_\_init\_\_.py** so Python treats it as a package; otherwise the import of `<package>.api_routes` fails (e.g. "is not a package").
- If a module is removed or **api_routes.py** is deleted, the core simply skips it; no extra configuration is needed.

### 12.3. Custom setting types (layout editor, no core changes)

The core renders module settings from the **settings** schema in **module.py**. Built-in **types** are **text**, **select**, **number**, and **range**. Any **other** type is treated as **custom**. The core does not implement custom types. Instead, the layout editor renders a placeholder; modules add **layout_settings.js** (loaded from **/module/&lt;module_id&gt;/layout_settings.js**) to fill it. See **satellite_pass/layout_settings.js** for an example. Your script finds placeholders (e.g. `.cell-setting-custom[data-setting-type="your_type"]`), fills `.cell-setting-custom-ui`, and updates the `.cell-setting-custom-value` hidden input on change. Listen for the **`glancerf-cell-settings-updated`** event when new placeholders are added.

### 12.4. Example: satellite_pass module

The **satellite_pass** module in **`glancerf/modules/satellite_pass/`** is a full example of a self-contained module with API routes:

- **satellite_service.py** – Fetches satellite list from CelesTrak, caches it in **satellite_list.json** in the project **cache** folder, refreshes about every 24 hours, and prunes the main config so selected satellites that no longer appear in the list are removed from config.
- **api_routes.py** – Defines **`register_routes(app)`** and registers **GET /api/satellite/list** (serves from cached JSON, refreshing when stale) and **GET /api/satellite/passes** (computes pass data via Skyfield).
- **module.py** – Includes a setting of type **satellite_checkboxes** (a custom type; the core does not implement it).
- **layout_settings.js** – Loaded on the layout editor page; finds **satellite_checkboxes** placeholders, fetches **/api/satellite/list**, and renders the checkbox list; updates the hidden input on change so Save stores the selection.

You can use this module as a reference for structure and for how to combine **api_routes.py** with a service layer and config.

### 12.5. Satellite_pass API methods (reference)

If your module or the Modules page needs to call the satellite_pass API, use these endpoints. They are registered by the **satellite_pass** module when it has **api_routes.py** and are served under the same FastAPI app as the rest of GlanceRF.

**GET /api/satellite/list**

- **Purpose:** Return the list of trackable satellites (from cached JSON, refreshed from CelesTrak when missing or older than ~24 hours).
- **Query parameters:** None.
- **Response (200):** JSON object:
  - **`satellites`** – array of objects, each with **`norad_id`** (int) and **`name`** (str), sorted by name.
- **Errors:** **502** – body `{ "error": "...", "detail": "..." }` if the list could not be loaded or refreshed.

**GET /api/satellite/passes**

- **Purpose:** Compute current position and next pass for each requested satellite at the given observer location.
- **Query parameters (all required except `alt`):**
  - **`norad_ids`** (str) – Comma-separated NORAD IDs (e.g. `25544,48274`).
  - **`lat`** (float) – Observer latitude in degrees (-90 to 90).
  - **`lng`** (float) – Observer longitude in degrees (-180 to 180).
  - **`alt`** (float, optional) – Observer altitude in metres (0 to 10000). Default **0**.
- **Response (200):** JSON object:
  - **`passes`** – array of objects, one per satellite (only satellites that could be computed are included). Each object has:
    - **`norad_id`** (int), **`name`** (str)
    - **`current`** – `{ "az": float, "el": float, "up": bool }` (azimuth and elevation in degrees; `up` is true if the satellite is above the horizon)
    - **`next_pass`** – `null` or `{ "rise_utc": str, "set_utc": str, "rise_az": float|null, "set_az": float|null, "max_el": float|null, "duration_sec": int }` (ISO UTC times; azimuths in degrees; max elevation in degrees; duration in seconds)
- **Errors:**
  - **400** – `norad_ids` missing, not comma-separated integers, empty, or more than 20 IDs; body `{ "error": "..." }`.
  - **502** – body `{ "error": "...", "detail": "..." }` if pass computation failed.

Example request: `GET /api/satellite/passes?norad_ids=25544,48274&lat=-43.5&lng=172.6&alt=0`

### 12.6. Using the universal cache

When your module's API routes call **external services** or do **heavy computation**, use the shared **TTL cache** so multiple requests (or screens) get the same result without hitting the backend every time.

**Import and get the cache:**

```python
from glancerf.utils.cache import get_cache

cache = get_cache()
```

**Key naming:** Use a **prefix per module** to avoid collisions, e.g. `contests:list:...`, `dxpeditions:list:...`, `satellite:passes:...`, `rss:...`. Include enough of the request (sources, URL hash, lat/lng, etc.) in the key so different parameters get different cache entries.

**When to cache:** External HTTP fetches (RSS, contest lists, propagation data), computed results that depend on stable inputs (satellite passes for a given location, sun up/down for lat/lng). Choose a **TTL** that balances freshness and load (e.g. 45–90 seconds for passes, 5–15 minutes for contest/RSS lists).

**Pattern 1 – get then set:** Check the cache first; on miss, compute or fetch, then store and return.

```python
cache_key = "my_module:data:" + (param or "default")
cached = cache.get(cache_key)
if cached is not None:
    return cached
result = await fetch_or_compute(...)
cache.set(cache_key, result, ttl_seconds=900)
return result
```

**Pattern 2 – get_or_set:** Let the cache call your factory on miss. Best when the value is computed synchronously (e.g. in a thread). For async routes you can still use **get** / **set** as above.

```python
def compute():
    return expensive_operation()

result = cache.get_or_set(
    "my_module:item:" + key,
    ttl_seconds=300,
    factory=compute,
)
return {"data": result}
```

**Examples in the codebase:** **contests** and **dxpeditions** cache list responses by source set (TTL 15 min). **satellite_pass** caches passes by `norad_ids|lat|lng|alt` (45 s) and tracks by `norad_ids|minutes` (90 s). **rss** caches by feed URL hash (10 min). **map** caches propagation and APRS data by source/hours (5 min). **sun_times** caches status by lat|lng (1 min).

---

## 13. GPIO support (optional)

On systems with GPIO (e.g. Raspberry Pi with **RPi.GPIO**), GlanceRF can assign module inputs and outputs to physical pins. Users configure this on the **GPIO** setup page (Menu → GPIO when GPIO is available). Your module only declares what it supports; the core discovers it and shows your functions in the Pin → Module → Function table.

### 13.1. Declaring GPIO in module.py

Add a **`gpio`** key to **MODULE** with **`inputs`** and/or **`outputs`**. Each item is a dict with **`id`** (used in code) and **`name`** (shown in the GPIO setup dropdown). Pin direction (input or output) is determined by the function the user picks, so you list each function once under either inputs or outputs.

Example:

```python
MODULE = {
    "id": "my_rig",
    "name": "My Rig",
    "color": "#1a1a2e",
    "gpio": {
        "inputs": [
            {"id": "ptt_trigger", "name": "PTT trigger"},
        ],
        "outputs": [
            {"id": "led", "name": "Status LED"},
        ],
    },
}
```

After the user assigns a pin to your module and function on the GPIO setup page, the core configures the pin and either calls your input handler or lets you drive the output.

### 13.2. Handling GPIO inputs

When a pin assigned to one of your **inputs** changes state, the core looks for a dict named **`GPIO_INPUT_HANDLERS`** in your **module.py**. Keys are your input **function_id**; values are callables that take a single argument **`value`** (bool: pin state).

Define **`GPIO_INPUT_HANDLERS`** in the same **module.py** as **MODULE**:

```python
def _on_ptt_trigger(value: bool):
    # value is True (high) or False (low)
    if value:
        # start transmitting, etc.
        pass
    else:
        # stop transmitting, etc.
        pass

GPIO_INPUT_HANDLERS = {
    "ptt_trigger": _on_ptt_trigger,
}
```

The core loads your module and calls the handler when the physical pin changes. Handlers run in the main process; keep them short (e.g. set a flag or queue work).

### 13.3. Driving GPIO outputs

For **outputs**, your module turns the pin on or off by calling the core’s **`set_output`** function. Import it from **glancerf.gpio_manager** and call it with your module id, function id, and a boolean:

```python
from glancerf.gpio_manager import set_output

# Turn the assigned "led" pin on
set_output("my_rig", "led", True)

# Turn it off
set_output("my_rig", "led", False)
```

Only the pin that the user assigned to this module and function on the GPIO setup page is updated. If no pin is assigned or GPIO is not available, **set_output** does nothing (no error). You can call it from **api_routes.py**, a background task, or any code that runs after the app has started.

### 13.4. When GPIO is available

- The **GPIO** menu item and the **GPIO** setup page appear only when the system has GPIO support (e.g. RPi.GPIO on a Raspberry Pi).
- On other systems, the menu and setup show no GPIO option, and **set_output** and input handlers are never used.
- Assignments are stored in config as **gpio_assignments** and applied at startup; changing assignments on the GPIO page restarts the GPIO manager with the new mapping.

---

## 14. Checklist

- [ ] Copied **`glancerf/modules/_custom/_example/`** and renamed the folder to your module id (no leading `_`). The template includes **\_\_init\_\_.py**; keep it so the folder is a Python package (required if you add api_routes.py).
- [ ] **module.py**: Set `id`, `name`, `color`; add `settings` if needed.
- [ ] **index.html**: Inner content only; all classes use **`{id}_`** prefix (e.g. `my_timer_label`).
- [ ] **style.css**: All rules scoped under **`.grid-cell-{id}`**; same class names as in HTML.
- [ ] **script.js**: Find cells with **`querySelectorAll('.grid-cell-{id}')`**; query inside cells with your class names; read per-cell settings from **`window.GLANCERF_MODULE_SETTINGS[cellKey]`** if you have settings; use **`window.GLANCERF_SETUP_CALLSIGN`** or **`window.GLANCERF_SETUP_LOCATION`** as fallbacks if your module uses callsign/location.
- [ ] Restart the app (or reload the page) and pick your module in the layout editor.
- [ ] Put your module in **`glancerf/modules/_custom/`** so it survives updates (see [Custom modules (survive updates)](#11-custom-modules-survive-updates)).
- [ ] If your module needs API endpoints: ensure the module folder has **\_\_init\_\_.py** (the template includes it), then add **api_routes.py** with **`register_routes(app)`** and keep backend logic in the module folder (see [Module API routes (optional)](#12-module-api-routes-optional)). For external APIs or heavy work, use the [universal cache](#126-using-the-universal-cache) so multiple requests share the same result.
- [ ] If your module uses GPIO: add **`gpio`** with **`inputs`** and/or **`outputs`** to **MODULE**; define **`GPIO_INPUT_HANDLERS`** in **module.py** for inputs; use **`set_output(module_id, function_id, value)`** from **glancerf.gpio_manager** for outputs (see [GPIO support (optional)](#13-gpio-support-optional)).
- [ ] If your module fetches data that is cached and you want the cache to stay warm when the server runs headless: add **`"cache_warmer": True`** to **MODULE** and **warmer.py** with **`async def warm(settings, config)`** that fills the same cache your API uses (see [Cache warmer (optional, headless)](#15-cache-warmer-optional-headless)).

For a minimal, commented reference, see the **`_example`** template in `glancerf/modules/_custom/_example/` (includes `__init__.py`). For a module with API routes and cached data, see **`satellite_pass`** in `glancerf/modules/satellite_pass/`.

---

## 15. Cache warmer (optional, headless)

When the server runs **headless** (e.g. as a Windows service or with no browser/desktop connected), the core runs a **cache warmer** in the background. It periodically calls each **active** module’s warmer (if the module has one) so that when a client later connects, the cache is already filled. This avoids cold caches and slow first loads.

**You do not need to change any core code to add a new cache-warmed module.** The core discovers warmers by convention.

### 15.1. Opting in

1. In **module.py**, add **`"cache_warmer": True`** to the **MODULE** dict.
2. In the same folder, add **warmer.py** with a single async function:

   **`async def warm(settings: dict, config: Any) -> None`**

   - **`settings`** – The **cell** settings for one grid cell that uses this module (same keys as in your module’s `settings` schema, e.g. `rss_url`, `enabled_sources`). The core calls `warm` once per cell that uses your module; you may be called multiple times for different cells or the same logical config.
   - **`config`** – The global config object (e.g. from `get_config()`). Use it for global values like `setup_location` or `setup_callsign` if your cell settings are empty.

Your **`warm`** function should:

- **Return early** if the cell is not configured (e.g. empty URL, missing location). No need to raise; just `return`.
- **Do the same work the API would do**: call your service layer (or fetch), then write the result into the shared cache with the **same cache key and TTL** your API route uses. That way, when a browser later hits your API, the response is served from cache.
- **Catch exceptions** if you prefer (e.g. log and return); the core catches and logs any exception from `warm` so one failing module does not stop others.

### 15.2. When the warmer runs

- The warmer runs only when **no browser and no desktop** is connected. If someone has the dashboard open, their requests fill the cache as usual and the background warmer does not run.
- It runs on an interval (e.g. every 5 minutes) after a short startup delay. Only modules that are **active** (appear in the current layout) and have **`cache_warmer: True`** and a **warmer.py** are invoked.

### 15.3. Example

Your module has an API that fetches by URL and caches by `"rss:" + hash(url)`. In **warmer.py**:

```python
# warmer.py
import hashlib
from typing import Any

from glancerf.utils.cache import get_cache


async def warm(settings: dict, config: Any) -> None:
    url = (settings.get("rss_url") or "").strip()
    if not url:
        return
    try:
        from .api_routes import fetch_rss_feed, _RSS_CACHE_TTL
        out = await fetch_rss_feed(url)
        if out is not None:
            cache_key = "rss:" + hashlib.sha256(url.encode()).hexdigest()
            get_cache().set(cache_key, out, _RSS_CACHE_TTL)
    except Exception:
        pass
```

In **module.py**, add **`"cache_warmer": True`** to **MODULE**. The core will discover **warmer.py** and call **`warm`** for each cell that uses this module when the server is headless.

### 15.4. Built-in modules with warmers

The **contests**, **dxpeditions**, **rss**, **sun_times**, **map**, **satellite_pass**, and **live_spots** modules each define **`cache_warmer: True`** and a **warmer.py**. You can copy their pattern (e.g. `glancerf/modules/rss/warmer.py`, `glancerf/modules/contests/warmer.py`). For location parsing (grid square or `lat,lng`), use **`glancerf.utils.location.parse_location(s)`** which returns `(lat, lng)` or `None`.
