#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$ProjectPath = $null
if (Test-Path (Join-Path $PSScriptRoot "..\run.py")) {
    $ProjectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
if (-not $ProjectPath -or -not (Test-Path (Join-Path $ProjectPath "run.py"))) {
    $ProjectPath = (Get-Location).Path
}
if (-not (Test-Path (Join-Path $ProjectPath "run.py"))) {
    Write-Host "Error: run.py not found. Run this script from the Project folder or from Project\installers."
    exit 1
}

$ConfigPath = Join-Path $ProjectPath "glancerf_config.json"
$RequirementsPath = Join-Path $ProjectPath "requirements.txt"
# Python version to download when not installed (update when needed for latest 3.12)
$PythonInstallVersion = "3.12.7"

# --- 1. Check / install Python ---
$PythonCmd = $null
foreach ($try in @("py -3", "python3", "python")) {
    try {
        if ($try -eq "py -3") {
            & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        } else {
            & $try -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        }
        if ($LASTEXITCODE -eq 0) {
            $PythonCmd = $try
            break
        }
    } catch {
        continue
    }
}

if (-not $PythonCmd) {
    Write-Host "Python 3.8 or higher not found."
    $autoInstall = Read-Host "Download and install Python $PythonInstallVersion automatically? (Y/N)"
    if ($autoInstall -eq "Y" -or $autoInstall -eq "y") {
        $is64 = [Environment]::Is64BitOperatingSystem
        $arch = if ($is64) { "amd64" } else { "win32" }
        $fileName = if ($is64) { "python-$PythonInstallVersion-amd64.exe" } else { "python-$PythonInstallVersion.exe" }
        $installerUrl = "https://www.python.org/ftp/python/$PythonInstallVersion/$fileName"
        $installerPath = Join-Path $env:TEMP "python-glancerf-installer-$([Guid]::NewGuid().ToString('N')).exe"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        try {
            $req = [System.Net.HttpWebRequest]::Create($installerUrl)
            $req.UserAgent = "PowerShell"
            $req.Method = "GET"
            $resp = $req.GetResponse()
            $totalBytes = $resp.ContentLength
            $respStream = $resp.GetResponseStream()
            $fileStream = [System.IO.File]::Create($installerPath)
            $buffer = New-Object byte[] 65536
            $bytesRead = 0
            $totalRead = 0
            do {
                $bytesRead = $respStream.Read($buffer, 0, $buffer.Length)
                if ($bytesRead -gt 0) {
                    $fileStream.Write($buffer, 0, $bytesRead)
                    $totalRead += $bytesRead
                    if ($totalBytes -gt 0) {
                        $pct = [int](($totalRead / $totalBytes) * 100)
                        Write-Progress -Activity "Downloading" -Status "$pct% complete" -PercentComplete $pct
                    } else {
                        Write-Progress -Activity "Downloading" -Status "Please wait..." -PercentComplete -1
                    }
                }
            } while ($bytesRead -gt 0)
            $fileStream.Close()
            $respStream.Close()
            $resp.Close()
        } catch {
            Write-Progress -Activity "Downloading" -Completed -ErrorAction SilentlyContinue
            Write-Host "Download failed: $_"
            Write-Host "Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
            exit 1
        }
        Write-Progress -Activity "Downloading" -Completed
        Write-Host "Installing Python (installer window will open)..."
        Write-Host "This installation can take a while; let it finish."
        Start-Sleep -Seconds 5
        $p = Start-Process -FilePath $installerPath -ArgumentList "/passive", "PrependPath=1", "InstallAllUsers=0" -Wait -PassThru
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        if ($p.ExitCode -eq 0) {
            $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
            $PythonCmd = $null
            foreach ($try in @("py -3", "python3", "python")) {
                try {
                    if ($try -eq "py -3") {
                        & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
                    } else {
                        & $try -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
                    }
                    if ($LASTEXITCODE -eq 0) {
                        $PythonCmd = $try
                        break
                    }
                } catch { continue }
            }
            if ($PythonCmd) {
                Write-Host "Python installed. Continuing with setup..."
                Write-Host ""
            } else {
                Write-Host "Python was installed but is not yet in this session's PATH. Close and reopen this window, then run this script again."
                exit 0
            }
        } elseif ($p.ExitCode -eq 1618) {
            Write-Host "Another installation is in progress (or a previous one did not finish)."
            Write-Host "Wait a few minutes, then run this script again. Or close other installers and try again."
        } else {
            Write-Host "Installation returned exit code $($p.ExitCode). Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
            exit 1
        }
    } else {
        Write-Host "Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
        exit 1
    }
}

# --- 2. Desktop or headless? ---
$WantHeadless = $false
$modeResp = Read-Host "Run in desktop (terminal + browser) or headless (server only)? (desktop/headless)"
if ($modeResp -match "headless") { $WantHeadless = $true }

# --- 3. Check / install requirements ---
Write-Host "Checking requirements..."
$pipOk = $false
try {
    if ($PythonCmd -eq "py -3") {
        & py -3 -m pip install -r $RequirementsPath -q 2>$null
    } else {
        & $PythonCmd -m pip install -r $RequirementsPath -q 2>$null
    }
    if ($LASTEXITCODE -eq 0) { $pipOk = $true }
} catch {
    # ignore
}
if (-not $pipOk) {
    Write-Host "Installing requirements..."
    if ($PythonCmd -eq "py -3") {
        & py -3 -m pip install -r $RequirementsPath
    } else {
        & $PythonCmd -m pip install -r $RequirementsPath
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install requirements."
        exit 1
    }
}
Write-Host "Requirements OK."

# --- 2b. Check / install ffmpeg (for webcam Local server) ---
$ffmpegOk = $false
try {
    $null = & ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) { $ffmpegOk = $true }
} catch {
    # ffmpeg not in PATH
}
if (-not $ffmpegOk) {
    Write-Host "ffmpeg not found (optional; needed for Webcam module Local server source)."
    $installFfmpeg = Read-Host "Install ffmpeg now? (Y/N)"
    if ($installFfmpeg -eq "Y" -or $installFfmpeg -eq "y") {
        $installed = $false
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            try {
                winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
                if ($LASTEXITCODE -eq 0) { $installed = $true }
            } catch {}
        }
        if (-not $installed -and (Get-Command choco -ErrorAction SilentlyContinue)) {
            try {
                choco install ffmpeg -y
                if ($LASTEXITCODE -eq 0) { $installed = $true }
            } catch {}
        }
        if ($installed) {
            Write-Host "ffmpeg installed. You may need to restart this window for PATH to update."
        } else {
            Write-Host "Could not install ffmpeg automatically. Download from https://ffmpeg.org/download.html and add to PATH."
        }
    } else {
        Write-Host "You can install ffmpeg later (winget install Gyan.FFmpeg or from https://ffmpeg.org/download.html) for Webcam Local server."
    }
} else {
    Write-Host "ffmpeg OK."
}

