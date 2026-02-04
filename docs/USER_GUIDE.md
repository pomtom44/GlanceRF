# GlanceRF – User Guide

This guide explains how to use GlanceRF: first run, setup, the menu (press M), the layout editor, and module options (including the map and clock).

---

## First run and setup

**Option A: Use the installer (recommended)**

- **Windows:** Double-click `installers\install-windows.bat` (or run it from the Project folder). It will check Python, install requirements, and ask about startup and desktop/headless mode.
- **Linux:** From the Project folder run `chmod +x installers/install-linux.sh` then `./installers/install-linux.sh`. It detects your distro and installs Python/requirements, then asks about startup and desktop/headless.
- **macOS:** From the Project folder run `chmod +x installers/install-mac.sh` then `./installers/install-mac.sh`.

**Option B: Manual setup**

1. **Download the project and save where you want it to run**

   If you know how to download from Git, feel free to do that how you normally would.
   Otherwise click on "Code" and "Download ZIP".
   Then extract to where you want it to go.

2. **Install dependencies** (see main README):

   First, make sure Python is installed, follow a guide on this for your OS if you don't know how.
   Then install the dependencies.

   Open a terminal and navigate to your installed location (the **Project** folder that contains `run.py`).
   Then type:
   ```bash
   pip install -r requirements.txt
   ```

   **For headless/server-only installations (no GUI):**
   ```bash
   pip install -r requirements_headless.txt
   ```

   Note: The application automatically handles missing GUI libraries if desktop mode is disabled in configuration.

3. **Basic configuration**

   Most of the setup will be done via the GUI. The config file is **`glancerf_config.json`** in the same folder as `run.py` (the Project folder). If you want to run headless, edit it to set `"use_desktop": false`.

4. **Start the application**

   In the same terminal window, from the Project folder run:
   ```bash
   python run.py
   ```
   If running desktop, a popup should appear where you can configure everything.
   If running headless, open a browser on another PC and connect to the IP:port to start the setup.

### Setup page (first run or via menu)

On the Setup page you can:

1. **Page 1 – Layout:** Screen aspect ratio and orientation (matches your display), grid size (columns and rows, 1–8 each). Click **Continue** to save and go to the Layout page.
2. **Page 2 – Station & updates:** Callsign and SSID (used as default by modules and for APRS cache), location (grid square or lat,lng for modules that need it), update mode (none / notify / auto), update check time, and telemetry (on/off).
3. **Page 3 – Tips & shortcuts:** Quick reference for keyboard shortcuts and tips.

You can open Setup again anytime by pressing **M** to open the menu, then choosing Setup.

Once that is done, you will be taken to **Layout** where you can:

1. **Pick modules** – Pick which modules you want to go where.
2. **Configure modules** – On the **Modules** page (menu > Modules), expand a module to edit its settings and click Save for that module.
3. **Resize modules** – Each module can be resized to take up other module spaces.

You can open the Layout Editor again anytime by pressing **M** to open the menu, then choosing Layout editor.

---

## Menu (keyboard shortcut)

Press **M** on the main dashboard (or on Setup, Layout, or Modules pages) to open the **menu**. The menu lets you go to:

- **Setup** – First-run setup, aspect ratio, grid, station & updates, telemetry
- **Layout editor** – Add or rearrange cells, resize modules
- **Modules** – View all modules and their status; expand a module to edit its settings and use Save
- **Updates** – Open the Updates page to see current and latest version, release notes, and trigger an update

The shortcut is ignored when the cursor is in a text field.

---

## Configuration file

- **Location** – `glancerf_config.json` in the same directory as `run.py` (typically the Project folder).

Most of the settings in here you shouldn't need to touch. If you create your own modules, put them in **`glancerf/modules/_custom/`** so they survive app updates; see [CREATING_A_MODULE.md](CREATING_A_MODULE.md). Everything that is configured is stored in here, so you can back this up and replace with any changes to go back to a previous version.

---

## Telemetry and Privacy

GlanceRF includes optional telemetry to help improve the application. For detailed information about what data is collected, what isn't, and how to control it, see **[TELEMETRY.md](TELEMETRY.md)**.

**Quick summary:**
- Telemetry is **enabled by default** (opt-out)
- Only **anonymous** data is collected (version, OS info, module lists)
- **No personal information** is collected (no callsigns, locations, etc.)
- You can **disable it anytime** in Setup → Page 2 → Telemetry
- The application works identically with or without telemetry

The values you may want to change are:

| Key | Purpose |
|-----|--------|
| **port** | Main app port (e.g. 8080). |
| **readonly_port** | Read-only mirror port (e.g. 8081). |
| **use_desktop** | `true` = open desktop window; `false` = server only. |

---

## Desktop, browser, and read-only view

- **Desktop mode** (`use_desktop: true`) – Starts the main server (e.g. on port 8080) and opens a local window showing the dashboard. Ideal for a dedicated screen.
- **Server-only** (`use_desktop: false`) – Only the web server runs; open the main URL (e.g. `http://localhost:8080`) in a browser.
- **Read-only view** – A separate server (e.g. port 8081) serves a non-interactive copy of the current layout. Use this for extra displays or kiosks that should only show the dashboard, not setup or layout. Open e.g. `http://localhost:8081`.

---

## Logging and errors

Logging always goes to **the console (stderr)**. You can optionally add a **log file** and choose how much is logged by editing `glancerf_config.json`.

### Log levels

Add a **`log_level`** key to your config (or leave it out for default behaviour):

| Level | What you see |
|-------|----------------|
| **default** | **INFO:** Startup and shutdown messages. **ERROR:** Error messages. |
| **detailed** | Same as default, plus **DETAILED:** Web requests, telemetry heartbeat, update checks, and similar one-line events. |
| **verbose** | Same as default and detailed (INFO, ERROR, DETAILED), plus **DEBUG:** Per-request details (method, path, status, duration) and other debug output. |

If `log_level` is missing, the app uses **default** (startup, shutdown, and errors).

### File logging

To also write logs to a file, add **`log_path`** to `glancerf_config.json` with a full or relative path. The app will create the file and its parent folders if needed. Example:

```json
{
  "port": 8080,
  "readonly_port": 8081,
  "use_desktop": true,
  "log_level": "detailed",
  "log_path": "C:/GlanceRF/logs/glancerf.log"
}
```

- **Console** – Always used; level is controlled by `log_level`.
- **File** – Only used when `log_path` is set; the same level applies. Omit `log_path` to have console-only logging.
