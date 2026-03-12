# GlanceRF – User Guide

This guide explains how to use GlanceRF: first run, setup, the menu, the layout editor, and key features.

---

## First run and setup

**Option A: Install (choose one of three methods)**

1. **Core installer** — Download from [glancerf.zl4st.com/installers/](https://glancerf.zl4st.com/installers/) (GlanceRF-Install-Windows.exe, GlanceRF-install-Linux.sh, or GlanceRF-install-Mac.sh) and run it.
2. **GitHub + installer** — Download the [GitHub ZIP](https://github.com/pomtom44/GlanceRF/archive/refs/heads/main.zip), extract, then run the installer from `Project/installers`:
   - **Windows:** Double-click `installers\install-windows.bat`
   - **Linux:** `chmod +x installers/install-linux.sh` then `./installers/install-linux.sh`
   - **macOS:** `chmod +x installers/install-mac.sh` then `./installers/install-mac.sh`
3. **Manual** — Download from GitHub, then `pip install -r requirements/requirements-headless.txt` and `python run.py` from the Project folder.

**Option B: Manual setup (if you already have the project)**

1. Download the project and extract to where you want it to run.
2. Install dependencies: from the Project folder (containing `run.py`):
   ```bash
   pip install -r requirements.txt
   ```
3. Start the application:
   ```bash
   python run.py
   ```
   If running with a desktop window, a popup appears. If headless, open a browser and connect to the IP:port to run setup.

### Setup page (first run or via menu)

On the Setup page you can:

1. **Page 1 – Layout:** Screen aspect ratio and orientation, grid size (columns and rows). Click **Next** to continue.

   ![Setup – Layout](screenshots/Setup%20Page%201.png)

2. **Page 2 – Station & updates:** Callsign and SSID (used by modules and for APRS cache), default location (grid square or lat,lng), APRS cache size and age, update mode (none / notify / auto), update check time, and telemetry (on/off).

   ![Setup – Station & updates](screenshots/Setup%20Page%202.png)

3. **Page 3 – Tips & shortcuts:** Quick reference for keyboard shortcuts and tips.

You can open Setup anytime by pressing **M** to open the menu, then choosing **Setup**.

After setup you are taken to **Layout** where you can:

1. **Pick modules** – Choose which modules go in each cell.
2. **Configure modules** – On the **Modules** page (menu → Modules), expand a module to edit its settings and click Save.
3. **Resize modules** – Use the layout editor to merge cells and resize modules.
4. **Map only modules** – Add modules that feed the map overlay without taking a grid cell (menu → Map only modules or `/map-modules`).

![Layout editor](screenshots/Editor%20Layout.png)

---

## Menu (keyboard shortcut)

Press **M** on the main dashboard (or on Setup, Layout, or Modules pages) to open the **menu**. The menu lets you go to:

- **Setup** – First-run setup, aspect ratio, grid, station & updates, telemetry
- **Layout editor** – Add or rearrange cells, resize modules
- **Modules** – View all modules; expand to edit settings and Save
- **Map only modules** – Add modules that feed the map overlay (e.g. APRS, satellites)
- **Updates** – Current and latest version, release notes, trigger an update
- **GPIO** – Configure GPIO pins (Raspberry Pi; only when GPIO is available)

The shortcut is ignored when the cursor is in a text field.

---

## Configuration file

- **Location:** `glancerf_config.json` in the Project directory (or the path in `GLANCERF_PROJECT`).
- Most settings are configured via the UI. For custom modules, put them in **`glancerf/modules/_custom/`** so they survive updates; see [CREATING_A_MODULE.md](CREATING_A_MODULE.md).
- Back up this file to restore a previous configuration.

---

## Telemetry and Privacy

GlanceRF includes optional telemetry to help improve the application. For details, see **[TELEMETRY.md](TELEMETRY.md)**.

**Quick summary:**
- Telemetry is **enabled by default** (opt-out)
- Only **anonymous** data is collected (version, OS info, module lists)
- **No personal information** is collected (no callsigns, locations, etc.)
- You can **disable it anytime** in Setup → Page 2 → Telemetry
- The application works identically with or without telemetry

---

## Desktop, browser, terminal, and headless mode

| Mode | Config | Behaviour |
|------|--------|-----------|
| **Desktop** | `desktop_mode: "desktop"` | Opens a local window showing the dashboard. Ideal for a dedicated screen. |
| **Browser** | `desktop_mode: "browser"` | Starts the server and opens the default browser. |
| **Terminal** | `desktop_mode: "terminal"` | Server runs in terminal; no automatic browser. |
| **Headless** | `desktop_mode: "headless"` | Server only; connect via browser from another device. |
| **None** | `desktop_mode: "none"` | Server only; no automatic browser or window. |

- **Read-only view:** A separate server (e.g. port 8081) serves a non-interactive copy of the layout. Use for extra displays or kiosks. Open e.g. `http://localhost:8081`.

---

## Logging and errors

Logging goes to **the console (stderr)**. You can add a **log file** and set the log level in `glancerf_config.json`.

### Log levels

| Level | What you see |
|-------|--------------|
| **default** | Startup, shutdown, errors |
| **detailed** | Default plus web requests, telemetry, update checks |
| **verbose** | Detailed plus per-request debug output |
| **debug** | Same as verbose (alias) |

### File logging

Add **`log_path`** to `glancerf_config.json` with a full or relative path. The app creates the file and parent folders if needed:

```json
{
  "port": 8080,
  "readonly_port": 8081,
  "desktop_mode": "browser",
  "log_level": "detailed",
  "log_path": "C:/GlanceRF/logs/glancerf.log"
}
```

---

## APRS

When you set a **callsign** in Setup, GlanceRF connects to APRS-IS and caches packets locally. The **APRS** module shows a last-heard list, and the **Map** can show APRS stations as dots or icons when the APRS module is in the layout or in Map only modules.

- APRS passcode is auto-computed from your callsign.
- Cache size and max age are configurable in Setup.
- See [DEBUGGING.md](DEBUGGING.md) for APRS troubleshooting.
