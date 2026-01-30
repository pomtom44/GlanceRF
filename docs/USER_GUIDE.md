# GlanceRF – User Guide

This guide explains how to use GlanceRF: first run, setup, keyboard shortcuts, the layout editor, and module options (including the map and clock).

---

## First run and setup


1. **Download the project and save where you want it to run**

  If you know how to download from Git, feel free to do that how you normally would.
  Otherwise click on "Code" and "Download ZIP".
  Then extract to where you want it to go.

2. **Install dependencies** (see main README):

  First, make sure Python is installed, follow a guide on this for your OS if you don't know how.
  Then install the dependencies.

  Open a terminal and navigate to your installed location
  Then type
  ```pip install -r requirements.txt```
  
  **For headless/server-only installations (no GUI):**
  ```pip install -r requirements_headless.txt```
  
  Note: The application automatically handles missing GUI libraries if desktop mode is disabled in configuration.
  This will install the required modules

3. **Basic Configuration**
  Most of the setup will be done via the GUI. The config file is **`glancerf_config.json`** in the same folder as `run.py` (the Project folder). If you want to run headless, edit it to disable desktop mode.

4. **Start the application**:

  In the same terminal window, run
  ```python run.py```
  If running desktop, a popup should appear where you can configure everything.
  If running headless, open a browser on another PC and connect to the IP:Port to start the setup.

### Setup page (first run or via S key)

On the Setup page you can:

1. **Screen aspect ratio and orientation** – Choose the layout that matches your display (This is just as a rough guide for first setup).
2. **Grid size** – Use the sliders to set the number of **columns** (1–8) and **rows** (1–8). The preview shows the resulting grid.
3. **Continue** – Click to save and continue. You will be sent to the **Layout** page to choose what appears in each cell.

You can open Setup again anytime with the **S** keyboard shortcut.

Once that is done, you will be taken to **Layout** where you can:

1. **Pick Modules** - Pick which modules you want to go where.
2. **Configure Modules** - Each module has its own configuration you can edit.
3. **Resize Modules** - Each module can be resized to take up other module spaces.

You can open the Layout Editor again anytime with the **L** keyboard shortcut.

---

## Keyboard shortcuts

These work on the **main dashboard** (not when the cursor is in a text field):

| Key | Action |
|-----|--------|
| **S** | Open **Setup** |
| **L** | Open **Layout editor** |
| **M** | Open **Modules** page |
| **C** | Open **Config** page |

Shortcuts are ignored when typing in an input, so you can use these shortcuts after closing any dialogs or leaving input fields.

---

## Configuration file

- **Location** – `glancerf_config.json` in the same directory as `run.py` (typically the Project folder).

Most of the settings in here you shouldn't need to touch.
However, everything that is configured is stored in here, so you can back this up and replace with any changes to go back to a previous version.

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

- **Desktop mode** (`use_desktop: true`) – Starts the main server (e.g. on port 8080) and opens a local window showing the clock. Ideal for a dedicated screen.
- **Server-only** (`use_desktop: false`) – Only the web server runs; open the main URL (e.g. `http://localhost:8080`) in a browser.
- **Read-only view** – A separate server (e.g. port 8081) serves a non-interactive copy of the current layout. Use this for extra displays or kiosks that should only show the dashboard, not setup or layout. Open e.g. `http://localhost:8081`.

---

## Logging and errors

Error and exception logging goes to **standard error (stderr)**. If you start the app from a terminal (e.g. `python run.py`), that is the **same console window** where you see the startup messages ("Read-only server started...", "Starting GlanceRF server...", etc.). Any asyncio or application errors will appear there.

- **Running from a terminal** – Watch that window for errors.
- **Running in the background or from a shortcut** – To capture errors to a file, redirect stderr when starting the app:
  - Windows (Command Prompt): `python run.py 2> glancerf_errors.log`
  - Windows (PowerShell): `python run.py 2>&1 | Tee-Object -FilePath glancerf_errors.log`
  - Linux/macOS: `python run.py 2> glancerf_errors.log`

The app does not write a log file by default. Config save errors are printed with `print()` and also go to the same console.

---