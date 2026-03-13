# Installation

There are **three ways** to install GlanceRF:

| Method | Description |
|--------|--------------|
| **1. Core installer** | Download a small installer from the website; it fetches the latest code and runs the full installer. |
| **2. GitHub + installer** | Download the project from GitHub, extract it, then run the installer from the `Project/installers` folder. |
| **3. Manual** | Download from GitHub and install dependencies yourself; no installer. |

---

## Method 1: Core installer (easiest)

Download the installer for your OS and run it. It downloads the latest GlanceRF code and runs the full installer.

| Platform | Download | Run |
|----------|----------|-----|
| **Windows** | [GlanceRF-Install-Windows.exe](https://glancerf.zl4st.com/installers/GlanceRF-Install-Windows.exe) | Double-click the downloaded file |
| **Linux** | [GlanceRF-install-Linux.sh](https://glancerf.zl4st.com/installers/GlanceRF-install-Linux.sh) | `curl -sSL https://glancerf.zl4st.com/installers/GlanceRF-install-Linux.sh \| bash` |
| **macOS** | [GlanceRF-install-Mac.sh](https://glancerf.zl4st.com/installers/GlanceRF-install-Mac.sh) | `curl -sSL https://glancerf.zl4st.com/installers/GlanceRF-install-Mac.sh \| bash` |

---

## Method 2: GitHub + installer

1. Download the project: [GitHub main branch (ZIP)](https://github.com/pomtom44/GlanceRF/archive/refs/heads/main.zip)
2. Extract the ZIP to a folder of your choice
3. Run the installer from the `Project/installers` folder:

### Windows

```powershell
cd Project\installers
.\install-windows-gui.ps1
```

Or double-click `install-windows.bat` (runs `install-windows.ps1`).

- Prompts for mode: **Desktop app**, **Browser + Terminal**, **Terminal only**, or **Service**
- Modes 1–3: Run at logon, desktop shortcut
- Service mode: Installs as Windows service; tray icon; desktop shortcut opens http://localhost:PORT

### Linux

```bash
cd Project/installers
chmod +x install-linux.sh
./install-linux.sh
```

- **Desktop** (display available): Prompts for mode (Terminal + Browser, Terminal only, Service), shortcut, run at logon
- **Server** (no display, e.g. SSH): Single question – install as service (y/n)
- Desktop shortcut: `~/.local/share/applications/glancerf.desktop`
- Final message shows your local IP for browser access

### macOS

```bash
cd Project/installers
chmod +x install-mac.sh
./install-mac.sh
```

- **Desktop** (local session): Prompts for mode (Terminal + Browser, Terminal only, Service), shortcut, run at logon
- **Server** (SSH session): Single question – install as service (y/n)
- Desktop shortcut: `~/Desktop/GlanceRF.command`

---

## Method 3: Manual (no installer)

```bash
cd Project
pip install -r requirements/requirements-linux.txt   # Linux; or requirements-mac.txt (macOS); or requirements-windows.txt / requirements-windows-desktop.txt (Windows)
python run.py
```

Config is created at `glancerf_config.json` on first run. Open http://localhost:8080 for setup.

---

## Service mode (headless)

When you choose **Service** in the installer (or set `desktop_mode` to `headless`):

- **Windows:** Installs as a Windows service (requires Administrator). Tray icon in Startup. Desktop shortcut (if requested) is a `.url` file opening http://localhost:PORT
- **Linux:** systemd user service + tray autostart
- **macOS:** launchd service + tray LaunchAgent

### Manual Windows service install

```powershell
cd Project
python -m glancerf.desktop.glancerf_service install
sc config GlanceRF start= auto
net start GlanceRF
```

---

## Docker

```bash
cd Project
docker build -t glancerf .
docker run -p 8080:8080 -p 8081:8081 glancerf
```

- Runs in headless mode (`GLANCERF_DOCKER=1`)
- Ports 8080 (main), 8081 (readonly)

### Persist config and cache

To keep config and APRS cache across container restarts, mount a volume and set `GLANCERF_PROJECT`:

```bash
docker run -p 8080:8080 -p 8081:8081 \
  -e GLANCERF_PROJECT=/data \
  -v glancerf-data:/data \
  glancerf
```

Or use a host path:

```bash
docker run -p 8080:8080 -p 8081:8081 \
  -e GLANCERF_PROJECT=/data \
  -v /path/on/host/glancerf-data:/data \
  glancerf
```

Config is written to `glancerf_config.json` and the APRS cache to `cache/aprs.db` inside the mounted directory.