# Headless on Windows: install pywin32 for the service
if ($WantHeadless) {
    Write-Host "Installing pywin32 for Windows service..."
    $pipOk = $false
    $prevErrAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($PythonCmd -eq "py -3") {
            & py -3 -m pip install pywin32 -q 2>&1 | Out-Null
        } else {
            & $PythonCmd -m pip install pywin32 -q 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -eq 0) { $pipOk = $true }
    } catch {
        # pip or py may write to stderr; ignore
    }
    if (-not $pipOk) {
        try {
            if ($PythonCmd -eq "py -3") {
                & py -3 -m pip install pywin32 2>&1 | Out-Null
            } else {
                & $PythonCmd -m pip install pywin32 2>&1 | Out-Null
            }
            if ($LASTEXITCODE -eq 0) { $pipOk = $true }
        } catch { }
    }
    $ErrorActionPreference = $prevErrAction
}

# --- 4. Run on startup? (desktop only; headless service is set to auto-start later) ---
$WantStartup = $false
if (-not $WantHeadless) {
    $startupResp = Read-Host "Run GlanceRF at Windows logon? (Y/N)"
    if ($startupResp -eq "Y" -or $startupResp -eq "y") { $WantStartup = $true }
}

# Update config: use_desktop (via Python to preserve JSON structure)
$env:GLANCERF_PROJECT = $ProjectPath
$useDesktopVal = if ($WantHeadless) { "False" } else { "True" }
$configScript = "import json, os; p = os.path.join(os.environ.get('GLANCERF_PROJECT',''), 'glancerf_config.json'); c = json.load(open(p,'r',encoding='utf-8')) if os.path.exists(p) else {'port':8080,'readonly_port':8081,'use_desktop':True,'first_run':True,'max_grid_scale':10,'grid_columns':3,'grid_rows':3,'aspect_ratio':'16:9','orientation':'landscape','layout':[['','',''],['','',''],['','','']],'cell_spans':{},'module_settings':{}}; c['use_desktop'] = $useDesktopVal; json.dump(c, open(p,'w',encoding='utf-8'), indent=2)"
if ($PythonCmd -eq "py -3") {
    & py -3 -c $configScript
} else {
    & $PythonCmd -c $configScript
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: could not update config file."
}
Write-Host "Config set to $(if ($WantHeadless) { 'headless' } else { 'desktop' })."

