# Architecture

## Project Structure

```
Project/
├── run.py                 # Entry point
├── glancerf_config.json   # Config (created on first run)
├── glancerf/
│   ├── __init__.py        # Version
│   ├── main.py            # FastAPI app, API routes
│   ├── config/            # Config, logging
│   ├── routes/            # Web routes
│   │   ├── root.py        # Main dashboard
│   │   ├── readonly.py   # Read-only server
│   │   ├── setup_routes.py
│   │   ├── layout_routes.py
│   │   ├── pages.py      # Modules, updates
│   │   ├── gpio_routes.py
│   │   └── websocket.py
│   ├── views/             # HTML rendering
│   ├── web/               # Templates, static, WebSocket
│   ├── modules/           # Cell modules
│   ├── desktop/           # PyQt5, tray, Windows service
│   ├── gpio/              # Raspberry Pi GPIO
│   ├── services/          # Cache warmer, telemetry
│   ├── updates/           # Update checker, updater
│   └── utils/
├── requirements/
│   ├── requirements-linux.txt
│   ├── requirements-mac.txt
│   ├── requirements-windows.txt
│   └── requirements-windows-desktop.txt
├── installers/
└── docs/
```

## Servers

| Server | Port | Purpose |
|--------|------|---------|
| Main | 8080 | Full UI, WebSocket, API |
| Read-only | 8081 | Dashboard only, no interactions |

Both run in the same process (threads). Read-only connects to main's WebSocket for config updates.

## Routes

| Path | Description |
|------|-------------|
| `/` | Main dashboard |
| `/setup` | First-run setup (Hardware, Station, Layout, Tips) |
| `/layout` | Layout configurator |
| `/map-modules` | Map only modules (data providers for map overlay) |
| `/modules` | Modules list |
| `/updates` | Updates page |
| `/gpio` | GPIO setup (Raspberry Pi) |
| `/module/{id}/layout_settings.js` | Module layout UI |
| `/logo.png` | Favicon |
| `/static/*` | CSS, JS |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/time` | Current time (startup check) |
| GET | `/api/gps/status` | GPS setup status (devices, methods, hints) |
| GET | `/api/gps/stats` | GPS stats when connected (lat, lon, time, alt, speed, track, sats) |
| POST | `/api/gps/config` | Save GPS source and serial port |
| POST | `/api/restart` | Restart services |
| POST | `/api/telemetry/test` | Test telemetry |
| GET | `/api/update-status` | Version, update info |
| POST | `/api/check-updates` | Manual update check |
| GET | `/api/update-progress` | Update progress |
| POST | `/api/apply-update` | Apply update |

Module-owned routes (e.g. `/api/satellite/list`) are registered from `api_routes.py`.

## WebSocket

- `/ws/desktop` – Desktop app connection
- `/ws/browser` – Browser connection
- `/ws/readonly` – Read-only portal

Messages: `config_update` (reload), `update_available`, `gpio_input`, `state`.

## Startup Flow

1. Load config, setup logging
2. Validate module dependencies (exit if any fail)
3. Start readonly server (thread)
4. Start main server (thread)
5. Wait for HTTP ready
6. If desktop/browser: launch UI (PyQt or webbrowser)
7. Run cache warmer (background task)

## Desktop Mode

- PyQt5 + QtWebEngine
- Splash (tkinter) → main window with embedded browser
- Console hidden on Windows
- No tray icon (tray only in headless)

## Headless Mode

- Server only
- Windows: service + tray (pystray) at Startup
- Linux: systemd + tray autostart
- macOS: launchd + tray LaunchAgent
