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
12. [Checklist](#12-checklist)

---

## 1. Quick start

1. Copy the **`example`** folder from **`glancerf/modules/_custom/example/`**. Keep your copy inside **`glancerf/modules/_custom/`** (e.g. `glancerf/modules/_custom/my_timer/`) so it is not overwritten when you update GlanceRF.
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

1. The **`glancerf/modules/_custom/`** folder contains an **`example`** module as a template. Put all your custom module folders inside **`glancerf/modules/_custom/`**. On update, the app merges the modules folder so `_custom/` is preserved.
2. To create a new module: copy **`glancerf/modules/_custom/example/`**, rename the copy to your module id (e.g. `my_timer`), then edit `module.py`, `index.html`, `style.css`, and `script.js`. Folder names must not start with `_`.
3. Restart the app. Custom modules are loaded after built-in ones; any module id that appears in both uses your custom version.

---

## 12. Checklist

- [ ] Copied **`glancerf/modules/_custom/example/`** and renamed the folder to your module id (no leading `_`).
- [ ] **module.py**: Set `id`, `name`, `color`; add `settings` if needed.
- [ ] **index.html**: Inner content only; all classes use **`{id}_`** prefix (e.g. `my_timer_label`).
- [ ] **style.css**: All rules scoped under **`.grid-cell-{id}`**; same class names as in HTML.
- [ ] **script.js**: Find cells with **`querySelectorAll('.grid-cell-{id}')`**; query inside cells with your class names; read per-cell settings from **`window.GLANCERF_MODULE_SETTINGS[cellKey]`** if you have settings; use **`window.GLANCERF_SETUP_CALLSIGN`** or **`window.GLANCERF_SETUP_LOCATION`** as fallbacks if your module uses callsign/location.
- [ ] Restart the app (or reload the page) and pick your module in the layout editor.
- [ ] Put your module in **`glancerf/modules/_custom/`** so it survives updates (see [Custom modules (survive updates)](#11-custom-modules-survive-updates)).

For a minimal, commented reference, see the **`example`** module in `glancerf/modules/_custom/example/`.
