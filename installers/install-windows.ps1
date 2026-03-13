#Requires -Version 5.1
$ErrorActionPreference = "Stop"

trap {
    Write-Host "`nError: $_"
    Read-Host "Press Enter to close"
    exit 1
}

if (-not $PSScriptRoot) {
    try {
        $exePath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
        $PSScriptRoot = [System.IO.Path]::GetDirectoryName($exePath)
    } catch { }
}

function Exit-WithError { param([string]$Msg) Write-Host $Msg; Write-Host ""; Read-Host "Press Enter to close"; exit 1 }

$ProjectPath = $null
if (Test-Path (Join-Path $PSScriptRoot "..\run.py")) {
    $ProjectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
if (-not $ProjectPath -or -not (Test-Path (Join-Path $ProjectPath "run.py"))) {
    $ProjectPath = (Get-Location).Path
}
if (-not (Test-Path (Join-Path $ProjectPath "run.py"))) {
    Exit-WithError "Error: run.py not found. Run this script from the Project folder or from Project\installers."
}

$PythonInstallVersion = "3.12.7"

# --- ALL QUESTIONS FIRST (before any long operations) ---
Write-Host ""
Write-Host "GlanceRF Installer - Answer a few questions first."
Write-Host ""

# 1. Quick Python check
$PythonCmd = $null
foreach ($try in @("py -3", "python3", "python")) {
    try {
        if ($try -eq "py -3") { & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
        else { & $try -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
        if ($LASTEXITCODE -eq 0) { $PythonCmd = $try; break }
    } catch { continue }
}

$needPythonDownload = $false
if (-not $PythonCmd) {
    Write-Host "Python 3.8 or higher not found."
    $autoInstall = Read-Host "Download and install Python $PythonInstallVersion automatically? (Y/N)"
    if ($autoInstall -eq "Y" -or $autoInstall -eq "y") { $needPythonDownload = $true }
    else { Exit-WithError "Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run again." }
}

# 2. Mode
Write-Host ""
Write-Host "1) Desktop app      - PyQt window, no terminal, no service, no taskbar icon"
Write-Host "2) Browser+Terminal - Launch terminal and browser"
Write-Host "3) Terminal only    - Launch terminal, no browser"
Write-Host "4) Service          - Runs as Windows service, taskbar icon, shortcut opens browser"
$modeResp = Read-Host "Choose mode (1/2/3/4)"
$desktopMode = "browser"
if ($modeResp -eq "1") { $desktopMode = "desktop" }
elseif ($modeResp -eq "2") { $desktopMode = "browser" }
elseif ($modeResp -eq "3") { $desktopMode = "terminal" }
elseif ($modeResp -eq "4") { $desktopMode = "headless" }

# 3. Run at startup (modes 1, 2, 3 only; mode 4 is a service so auto-starts)
$WantStartup = $false
if ($desktopMode -ne "headless") {
    $r = Read-Host "Run GlanceRF at Windows logon? (Y/N)"
    if ($r -eq "Y" -or $r -eq "y") { $WantStartup = $true }
}

# 4. Desktop shortcut
$WantShortcut = $false
if ($desktopMode -eq "headless") {
    $r = Read-Host "Create a desktop shortcut to open GlanceRF in browser? (Y/N)"
} else {
    $r = Read-Host "Create a shortcut on your desktop? (Y/N)"
}
if ($r -eq "Y" -or $r -eq "y") { $WantShortcut = $true }

Write-Host ""
Write-Host "Installing... (this may take a few minutes)"
Write-Host ""

# --- PROCESSING (Python install, requirements, config, shortcut, service) ---

# 1. Install Python if needed
if ($needPythonDownload) {
    $is64 = [Environment]::Is64BitOperatingSystem
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
        $totalRead = 0
        do {
            $bytesRead = $respStream.Read($buffer, 0, $buffer.Length)
            if ($bytesRead -gt 0) {
                $fileStream.Write($buffer, 0, $bytesRead)
                $totalRead += $bytesRead
                if ($totalBytes -gt 0) { Write-Progress -Activity "Downloading Python" -Status "$([int]($totalRead/$totalBytes*100))% complete" -PercentComplete ([int]($totalRead/$totalBytes*100)) }
            }
        } while ($bytesRead -gt 0)
        $fileStream.Close()
        $respStream.Close()
        $resp.Close()
    } catch {
        Write-Progress -Activity "Downloading" -Completed -ErrorAction SilentlyContinue
        Exit-WithError "Download failed: $_`nInstall Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
    }
    Write-Progress -Activity "Downloading" -Completed
    Write-Host "Installing Python (installer window will open)..."
    Start-Sleep -Seconds 5
    $p = Start-Process -FilePath $installerPath -ArgumentList "/passive", "PrependPath=1", "InstallAllUsers=0", "Include_doc=0", "Include_tcltk=0", "Include_test=0", "Shortcuts=0" -Wait -PassThru
    Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    if ($p.ExitCode -eq 0) {
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
        foreach ($t in @("py -3", "python3", "python")) {
            try {
                if ($t -eq "py -3") { & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
                else { & $t -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
                if ($LASTEXITCODE -eq 0) { $PythonCmd = $t; break }
            } catch { continue }
        }
        if (-not $PythonCmd) {
            Write-Host "Python installed but not in PATH. Close and reopen this window, then run again."
            Read-Host "Press Enter to close"
            exit 0
        }
        Write-Host "Python installed."
    } elseif ($p.ExitCode -eq 1618) {
        Exit-WithError "Another installation in progress. Wait a few minutes, then run again."
    } else {
        Exit-WithError "Installation failed (exit $($p.ExitCode)). Install from https://www.python.org/downloads/"
    }
}

# --- 2. Install requirements ---
$reqPath = $null
if ($desktopMode -eq "desktop") {
    $reqPath = Join-Path $ProjectPath "requirements\requirements-windows-desktop.txt"
} else {
    $reqPath = Join-Path $ProjectPath "requirements\requirements-windows.txt"
}
if (-not (Test-Path $reqPath)) {
    $reqPath = Join-Path $ProjectPath "requirements\requirements-windows.txt"
}
if (-not (Test-Path $reqPath)) {
    Exit-WithError "Requirements file not found: $reqPath"
}

Write-Host "Installing requirements..."
if ($PythonCmd -eq "py -3") { & py -3 -m pip install -r $reqPath -q 2>&1 | Out-Null }
else { & $PythonCmd -m pip install -r $reqPath -q 2>&1 | Out-Null }
if ($LASTEXITCODE -ne 0) {
    Write-Host "Retrying with full output..."
    if ($PythonCmd -eq "py -3") { & py -3 -m pip install -r $reqPath }
    else { & $PythonCmd -m pip install -r $reqPath }
    if ($LASTEXITCODE -ne 0) { Exit-WithError "Failed to install requirements." }
}
Write-Host "Requirements OK."

# Headless: install pywin32 for service
if ($desktopMode -eq "headless") {
    Write-Host "Installing pywin32 for Windows service..."
    if ($PythonCmd -eq "py -3") { & py -3 -m pip install pywin32 -q 2>&1 | Out-Null }
    else { & $PythonCmd -m pip install pywin32 -q 2>&1 | Out-Null }
}

# --- 3. Update config ---
$configPath = Join-Path $ProjectPath "glancerf_config.json"
$env:GLANCERF_CONFIG_PATH = $configPath
$env:GLANCERF_DESKTOP_MODE = $desktopMode
$configScript = "import json, os; p=os.environ.get('GLANCERF_CONFIG_PATH',''); c=json.load(open(p,'r',encoding='utf-8')) if os.path.exists(p) else {}; c['desktop_mode']=os.environ.get('GLANCERF_DESKTOP_MODE','browser'); json.dump(c, open(p,'w',encoding='utf-8'), indent=2)"
if ($PythonCmd -eq "py -3") { & py -3 -c $configScript } else { & $PythonCmd -c $configScript }
Write-Host "Config set to $desktopMode."

# --- 4. Create shortcut ---
if ($WantShortcut) {
    try {
        $desktop = [Environment]::GetFolderPath("Desktop")
        if ($desktopMode -eq "headless") {
            # Service mode: create URL shortcut to web page (not Python)
            $port = 8080
            if (Test-Path $configPath) {
                try {
                    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
                    if ($cfg.port) { $port = $cfg.port }
                } catch { }
            }
            $urlPath = Join-Path $desktop "GlanceRF.url"
            $urlContent = @"
[InternetShortcut]
URL=http://localhost:$port
"@
            $logoIco = Join-Path $ProjectPath "logos\logo.ico"
            if (Test-Path $logoIco) {
                $urlContent += "`nIconIndex=0`nIconFile=$logoIco"
            }
            [System.IO.File]::WriteAllText($urlPath, $urlContent)
            Write-Host "Shortcut created: GlanceRF.url (opens web page)"
        } else {
            # Desktop/browser mode: create .lnk to python run.py
            $pythonExe = if ($PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
            $lnkPath = Join-Path $desktop "GlanceRF.lnk"
            $ws = New-Object -ComObject WScript.Shell
            $sc = $ws.CreateShortcut($lnkPath)
            $sc.TargetPath = $pythonExe
            $sc.Arguments = "run.py"
            $sc.WorkingDirectory = $ProjectPath
            $sc.Description = "GlanceRF dashboard"
            $logoIco = Join-Path $ProjectPath "logos\logo.ico"
            $logoPng = Join-Path $ProjectPath "logos\logo.png"
            if (Test-Path $logoIco) { $sc.IconLocation = "$logoIco,0" } elseif (Test-Path $logoPng) { $sc.IconLocation = "$logoPng,0" }
            $sc.Save()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
            Write-Host "Shortcut created: GlanceRF.lnk"
        }
    } catch { Write-Host "Could not create shortcut: $_" }
}

# --- 5. Service (headless) or startup task (desktop/browser) ---
$serviceInstallOk = $false
if ($desktopMode -eq "headless") {
    Set-Location $ProjectPath
    Write-Host "Installing GlanceRF as Windows service (requires Administrator)..."
    try {
        if ($PythonCmd -eq "py -3") { & py -3 -m glancerf.desktop.glancerf_service install 2>&1 | Out-Null }
        else { & $PythonCmd -m glancerf.desktop.glancerf_service install 2>&1 | Out-Null }
        if ($LASTEXITCODE -eq 0) {
            $serviceInstallOk = $true
            & sc.exe config GlanceRF start= auto 2>$null
            Write-Host "Service installed and set to auto-start."
        }
    } catch { }
    if (-not $serviceInstallOk) {
        Write-Host "Service install failed (may need Administrator). To install manually: python -m glancerf.desktop.glancerf_service install"
    }
    if ($serviceInstallOk) {
        Start-Process -FilePath "net" -ArgumentList "start", "GlanceRF" -Verb RunAs -Wait -ErrorAction SilentlyContinue
        try {
            $pyExePath = if ($PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
            $pythonwPath = $pyExePath -replace "python\.exe$", "pythonw.exe"
            if (-not (Test-Path $pythonwPath)) { $pythonwPath = $pyExePath }
            $startupFolder = [Environment]::GetFolderPath("Startup")
            $ws = New-Object -ComObject WScript.Shell
            $sc = $ws.CreateShortcut((Join-Path $startupFolder "GlanceRF Tray.lnk"))
            $sc.TargetPath = $pythonwPath
            $sc.Arguments = "-m glancerf.desktop.tray_helper"
            $sc.WorkingDirectory = $ProjectPath
            $sc.Description = "GlanceRF tray icon"
            $logoIco = Join-Path $ProjectPath "logos\logo.ico"
            if (Test-Path $logoIco) { $sc.IconLocation = "$logoIco,0" }
            $sc.Save()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
            Start-Process -FilePath $pythonwPath -ArgumentList "-m glancerf.desktop.tray_helper" -WorkingDirectory $ProjectPath -WindowStyle Hidden
            Write-Host "Tray icon added to Startup and started."
        } catch { }
        Write-Host ""
        Write-Host "GlanceRF is running as a service. Open http://localhost:8080 in your browser."
    } else {
        Write-Host "Starting GlanceRF in this window..."
        if ($PythonCmd -eq "py -3") { & py -3 run.py } else { & $PythonCmd run.py }
    }
} else {
    $startupTaskCreated = $false
    if ($WantStartup) {
        try {
            $pyExePath = if ($PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
            $Action = New-ScheduledTaskAction -Execute $pyExePath -Argument "run.py" -WorkingDirectory $ProjectPath
            $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            Unregister-ScheduledTask -TaskName "GlanceRF" -ErrorAction SilentlyContinue
            Register-ScheduledTask -TaskName "GlanceRF" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
            $startupTaskCreated = $true
            Write-Host "Startup task created."
        } catch { Write-Host "Could not create startup task." }
    }
    Write-Host "Starting GlanceRF..."
    Set-Location $ProjectPath
    if ($WantStartup -and $startupTaskCreated) {
        try { Start-ScheduledTask -TaskName "GlanceRF" -ErrorAction Stop } catch { }
    }
    if ($PythonCmd -eq "py -3") { & py -3 run.py } else { & $PythonCmd run.py }
}