# --- 5. Desktop shortcut? (desktop mode only) ---
$WantShortcut = $false
if (-not $WantHeadless) {
    $shortcutResp = Read-Host "Create a shortcut on your desktop? (Y/N)"
    if ($shortcutResp -eq "Y" -or $shortcutResp -eq "y") { $WantShortcut = $true }
}

if ($WantShortcut) {
    try {
        $pythonExe = if ($PythonCmd -eq "py -3") {
            (py -3 -c "import sys; print(sys.executable)").Trim()
        } else {
            (& $PythonCmd -c "import sys; print(sys.executable)").Trim()
        }
        $desktop = [Environment]::GetFolderPath("Desktop")
        $lnkPath = Join-Path $desktop "GlanceRF.lnk"
        $ws = New-Object -ComObject WScript.Shell
        $sc = $ws.CreateShortcut($lnkPath)
        $sc.TargetPath = $pythonExe
        $sc.Arguments = "run.py"
        $sc.WorkingDirectory = $ProjectPath
        $sc.Description = "GlanceRF dashboard"
        $logoIco = Join-Path $ProjectPath "logos\logo.ico"
        $logoPng = Join-Path $ProjectPath "logos\logo.png"
        if (Test-Path $logoIco) {
            $sc.IconLocation = "$logoIco,0"
        } elseif (Test-Path $logoPng) {
            $sc.IconLocation = "$logoPng,0"
        }
        $sc.Save()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
        Write-Host "Shortcut created on desktop: GlanceRF.lnk"
    } catch {
        Write-Host "Could not create shortcut: $_"
    }
}

# --- 6. Create startup task (desktop) or install Windows service (headless) ---
if ($WantHeadless) {
    # Headless: install as Windows service (requires Administrator)
    Set-Location $ProjectPath
    Write-Host "Installing GlanceRF as a Windows service (requires Administrator)..."
    $serviceInstallOk = $false
    try {
        if ($PythonCmd -eq "py -3") {
            & py -3 glancerf\glancerf_service.py install 2>&1
        } else {
            & $PythonCmd glancerf\glancerf_service.py install 2>&1
        }
        if ($LASTEXITCODE -eq 0) { $serviceInstallOk = $true }
    } catch {
        # ignore
    }
    if ($serviceInstallOk) {
        & sc.exe config GlanceRF start= auto 2>$null
        Write-Host "Service set to start automatically at boot."
        Write-Host "GlanceRF service installed. Start/stop via Services (services.msc) or: net start GlanceRF / net stop GlanceRF"
    } else {
        Write-Host "Could not install the service (Administrator rights may be required)."
        Write-Host "To install manually: Run PowerShell as Administrator, cd to Project folder, then: python glancerf\glancerf_service.py install"
    }
} else {
    # Desktop: create startup task (use python.exe so a console window shows logs)
    $startupTaskCreated = $false
    if ($WantStartup) {
        $TaskName = "GlanceRF"
        try {
            $pyExePath = if ($PythonCmd -eq "py -3") {
                (py -3 -c "import sys; print(sys.executable)").Trim()
            } else {
                (& $PythonCmd -c "import sys; print(sys.executable)").Trim()
            }
            $Action = New-ScheduledTaskAction -Execute $pyExePath -Argument "run.py" -WorkingDirectory $ProjectPath
            $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            Unregister-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
            $startupTaskCreated = $true
            Write-Host "Startup task created. GlanceRF will run at logon (terminal window and browser)."
        } catch {
            Write-Host "Could not create startup task (access denied or not allowed in this environment)."
            Write-Host "To add it later: Run this installer as Administrator, or create a shortcut and place it in your Startup folder."
        }
    }
}

