# GlanceRF – Startup Guide

This guide explains how to run GlanceRF automatically when your computer starts (or when you log in), on **Windows**, **Ubuntu/Linux**, **macOS**, and **Raspberry Pi**.

Before you start:

- GlanceRF must already be installed and working when you run it manually (see [USER_GUIDE.md](USER_GUIDE.md)).
- You need to know your **Project folder** path (the folder that contains `run.py`, `glancerf`, and `glancerf_config.json`).

---

## Contents

1. [Easiest: use the installer](#easiest-use-the-installer)
2. [Windows (manual)](#windows-manual)
3. [Ubuntu and other Linux (manual)](#ubuntu-and-other-linux-manual)
4. [macOS (manual)](#macos-manual)
5. [Raspberry Pi](#raspberry-pi)
6. [Headless vs desktop mode](#headless-vs-desktop-mode)

---

## Easiest: use the installer

The simplest way to get GlanceRF running at logon is to run the **installer** for your OS. It will ask whether to run at startup and create the task/service for you.

| Platform | From Project folder |
|----------|---------------------|
| **Windows** | Double‑click `installers\install-windows.bat` (or run `powershell -ExecutionPolicy Bypass -File installers\install-windows.ps1`). When prompted “Run GlanceRF at Windows logon? (Y/N)”, choose **Y**. |
| **Linux** | `chmod +x installers/install-linux.sh` then `./installers/install-linux.sh`. When prompted “Run GlanceRF at logon? (y/n)”, choose **y**. |
| **macOS** | `chmod +x installers/install-mac.sh` then `./installers/install-mac.sh`. When prompted “Run GlanceRF at logon? (y/n)”, choose **y**. |

The installer also handles Python, requirements, desktop/headless config, and an optional desktop shortcut.

---

## Windows (manual)

You can start GlanceRF at logon in two ways: **Startup folder** (simplest) or **Task Scheduler** (no visible window if you want).

### Option A: Startup folder (easiest)

1. Press `Win + R`, type `shell:startup`, press Enter. A folder opens.
2. Right-click in the folder and choose **New** > **Shortcut**.
3. For the target, use (replace `C:\Path\To\Project` with your real Project path):
   - **Run Python directly:**  
     `C:\Windows\System32\cmd.exe /k cd /d C:\Path\To\Project && py -3 run.py`  
     (Or use `python` instead of `py -3` if that is how you run Python.)
4. Name the shortcut (e.g. **GlanceRF**) and finish.
5. Log off and log back in (or restart). GlanceRF should start automatically and a console window will appear.

To stop GlanceRF, close that console window or press Ctrl+C in it.

### Option B: Task Scheduler (no console window)

1. Open PowerShell, go to your Project folder: `cd C:\Path\To\Project`.
2. Create a scheduled task that runs at your logon (replace `C:\Path\To\Project` and `py -3` if needed):
   ```powershell
   $ProjectPath = "C:\Path\To\Project"
   $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c cd /d `"$ProjectPath`" && py -3 run.py" -WorkingDirectory $ProjectPath -WindowStyle Hidden
   $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
   $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
   $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
   Register-ScheduledTask -TaskName "GlanceRF" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
   ```
3. Log off and log back in. GlanceRF will start in the background.

To remove the task later:

```powershell
Unregister-ScheduledTask -TaskName "GlanceRF" -Confirm:$false
```

---

## Ubuntu and other Linux (manual)

On Linux we use **systemd** so GlanceRF runs as a user service: it starts when you log in and stops when you log out (or when you stop the service).

### 1. Create the user service

From your Project folder (the one that contains `run.py`):

```bash
mkdir -p ~/.config/systemd/user
```

Create `~/.config/systemd/user/glancerf.service` with (replace `/path/to/Project` and the Python path):

```ini
[Unit]
Description=GlanceRF dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/Project
ExecStart=/usr/bin/python3 run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

Use `which python3` to get the correct `ExecStart` path.

### 2. Enable and start

```bash
systemctl --user daemon-reload
systemctl --user enable glancerf
systemctl --user start glancerf
```

### 3. Useful commands

| Action        | Command |
|---------------|--------|
| Start         | `systemctl --user start glancerf`   |
| Stop          | `systemctl --user stop glancerf`    |
| Restart       | `systemctl --user restart glancerf` |
| View logs     | `journalctl --user -u glancerf -f`  |
| Disable at login | `systemctl --user disable glancerf` |

---

## macOS (manual)

On macOS we use **launchd** so GlanceRF runs as a LaunchAgent: it starts when you log in.

### 1. Create the LaunchAgent

Create `~/Library/LaunchAgents/com.glancerf.plist` with (replace `/path/to/Project` and the Python path):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glancerf</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/Project</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/Project/glancerf.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/Project/glancerf.log</string>
</dict>
</plist>
```

Use `which python3` to get the correct path (e.g. `/opt/homebrew/bin/python3` on Apple Silicon Homebrew).

### 2. Load and start

```bash
launchctl load ~/Library/LaunchAgents/com.glancerf.plist
```

### 3. Useful commands

| Action    | Command |
|----------|--------|
| Start    | `launchctl load ~/Library/LaunchAgents/com.glancerf.plist`   |
| Stop     | `launchctl unload ~/Library/LaunchAgents/com.glancerf.plist` |
| View logs| `~/Project/glancerf.log` or Console.app |

---

## Raspberry Pi

On Raspberry Pi OS use the same **systemd** approach as Ubuntu. Run the Linux installer from the Project folder (`./installers/install-linux.sh`) and choose “Run at logon”, or follow the [Ubuntu and other Linux (manual)](#ubuntu-and-other-linux-manual) steps.

For a **headless** Pi (no monitor), set `use_desktop` to `false` in `glancerf_config.json` and access the dashboard from another device using the Pi’s IP and the ports in config (e.g. port 8081 for read-only).

To run at **boot** before any user logs in (e.g. kiosk): copy the service file to `/etc/systemd/system/glancerf.service`, edit it to set `User=` and `Group=` and the correct paths, then `sudo systemctl daemon-reload`, `sudo systemctl enable glancerf`, `sudo systemctl start glancerf`.

---

## Headless vs desktop mode

- **Desktop mode** (`use_desktop`: `true` in `glancerf_config.json`): opens the GlanceRF window on this machine. Use this when you run it on a PC with a display.
- **Headless mode** (`use_desktop`: `false`): no GUI; only the web server runs. Use this for Raspberry Pi without a monitor, or any machine you only access via browser.

After changing `glancerf_config.json`, restart GlanceRF (or the service/task) for the change to take effect.

---

## Troubleshooting

- **Service or task does not start**
  - Check that the path to the Project folder and to `python3` (or `py`/`python` on Windows) are correct and have no typos.
  - On Linux/Mac, run `python3 run.py` from the Project folder in a terminal to see any error messages. On Windows, run `py -3 run.py` (or `python run.py`) from the Project folder.
- **Port already in use**
  - Change `port` and/or `readonly_port` in `glancerf_config.json` to values that are not in use.
- **Linux: user service not starting at login**
  - Ensure **lingering** is enabled if you want the service to run when nobody is logged in:
    ```bash
    loginctl enable-linger $USER
    ```

---

## Summary

| Platform     | Easiest              | Manual option                    |
|-------------|----------------------|----------------------------------|
| Windows     | `installers\install-windows.bat` | Startup folder shortcut or Task Scheduler (see above) |
| Ubuntu/Linux| `./installers/install-linux.sh`  | systemd user service (`~/.config/systemd/user/glancerf.service`) |
| macOS       | `./installers/install-mac.sh`    | launchd (`~/Library/LaunchAgents/com.glancerf.plist`) |
| Raspberry Pi| Same as Linux        | Same as Ubuntu; optionally system-wide. |

For more on running and configuring GlanceRF, see [USER_GUIDE.md](USER_GUIDE.md).
