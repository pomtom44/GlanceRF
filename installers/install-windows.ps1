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
    $install = Read-Host "Try to install Python via winget? (Y/N)"
    if ($install -eq "Y" -or $install -eq "y") {
        try {
            winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
            Write-Host "Python installed. Please close and reopen PowerShell, then run this script again."
            exit 0
        } catch {
            Write-Host "winget install failed. Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
            exit 1
        }
    } else {
        Write-Host "Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this script again."
        exit 1
    }
}

Write-Host "Python OK: $PythonCmd"

# --- 2. Check / install requirements ---
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

# --- 3. Run on startup? ---
$WantStartup = $false
$startupResp = Read-Host "Run GlanceRF at Windows logon? (Y/N)"
if ($startupResp -eq "Y" -or $startupResp -eq "y") { $WantStartup = $true }

# --- 4. Desktop or headless? ---
$WantHeadless = $false
$modeResp = Read-Host "Run in desktop (window) or headless (browser only)? (desktop/headless)"
if ($modeResp -match "headless") { $WantHeadless = $true }

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

# --- 5. Desktop shortcut? ---
$WantShortcut = $false
$shortcutResp = Read-Host "Create a shortcut on your desktop? (Y/N)"
if ($shortcutResp -eq "Y" -or $shortcutResp -eq "y") { $WantShortcut = $true }

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
        $sc.Save()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ws) | Out-Null
        Write-Host "Shortcut created on desktop: GlanceRF.lnk"
    } catch {
        Write-Host "Could not create shortcut: $_"
    }
}

# --- 7. Create startup task if requested ---
if ($WantStartup) {
    $TaskName = "GlanceRF"
    $pyExe = if ($PythonCmd -eq "py -3") { "py -3" } else { $PythonCmd }
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"cd /d `"$ProjectPath`" && $pyExe run.py`"" -WorkingDirectory $ProjectPath -WindowStyle Hidden
    $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    Unregister-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
    Write-Host "Startup task created. GlanceRF will run at logon."
}

# --- 8. Run now or start via task ---
if ($WantStartup) {
    Write-Host "Starting GlanceRF now (startup task will also run at next logon)..."
    Start-ScheduledTask -TaskName "GlanceRF"
    Write-Host "Started. To stop: Unregister-ScheduledTask -TaskName GlanceRF"
} else {
    Write-Host "Starting GlanceRF..."
    Set-Location $ProjectPath
    if ($PythonCmd -eq "py -3") {
        & py -3 run.py
    } else {
        & $PythonCmd run.py
    }
}