# --- 7. Run now or start task/service ---
if ($WantHeadless) {
    if ($serviceInstallOk) {
        Write-Host "Starting GlanceRF service..."
        Start-Process -FilePath "net" -ArgumentList "start", "GlanceRF" -Verb RunAs -Wait -ErrorAction SilentlyContinue
        # Tray icon: add to Startup (runs at logon) and run once now so it appears after setup
        try {
            $pyExePath = if ($PythonCmd -eq "py -3") {
                (py -3 -c "import sys; print(sys.executable)").Trim()
            } else {
                (& $PythonCmd -c "import sys; print(sys.executable)").Trim()
            }
            $pythonwPath = $pyExePath -replace "python\.exe$", "pythonw.exe"
            if (-not (Test-Path $pythonwPath)) { $pythonwPath = $pyExePath }
            $startupFolder = [Environment]::GetFolderPath("Startup")
            $trayLnkPath = Join-Path $startupFolder "GlanceRF Tray.lnk"
            $ws = New-Object -ComObject WScript.Shell
            $sc = $ws.CreateShortcut($trayLnkPath)
            $sc.TargetPath = $pythonwPath
            $sc.Arguments = "-m glancerf.tray_helper"
            $sc.WorkingDirectory = $ProjectPath
            $sc.Description = "GlanceRF tray icon (opens browser)"
            $logoIco = Join-Path $ProjectPath "logos\logo.ico"
            if (Test-Path $logoIco) { $sc.IconLocation = "$logoIco,0" }
            $sc.Save()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
            Write-Host "Tray icon added to Startup (runs at logon)."
            Start-Process -FilePath $pythonwPath -ArgumentList "-m glancerf.tray_helper" -WorkingDirectory $ProjectPath -WindowStyle Hidden
            Write-Host "Tray icon started (click it to open GlanceRF in browser)."
        } catch {
            Write-Host "Could not add tray to Startup or start tray: $_"
        }
        Write-Host ""
        Write-Host "============================================"
        Write-Host "GlanceRF (headless) is running as a service."
        Write-Host "============================================"
        Write-Host "Open a browser and go to:  http://localhost:8080"
        $ipAddr = $null
        try {
            $ipAddr = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^127\." } | Select-Object -First 1).IPAddress
        } catch { }
        if (-not $ipAddr) {
            try {
                $cfg = Get-NetIPConfiguration -ErrorAction SilentlyContinue | Where-Object { $_.IPv4DefaultGateway -ne $null } | Select-Object -First 1
                if ($cfg -and $cfg.IPv4Address) {
                    $a = $cfg.IPv4Address.IPAddress
                    if ($a -is [array]) { $a = $a | Where-Object { $_ -and $_ -notmatch "^127\." } | Select-Object -First 1 }
                    if ($a -and $a -notmatch "^127\.") { $ipAddr = $a }
                }
            } catch { }
        }
        if (-not $ipAddr) {
            try {
                $addrs = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) | Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and $_.IPAddressToString -notmatch "^127\." }
                if ($addrs -and $addrs.Count -gt 0) { $ipAddr = $addrs[0].IPAddressToString }
            } catch { }
        }
        if (-not $ipAddr) {
            try {
                $nic = Get-WmiObject Win32_NetworkAdapterConfiguration -ErrorAction SilentlyContinue | Where-Object { $_.IPEnabled -eq $true -and $_.IPAddress -ne $null } | Select-Object -First 1
                if ($nic -and $nic.IPAddress) { $ipAddr = ($nic.IPAddress | Where-Object { $_ -notmatch "^127\." }) | Select-Object -First 1 }
            } catch { }
        }
        if ($ipAddr) {
            Write-Host "From another device use:    http://${ipAddr}:8080"
        } else {
            Write-Host "From another device use:    http://<this PC's IP>:8080"
        }
        Write-Host "============================================"
        Write-Host ""
        Read-Host "Press Enter to close this window"
    } else {
        Write-Host "Starting GlanceRF in this window (server only)..."
        Set-Location $ProjectPath
        if ($PythonCmd -eq "py -3") { & py -3 run.py } else { & $PythonCmd run.py }
    }
} elseif ($WantStartup -and $startupTaskCreated) {
    Write-Host "Starting GlanceRF now (startup task will also run at next logon)..."
    try {
        Start-ScheduledTask -TaskName "GlanceRF" -ErrorAction Stop
        Write-Host "To stop: Unregister-ScheduledTask -TaskName GlanceRF"
    } catch {
        Write-Host "Could not start the task; run GlanceRF manually from the shortcut or: python run.py"
    }
} elseif ($WantStartup -and -not $startupTaskCreated) {
    Write-Host "Starting GlanceRF..."
    Set-Location $ProjectPath
    if ($PythonCmd -eq "py -3") { & py -3 run.py } else { & $PythonCmd run.py }
} else {
    Write-Host "Starting GlanceRF..."
    Set-Location $ProjectPath
    if ($PythonCmd -eq "py -3") {
        & py -3 run.py
    } else {
        & $PythonCmd run.py
    }
}
