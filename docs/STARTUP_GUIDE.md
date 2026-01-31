# GlanceRF – Startup Guide

This guide explains how to run GlanceRF automatically when your computer starts (or when you log in), on **Windows**, **Ubuntu/Linux**, **macOS**, and **Raspberry Pi**.

Before you start:

- GlanceRF must already be installed and working when you run it manually (see [USER_GUIDE.md](USER_GUIDE.md)).
- You need to know your **Project folder** path (the folder that contains `run.py`, `glancerf`, and `glancerf_config.json`).

---

## Contents

1. [Windows](#windows)
2. [Ubuntu and other Linux](#ubuntu-and-other-linux)
3. [macOS](#macos)
4. [Raspberry Pi](#raspberry-pi)
5. [Headless vs desktop mode](#headless-vs-desktop-mode)

---

## Windows

You can start GlanceRF at logon in two ways: **Startup folder** (simplest) or **Task Scheduler** (more control, no visible window if you want).

### Option A: Startup folder (easiest)

1. Press `Win + R`, type `shell:startup`, press Enter. A folder opens.
2. Right-click in the folder and choose **New** > **Shortcut**.
3. For the target, use one of these (replace `C:\Path\To\Project` with your real Project path):
   - If you use the batch file:  
     `C:\Path\To\Project\run_glancerf.bat`
   - If you run Python directly:  
     `C:\Windows\System32\cmd.exe /k cd /d C:\Path\To\Project && py -3 run.py`  
     (Or use `python` instead of `py -3` if that is how you run Python.)
4. Name the shortcut (e.g. **GlanceRF**) and finish.
5. Log off and log back in (or restart). GlanceRF should start automatically and a console window will appear.

To stop GlanceRF, close that console window or press Ctrl+C in it.

### Option B: Task Scheduler (no console window, or run at boot)

A PowerShell script is provided to create a scheduled task that runs GlanceRF at logon, with an optional **hidden** window so no console stays on screen.

1. Open PowerShell (right-click Start > **Windows PowerShell** or **Terminal**).
2. Go to your Project folder:
   ```powershell
   cd C:\Path\To\Project
   ```
3. Run the install script (this creates a task named **GlanceRF** that runs at your logon):
   ```powershell
   .\scripts\startup\install-windows-task.ps1
   ```
4. When prompted, confirm the path if it is correct, or edit the script to set `$ProjectPath` (see script comments).
5. Restart or log off and log back in. GlanceRF will start in the background.

To remove the task later:

```powershell
Unregister-ScheduledTask -TaskName "GlanceRF" -Confirm:$false
```

To run the script without a hidden window (so you see the console), edit `install-windows-task.ps1` and set `-WindowStyle Hidden` to `-WindowStyle Normal` in the `Register-ScheduledTask` command.

---

## Ubuntu and other Linux

On Linux we use **systemd** so GlanceRF runs as a user service: it starts when you log in and stops when you log out (or when you stop the service).

### 1. Install the user service

From your Project folder (the one that contains `run.py`):

```bash
cd /path/to/Project
chmod +x scripts/startup/install-systemd.sh
./scripts/startup/install-systemd.sh
```

The script copies the service file to `~/.config/systemd/user/glancerf.service`, fills in your Project path and Python path, and enables the service so it starts at logon.

### 2. Start the service now (optional)

```bash
systemctl --user start glancerf
```

### 3. Check status

```bash
systemctl --user status glancerf
```

### 4. Useful commands

| Action        | Command |
|---------------|--------|
| Start         | `systemctl --user start glancerf`   |
| Stop          | `systemctl --user stop glancerf`    |
| Restart       | `systemctl --user restart glancerf` |
| View logs     | `journalctl --user -u glancerf -f`  |
| Disable at login | `systemctl --user disable glancerf` |

### 5. Manual setup (if you prefer not to use the script)

1. Copy the service file:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp /path/to/Project/scripts/startup/glancerf.service ~/.config/systemd/user/
   ```
2. Edit `~/.config/systemd/user/glancerf.service` and replace:
   - `YOUR_PROJECT_PATH` with the full path to your Project folder (e.g. `/home/you/GlanceRF/Project`).
   - `YOUR_PYTHON3_PATH` with the full path to `python3` (run `which python3` to get it).
3. Enable and start:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable glancerf
   systemctl --user start glancerf
   ```

---

## macOS

On macOS we use **launchd** so GlanceRF runs as a **LaunchAgent**: it starts when you log in.

### 1. Install the LaunchAgent

From your Project folder:

```bash
cd /path/to/Project
chmod +x scripts/startup/install-mac-launchd.sh
./scripts/startup/install-mac-launchd.sh
```

The script copies the plist to `~/Library/LaunchAgents/com.glancerf.plist`, fills in your Project path and Python path, and loads it so it starts at logon.

### 2. Start GlanceRF now (optional)

```bash
launchctl load ~/Library/LaunchAgents/com.glancerf.plist
```

### 3. Useful commands

| Action    | Command |
|----------|--------|
| Start    | `launchctl load ~/Library/LaunchAgents/com.glancerf.plist`   |
| Stop     | `launchctl unload ~/Library/LaunchAgents/com.glancerf.plist` |
| View logs| Check Console.app, or run GlanceRF from Terminal once to see output. |

### 4. Manual setup

1. Copy the plist:
   ```bash
   cp /path/to/Project/scripts/startup/com.glancerf.plist ~/Library/LaunchAgents/
   ```
2. Edit `~/Library/LaunchAgents/com.glancerf.plist` and replace:
   - `YOUR_PROJECT_PATH` with the full path to your Project folder (e.g. `/Users/you/GlanceRF/Project`).
   - `YOUR_PYTHON3_PATH` with the full path to `python3` (run `which python3`; on Apple Silicon Homebrew it is often `/opt/homebrew/bin/python3`).
3. Load and enable at login:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.glancerf.plist
   ```

---

## Raspberry Pi

On Raspberry Pi OS (and most Pi distributions), use the same **systemd** approach as Ubuntu. Running as a **user** service is usually best so GlanceRF uses your home directory and config.

### 1. Install the user service

SSH or open a terminal on the Pi, then:

```bash
cd /home/pi/Project
# Or wherever your Project folder lives, e.g. /home/pi/GlanceRF/Project
chmod +x scripts/startup/install-systemd.sh
./scripts/startup/install-systemd.sh
```

The script is the same as on Ubuntu; it will use your home directory and the default `python3` on the Pi.

### 2. Start and enable

```bash
systemctl --user start glancerf
systemctl --user enable glancerf
```

### 3. Run at boot without logging in (optional)

If you want GlanceRF to start at **boot** before any user logs in (e.g. for a kiosk or headless Pi):

1. Install the service for the **system** (requires sudo). Copy the service file to the system directory and edit it to use the correct paths and the user you want to run as (e.g. `pi`):
   ```bash
   sudo cp /home/pi/Project/scripts/startup/glancerf.service /etc/systemd/system/
   sudo nano /etc/systemd/system/glancerf.service
   ```
   Set `WorkingDirectory` and `ExecStart` to your Project path and Python path. Add:
   ```ini
   [Service]
   User=pi
   Group=pi
   ```
   (or another user/group if you prefer).
2. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable glancerf
   sudo systemctl start glancerf
   ```
3. Use `sudo systemctl status glancerf`, `sudo systemctl stop glancerf`, etc.

For a **headless** Pi (no monitor), set `use_desktop` to `false` in `glancerf_config.json` and access the dashboard from another device using the Pi’s IP and the ports configured in config (e.g. port 8081 for read-only).

---

## Headless vs desktop mode

- **Desktop mode** (`use_desktop`: `true` in `glancerf_config.json`): opens the GlanceRF window on this machine. Use this for Windows/Mac/Linux when you run it on a PC with a display.
- **Headless mode** (`use_desktop`: `false`): no GUI; only the web server runs. Use this for:
  - Raspberry Pi without a monitor
  - Ubuntu server or any Linux/Mac/Windows machine you only access via browser

After changing `glancerf_config.json`, restart GlanceRF (or the service/task) for the change to take effect.

---

## Troubleshooting

- **Service or task does not start**
  - Check that the path to the Project folder and to `python3` (or `py`/`python` on Windows) are correct and have no typos.
  - On Linux/Mac, run `python3 run.py` (or `py run.py` / `run_glancerf.bat` on Windows) from the Project folder in a terminal to see any error messages.
- **Port already in use**
  - Change `port` and/or `readonly_port` in `glancerf_config.json` to values that are not in use.
- **Linux: user service not starting at login**
  - Ensure **lingering** is enabled for your user if you want the service to run when nobody is logged in:
    ```bash
    loginctl enable-linger $USER
    ```

---

## Summary

| Platform     | Method           | Script / file used                          |
|-------------|------------------|---------------------------------------------|
| Windows     | Startup folder   | Shortcut to `run_glancerf.bat` or `run.py`  |
| Windows     | Task Scheduler   | `scripts/startup/install-windows-task.ps1`   |
| Ubuntu/Linux| systemd (user)   | `scripts/startup/install-systemd.sh`, `glancerf.service` |
| macOS       | launchd          | `scripts/startup/install-mac-launchd.sh`, `com.glancerf.plist` |
| Raspberry Pi| systemd (user)   | Same as Ubuntu; optionally system-wide.    |

For more on running and configuring GlanceRF, see [USER_GUIDE.md](USER_GUIDE.md).
