# GlanceRF (A Hamclock Modern Rebuild)

## What is GlanceRF

GlanceRF is a modern rebuild of the Original HamClock by Elwood WB0OEW.

During development of this project, early in Beta, Elwood passed away. Originally this was a side project, and I was going to tell people: <br>
*"If you want a mature project with support, go use hamclock."*

Thoughts go to Elwood, and I thank him for the original project which so many use and which inspired this rebuild.

**Disclaimer:** This is a personal project. I built it for my needs but also designed it for ease of use for others. Once it's working how I want, support will be limited. However, requests, bugs, etc.—I will do my best to sort them out.

---

## Quick start

1. **Download** the project and open a terminal in the project folder.
2. **Install Python** (3.8 or higher) if needed.
3. **Install dependencies:**
   - With desktop GUI:  
     `pip install -r requirements.txt`
   - Headless (server only, no GUI):  
     `pip install -r requirements_headless.txt`
4. **Optional (headless):** Edit `glancerf_config.json` in this folder to set `"use_desktop": false`.
5. **Run:**  
   `python run.py`  
   Then follow the setup (in the app window, or in a browser if headless).

Configuration is stored in **`glancerf_config.json`** in the same folder as `run.py`.

---

## Screenshots

**Setup**

![Setup](screenshots/Setup.png)

**Sample dashboard**

![Sample Dash](screenshots/Sample%20Dash.png)

**Layout editor**

![Layout Editor](screenshots/Layout%20Editor.png)

**Layout with expanded cell**

![Layout Expanded](screenshots/Layout%20Expanded.png)

---

## Documentation

| Guide | Description |
|-------|-------------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | First run, setup, keyboard shortcuts (S = Setup, L = Layout), layout editor, map and clock options. |
| [MODULES.md](docs/MODULES.md) | Module system and available modules. |
| [CREATING_A_MODULE.md](docs/CREATING_A_MODULE.md) | How to create a cell module: folder structure, `module.py`, `index.html`, `style.css`, `script.js`. |
| [TELEMETRY.md](docs/TELEMETRY.md) | Telemetry and privacy: what is collected, what isn't, how to control it. |

---

## Requirements

- **Python** 3.8 or higher
- Dependencies in `requirements.txt` (full) or `requirements_headless.txt` (server only)

**Installation options:**

- **Full (with desktop GUI):** `pip install -r requirements.txt`  
  Includes PyQt5 and PyQtWebEngine for the desktop window.
- **Headless (server only):** `pip install -r requirements_headless.txt`  
  No GUI; access via web browser. Set `"use_desktop": false` in `glancerf_config.json`.

The app skips GUI imports if desktop mode is disabled in config.

---

## Features

- **Modes:** Desktop app, server-only (web), and read-only for public displays
- **Layout:** Any grid size, any monitor; choose which modules go where and resize cells
- **Built-in modules:** Clock (local, UTC, international), map (various base images), weather, countdown, and more

---

## Feature requests & Bugs

See **[docs/FEATURE_REQUESTS.md](docs/FEATURE_REQUESTS.md)** for the list.  <br>
To request a feature or raise a bug, open an Issue using the Github issues. <br>
If you don't have a github account, and still want to raise a bug, email me GlanceRF@zl4st.com <br>


---

**Disclaimer:** This project was heavily assisted with AI. The concepts and code review are mine, and I still do manual fixes and bug reviews. If you don't like that, each to their own—I'd appreciate you keeping it to yourself.
