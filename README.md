# GlanceRF

## What is GlanceRF

GlanceRF is a modern rebuild of the Original HamClock by Elwood WB0OEW.

During development of this project, early in Beta, Elwood passed away. Originally this was a side project, and I was going to tell people:
"If you want a mature project with support, go use hamclock."

Thoughts go to Elwood, and I thank him for the original project which so many use and which inspired this rebuild.

Disclaimer: This is a personal project. I built it for my needs but also designed it for ease of use for others.
Requests, bugs, etc. I will do my best to sort them out, however there may be periods where support and feature development slows down due to other commitments

![Main dashboard](docs/screenshots/Main%20Dashboard.png)

---

## **How do I install?**

**[→ Quick & Easy: Download and run the installer](https://glancerf.zl4st.com/quickstart.html)** — No GitHub needed. Just download for Windows, or run one command for Linux/Mac. Follow the prompts. Done.

---

## Screenshots

| Main dashboard | Setup | Layout editor |
|---------------|-------|---------------|
| ![Main dashboard](docs/screenshots/Main%20Dashboard.png) | ![Setup](docs/screenshots/Setup%20Page%201.png) | ![Layout editor](docs/screenshots/Editor%20Layout.png) |

See the [website](https://glancerf.zl4st.com) for more screenshots.

## Installation (4 methods)

| Method | Description |
|--------|-------------|
| **1. Core installer** | Download from [glancerf.zl4st.com/installers/](https://glancerf.zl4st.com/installers/) — GlanceRF-Install-Windows.exe, GlanceRF-install-Linux.sh, or GlanceRF-install-Mac.sh. Runs the full installer. |
| **2. GitHub + installer** | Download the [GitHub ZIP](https://github.com/pomtom44/GlanceRF/archive/refs/heads/main.zip), extract, then run the installer from `Project/installers`. |
| **3. Docker** | `docker run -p 8080:8080 pomtom44/glancerf` — Image on [Docker Hub](https://hub.docker.com/r/pomtom44/glancerf). See [DOCKER.md](../DOCKER.md) for options. |
| **4. Manual** | Download from GitHub, then `pip install -r requirements/requirements-linux.txt` (Linux), `requirements-mac.txt` (macOS), or `requirements-windows.txt` / `requirements-windows-desktop.txt` (Windows) and `python run.py` from the Project folder. |

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for details.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Installers for Windows, Linux, macOS; Docker |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Config file, environment variables |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | First run, setup, menu, layout, run at logon |
| [docs/CREATING_A_MODULE.md](docs/CREATING_A_MODULE.md) | How to add a custom cell module |
| [docs/MODULES.md](docs/MODULES.md) | Module structure, map overlays, API routes |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Project structure, routes, services |
| [docs/DEBUGGING.md](docs/DEBUGGING.md) | Log levels, APRS debug, troubleshooting |
| [docs/TELEMETRY.md](docs/TELEMETRY.md) | What data is collected, opt-out |
| [docs/THIRD_PARTY_AND_SERVICES.md](docs/THIRD_PARTY_AND_SERVICES.md) | External dependencies and APIs |
| [docs/FEATURE_REQUESTS.md](docs/FEATURE_REQUESTS.md) | Requested features and status |

## Run Modes

| Mode | Description |
|------|-------------|
| **Desktop** | Native PyQt5 window with embedded browser. Console hidden on Windows. |
| **Browser** | Terminal + browser. Server runs in terminal; opens default browser. |
| **Terminal** | Terminal only. Server runs in terminal; no automatic browser. |
| **Headless** | Server only. No window. Use as Windows service, systemd, or launchd. Tray icon (headless only) for quick access. |

Set via `desktop_mode` in config or installers.

## Feature requests & Bugs
See [docs/FEATURE_REQUESTS.md](docs/FEATURE_REQUESTS.md) for the list.
To request a feature or raise a bug, open an Issue using the Github issues.
If you don't have a github account, and still want to raise a bug, email me GlanceRF@zl4st.com

---

*This project is developed with AI-assisted tools (e.g. Cursor). Code is reviewed and tested, but please report any issues you encounter.*
