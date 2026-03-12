# GlanceRF V2 Documentation

GlanceRF is a modular RF/amateur radio dashboard that displays a configurable grid of cells (clock, satellite passes, spots, etc.) in a web interface.

---

## **I don't know GitHub. What do I do?**

**[→ Quick & Easy: Download and run the installer](https://glancerf.zl4st.com/quick.html)** — No GitHub needed. Just download for Windows, or run one command for Linux/Mac. Follow the prompts. Done.

---

## Screenshots

| Main dashboard | Setup | Layout editor |
|---------------|-------|---------------|
| ![Main dashboard](screenshots/Main%20Dashboard.png) | ![Setup](screenshots/Setup%20Page%201.png) | ![Layout editor](screenshots/Editor%20Layout.png) |

See the [website](https://glancerf.zl4st.com) for more screenshots.

## Installation (3 methods)

| Method | Description |
|--------|--------------|
| **1. Core installer** | Download from [glancerf.zl4st.com/installers/](https://glancerf.zl4st.com/installers/) — GlanceRF-install-Windows.exe, GlanceRF-install-Linux.sh, or GlanceRF-install-Mac.sh. Runs the full installer. |
| **2. GitHub + installer** | Download the [GitHub ZIP](https://github.com/pomtom44/GlanceRF/archive/refs/heads/main.zip), extract, then run the installer from `Project/installers`. |
| **3. Manual** | Download from GitHub, then `pip install -r requirements/requirements-headless.txt` and `python run.py` from the Project folder. |

See [Installation](INSTALLATION.md) for details.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Installation](INSTALLATION.md) | Installers for Windows, Linux, macOS; Docker |
| [Configuration](CONFIGURATION.md) | Config file, environment variables |
| [User Guide](USER_GUIDE.md) | First run, setup, menu, layout, features |
| [Startup Guide](STARTUP_GUIDE.md) | Run GlanceRF at logon (Windows, Linux, macOS, Pi) |
| [Creating a Module](CREATING_A_MODULE.md) | How to add a custom cell module |
| [Modules](MODULES.md) | Module structure, map overlays, API routes |
| [Architecture](ARCHITECTURE.md) | Project structure, routes, services |
| [Debugging](DEBUGGING.md) | Log levels, APRS debug, troubleshooting |
| [Telemetry](TELEMETRY.md) | What data is collected, opt-out |
| [Third-Party & Services](THIRD_PARTY_AND_SERVICES.md) | External dependencies and APIs |
| [Feature Requests](FEATURE_REQUESTS.md) | Requested features and status |

## Run Modes

| Mode | Description |
|------|-------------|
| **Desktop** | Native PyQt5 window with embedded browser. Console hidden on Windows. |
| **Browser** | Terminal + browser. Server runs in terminal; opens default browser. |
| **Terminal** | Terminal only. Server runs in terminal; no automatic browser. |
| **Headless** | Server only. No window. Use as Windows service, systemd, or launchd. Tray icon (headless only) for quick access. |

Set via `desktop_mode` in config or installers.

## Web Interface

- **Main** (`/`) – Dashboard grid. Right-click or press M for menu. Modules resize to fit; no scrollbars.
- **Setup** (`/setup`) – First-run: grid size, callsign, location, updates.
- **Layout** (`/layout`) – Assign modules to cells; expand/contract cells; per-cell settings.
- **Modules** (`/modules`) – List installed modules and status.
- **Updates** (`/updates`) – Check for updates, view changelog, apply update.
- **GPIO** (`/gpio`) – Pin assignments (Raspberry Pi only).

## Requirements

- Python 3.8+
- See `requirements/` for mode-specific deps:
  - `requirements-desktop-window.txt` – PyQt5, PyQtWebEngine
  - `requirements-headless.txt` – pystray, Pillow, pywin32 (Windows service)
  - `requirements-headless-linux.txt` – pystray, Pillow
