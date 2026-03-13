#Requires -Version 5.1
# GlanceRF Windows installer - GUI version
# Main window opens first; checks for Python; prompts to install if missing.

$ErrorActionPreference = "Continue"
$ProgressPreference = 'SilentlyContinue'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# When running as EXE (PS2EXE), $PSScriptRoot may be empty
if (-not $PSScriptRoot) {
    try {
        $exePath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
        $PSScriptRoot = [System.IO.Path]::GetDirectoryName($exePath)
    } catch { }
}

# --- Resolve project path (validated in Add_Shown after form displays) ---
$ProjectPath = $null
if (Test-Path (Join-Path $PSScriptRoot "..\run.py")) {
    $ProjectPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
if (-not $ProjectPath -or -not (Test-Path (Join-Path $ProjectPath "run.py"))) {
    $ProjectPath = (Get-Location).Path
}

# Generate logo.ico from logo.png if missing (e.g. when run from GitHub zip)
$logoIcoPath = Join-Path $ProjectPath "logos\logo.ico"
$logoPngPath = Join-Path $ProjectPath "logos\logo.png"
$repoRoot = Join-Path $ProjectPath ".."
$buildLogoScript = Join-Path $repoRoot "Scripts\build_logo_ico.py"
if (-not (Test-Path $logoIcoPath) -and (Test-Path $logoPngPath) -and (Test-Path $buildLogoScript)) {
    try {
        Push-Location $repoRoot
        if (Get-Command python -ErrorAction SilentlyContinue) { python $buildLogoScript 2>$null | Out-Null }
        if ($LASTEXITCODE -ne 0 -and (Get-Command py -ErrorAction SilentlyContinue)) { py -3 $buildLogoScript 2>$null | Out-Null }
        Pop-Location
    } catch { Pop-Location -ErrorAction SilentlyContinue }
}

$PythonInstallVersion = "3.12.7"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# --- Mode selection dialog ---
function Show-ModeDialog {
    $dlg = New-Object System.Windows.Forms.Form
    $dlg.Text = "GlanceRF Installer"
    $dlg.Size = New-Object System.Drawing.Size(320, 150)
    $dlg.StartPosition = "CenterScreen"
    $dlg.FormBorderStyle = "FixedDialog"
    $dlg.TopMost = $true
    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Location = New-Object System.Drawing.Point(15, 15)
    $lbl.Size = New-Object System.Drawing.Size(280, 20)
    $lbl.Text = "How would you like to run GlanceRF?"
    $dlg.Controls.Add($lbl)
    $cmb = New-Object System.Windows.Forms.ComboBox
    $cmb.Location = New-Object System.Drawing.Point(15, 40)
    $cmb.Size = New-Object System.Drawing.Size(280, 21)
    $cmb.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
    [void]$cmb.Items.Add("Desktop app")
    [void]$cmb.Items.Add("Browser + Terminal")
    [void]$cmb.Items.Add("Terminal only")
    [void]$cmb.Items.Add("Service")
    $cmb.SelectedIndex = 0
    $dlg.Controls.Add($cmb)
    $btnOk = New-Object System.Windows.Forms.Button
    $btnOk.Location = New-Object System.Drawing.Point(225, 85)
    $btnOk.Size = New-Object System.Drawing.Size(70, 28)
    $btnOk.Text = "OK"
    $btnOk.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $dlg.Controls.Add($btnOk)
    $dlg.AcceptButton = $btnOk
    [void]$dlg.ShowDialog()
    return $cmb.SelectedItem.ToString()
}

# --- Progress helpers ---
function Update-Progress {
    param([string]$Message, [int]$Percent)
    $lblStatus.Text = $Message
    $progressBar.Value = [Math]::Min([Math]::Max($Percent, 0), 100)
    [System.Windows.Forms.Application]::DoEvents()
}

# Progress: 0-10 questions, 10-50 Python (if needed), 50-90 deps, 90-100 config/setup
# Advance-Progress: call after each post-deps step; $totalUnits and $unitsDone set in Add_Shown
function Advance-Progress {
    param([string]$Message)
    $script:unitsDone++
    $pct = if ($script:totalUnits -gt 0) { 90 + [int](($script:unitsDone / $script:totalUnits) * 10) } else { 100 }
    Update-Progress $Message $pct
}

# --- Find Python ---
function Find-Python {
    foreach ($try in @("py -3", "python3", "python")) {
        try {
            if ($try -eq "py -3") { & py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
            else { & $try -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null }
            if ($LASTEXITCODE -eq 0) { return $try }
        } catch { continue }
    }
    return $null
}

# --- Main form ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "GlanceRF Installer"
$form.Size = New-Object System.Drawing.Size(480, 220)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
# Set window/taskbar icon from logo.ico when available
$logoIco = $null
if ($ProjectPath) { $logoIco = Join-Path $ProjectPath "logos\logo.ico" }
if (-not $logoIco -or -not (Test-Path $logoIco)) { $logoIco = Join-Path (Join-Path $PSScriptRoot "..") "logos\logo.ico" }
if ($logoIco -and (Test-Path $logoIco)) {
    try { $form.Icon = [System.Drawing.Icon]::new($logoIco) } catch {}
}

$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Location = New-Object System.Drawing.Point(20, 20)
$lblTitle.Size = New-Object System.Drawing.Size(420, 24)
$lblTitle.Text = "GlanceRF Installer"
$lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($lblTitle)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Location = New-Object System.Drawing.Point(20, 55)
$lblStatus.Size = New-Object System.Drawing.Size(420, 20)
$lblStatus.MaximumSize = New-Object System.Drawing.Size(420, 0)
$lblStatus.AutoSize = $true
$lblStatus.Text = "Preparing..."
$lblStatus.ForeColor = [System.Drawing.Color]::DarkBlue
$form.Controls.Add($lblStatus)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20, 85)
$progressBar.Size = New-Object System.Drawing.Size(420, 23)
$progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous
$progressBar.Value = 0
$form.Controls.Add($progressBar)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Location = New-Object System.Drawing.Point(20, 130)
$btnCancel.Size = New-Object System.Drawing.Size(75, 32)
$btnCancel.Text = "Finish"
$btnCancel.Visible = $false  # Shown only when install completes (Cancel removed - can't cancel during blocking ops)
$form.Controls.Add($btnCancel)

$form.Add_FormClosed({ [System.Windows.Forms.Application]::Exit() })

# --- Python check runs after main window is shown ---
$PythonCmd = $null
$script:needPythonDownload = $false
$script:launchOnFinish = $null  # Scriptblock to run when user clicks Finish (launch GlanceRF)

$form.Add_Shown({
    # Let form paint immediately before heavy work (helps in Sandbox/VMs)
    [System.Windows.Forms.Application]::DoEvents()
    # Reset state (in case of relaunch in same session)
    $script:needPythonDownload = $false
    $script:PythonCmd = $null

    # Let the main window fully display first
    Update-Progress "Preparing..." 0
    Start-Sleep -Milliseconds 400

    # Validate run.py (main window is now visible)
    if (-not (Test-Path (Join-Path $ProjectPath "run.py"))) {
        [System.Windows.Forms.MessageBox]::Show("run.py not found. Run from Project folder or Project\installers.", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        $form.Close()
        return
    }

    # --- ALL QUESTIONS UP FRONT (before any long operations) ---
    Update-Progress "Answer a few questions..." 5

    # 1. Quick Python check
    $script:PythonCmd = Find-Python
    if (-not $script:PythonCmd) {
        $result = [System.Windows.Forms.MessageBox]::Show($form,
            "Python 3.8 or higher not found.`n`nDownload and install Python $PythonInstallVersion automatically?",
            "GlanceRF Installer",
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question,
            [System.Windows.Forms.MessageBoxDefaultButton]::Button2
        )
        if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
            $script:needPythonDownload = $true
        } else {
            [System.Windows.Forms.MessageBox]::Show($form, "Install Python from https://www.python.org/downloads/ (tick Add Python to PATH), then run this installer again.", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            $form.Close()
            return
        }
    }

    # 2. Mode selection
    $RunMode = Show-ModeDialog
    $desktopMode = "browser"
    if ($RunMode -eq "Desktop app") { $desktopMode = "desktop" }
    elseif ($RunMode -eq "Browser + Terminal") { $desktopMode = "browser" }
    elseif ($RunMode -eq "Terminal only") { $desktopMode = "terminal" }
    elseif ($RunMode -eq "Service") { $desktopMode = "headless" }

    # 3. Run at startup (modes 1, 2, 3 only; service auto-starts)
    $WantStartup = $false
    if ($desktopMode -ne "headless") {
        $r = [System.Windows.Forms.MessageBox]::Show($form, "Run GlanceRF at Windows logon?", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question, [System.Windows.Forms.MessageBoxDefaultButton]::Button1)
        $WantStartup = ($r -eq [System.Windows.Forms.DialogResult]::Yes)
    }

    # 4. Desktop shortcut (service mode = URL to browser; others = .lnk to run.py)
    $WantShortcut = $false
    $shortcutMsg = if ($desktopMode -eq "headless") { "Create a desktop shortcut to open GlanceRF in browser?" } else { "Create a shortcut on your desktop?" }
    $r = [System.Windows.Forms.MessageBox]::Show($form, $shortcutMsg, "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question, [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
    $WantShortcut = ($r -eq [System.Windows.Forms.DialogResult]::Yes)

    # --- LONG OPERATIONS (Python install, dependencies) ---

    if ($script:needPythonDownload) {
        Update-Progress "Downloading Python..." 12

        $is64 = [Environment]::Is64BitOperatingSystem
        $fileName = if ($is64) { "python-$PythonInstallVersion-amd64.exe" } else { "python-$PythonInstallVersion.exe" }
        $installerUrl = "https://www.python.org/ftp/python/$PythonInstallVersion/$fileName"
        $installerPath = Join-Path $env:TEMP "python-glancerf-installer-$([Guid]::NewGuid().ToString('N')).exe"
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
            $lastPct = -1
            do {
                $bytesRead = $respStream.Read($buffer, 0, $buffer.Length)
                if ($bytesRead -gt 0) {
                    $fileStream.Write($buffer, 0, $bytesRead)
                    $totalRead += $bytesRead
                    if ($totalBytes -gt 0) {
                        $pct = [int](($totalRead / $totalBytes) * 100)
                        if ($pct -ge $lastPct + 5 -or $pct -eq 100) {
                            $dlPct = 12 + [int]($pct * 0.28)
                            Update-Progress "Downloading Python... $pct%" $dlPct
                            $lastPct = $pct
                        }
                    }
                }
            } while ($bytesRead -gt 0)
            $fileStream.Close()
            $respStream.Close()
            $resp.Close()
        } catch {
            $btnCancel.Enabled = $true
            [System.Windows.Forms.MessageBox]::Show("Download failed: $_", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return
        }

        Update-Progress "Installing Python - An extra window will open. Note this can take a while to install." 42
        $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Marquee
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Seconds 5
        # Skip optional components to speed install: doc, TclTk/IDLE (we use PyQt), test suite, shortcuts
        $p = Start-Process -FilePath $installerPath -ArgumentList "/passive", "PrependPath=1", "InstallAllUsers=0", "Include_doc=0", "Include_tcltk=0", "Include_test=0", "Shortcuts=0" -Wait -PassThru
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        $progressBar.Style = [System.Windows.Forms.ProgressBarStyle]::Continuous

        if ($p.ExitCode -eq 0) {
            $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
            $script:PythonCmd = Find-Python
            if ($script:PythonCmd) {
                $btnCancel.Enabled = $true
                Update-Progress "Python installed. Installing dependencies..." 50
            } else {
                [System.Windows.Forms.MessageBox]::Show("Python was installed but is not yet in PATH. Close and reopen the installer, then run again.", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
                $form.Close()
            }
        } elseif ($p.ExitCode -eq 1618) {
            [System.Windows.Forms.MessageBox]::Show("Another installation is in progress. Wait a few minutes, then run again.", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            $form.Close()
        } else {
            [System.Windows.Forms.MessageBox]::Show("Python installation failed (exit $($p.ExitCode)). Install from https://www.python.org/downloads/", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            $form.Close()
        }
    } else {
        Update-Progress "Python found. Installing dependencies..." 50
    }

    # Build dependency list and compute total progress units (dynamic - scales with package count)
    $depPackages = @()
    if ($desktopMode -eq "desktop") {
        $desktopReq = Join-Path $ProjectPath "requirements\requirements-windows-desktop.txt"
        if (Test-Path $desktopReq) {
            $depPackages = (Get-Content $desktopReq | Where-Object { $_ -match "^\s*[a-zA-Z0-9_-]+" } | ForEach-Object { ($_ -split "==|>=|<=|~=")[0].Trim() })
        }
        if ($depPackages.Count -eq 0) { $depPackages = @("PyQt5", "PyQtWebEngine") }
    }
    if ($desktopMode -eq "browser" -or $desktopMode -eq "terminal" -or $desktopMode -eq "headless") {
        $headlessReq = Join-Path $ProjectPath "requirements\requirements-windows.txt"
        if (Test-Path $headlessReq) {
            $depPackages = (Get-Content $headlessReq | Where-Object { $_ -match "^\s*[a-zA-Z0-9_-]+" } | ForEach-Object { ($_ -split "==|>=|<=|~=")[0].Trim() })
        }
        if ($depPackages.Count -eq 0) { $depPackages = @("pywin32", "pystray", "Pillow") }
    }

    $script:totalUnits = [Math]::Max(1, $depPackages.Count + 1 + $(if ($desktopMode -eq "headless") { 2 } else { 0 }) + $(if ($WantShortcut) { 1 } else { 0 }) + $(if ($WantStartup -and $desktopMode -ne "headless") { 1 } else { 0 }))
    $script:unitsDone = 0

    # Install dependencies (50-90%)
    for ($i = 0; $i -lt $depPackages.Count; $i++) {
        $depPct = if ($depPackages.Count -gt 0) { 50 + [int]((($i + 1) / $depPackages.Count) * 40) } else { 90 }
        Update-Progress "Installing dependencies... ($($i + 1)/$($depPackages.Count)) ... $($depPackages[$i])" $depPct
        if ($script:PythonCmd -eq "py -3") { & py -3 -m pip install $depPackages[$i] -q 2>&1 | Out-Null }
        else { & $script:PythonCmd -m pip install $depPackages[$i] -q 2>&1 | Out-Null }
        if ($LASTEXITCODE -ne 0) {
            if ($script:PythonCmd -eq "py -3") { & py -3 -m pip install $depPackages[$i] 2>&1 | Out-Null }
            else { & $script:PythonCmd -m pip install $depPackages[$i] 2>&1 | Out-Null }
        }
        $script:unitsDone++
    }

    $configPath = Join-Path $ProjectPath "glancerf_config.json"
    $env:GLANCERF_CONFIG_PATH = $configPath
    $env:GLANCERF_DESKTOP_MODE = $desktopMode
    # Detect GPU state when desktop mode: Sandbox / software rendering -> disable_gpu for faster startup
    $disableGpu = "false"
    if ($desktopMode -eq "desktop") {
        try {
            $env:PYTHONPATH = $ProjectPath
            $detectOut = if ($script:PythonCmd -eq "py -3") {
                py -3 -c "from glancerf.desktop.gpu_detect import should_disable_gpu; print('true' if should_disable_gpu() else 'false')" 2>$null
            } else {
                & $script:PythonCmd -c "from glancerf.desktop.gpu_detect import should_disable_gpu; print('true' if should_disable_gpu() else 'false')" 2>$null
            }
            if ($detectOut -match "true") { $disableGpu = "true" }
        } catch {}
    }
    $env:GLANCERF_DISABLE_GPU_DETECTED = $disableGpu
    $configScript = "import json, os; p=os.environ.get('GLANCERF_CONFIG_PATH',''); c=json.load(open(p,'r',encoding='utf-8')) if os.path.exists(p) else {}; c['desktop_mode']=os.environ.get('GLANCERF_DESKTOP_MODE','browser'); c['disable_gpu']=(os.environ.get('GLANCERF_DISABLE_GPU_DETECTED','false').lower()=='true'); json.dump(c, open(p,'w',encoding='utf-8'), indent=2)"
    if ($script:PythonCmd -eq "py -3") { & py -3 -c $configScript } else { & $script:PythonCmd -c $configScript }
    Advance-Progress "Saving config..."

    # Headless (Service) mode: install service, tray
    $serviceInstallOk = $false
    if ($desktopMode -eq "headless") {
        Update-Progress "Installing Windows service (may require Administrator)..." (90 + [int](($script:unitsDone / $script:totalUnits) * 10))
        Set-Location $ProjectPath
        try {
            if ($script:PythonCmd -eq "py -3") { & py -3 -m glancerf.desktop.glancerf_service install 2>&1 | Out-Null }
            else { & $script:PythonCmd -m glancerf.desktop.glancerf_service install 2>&1 | Out-Null }
            if ($LASTEXITCODE -eq 0) {
                $serviceInstallOk = $true
                & sc.exe config GlanceRF start= auto 2>$null
            }
        } catch {}
        $script:unitsDone++

        if (-not $serviceInstallOk) {
            [System.Windows.Forms.MessageBox]::Show("Service install failed (may require Administrator). Run this installer as Administrator, or install manually: cd to Project folder, then run: python -m glancerf.desktop.glancerf_service install", "GlanceRF Installer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
        }
        if ($serviceInstallOk) {
            Update-Progress "Configuring service and tray (will start when you click Finish)..." (90 + [int](($script:unitsDone / $script:totalUnits) * 10))
            # Create tray shortcut in Startup folder now (so it runs at next logon)
            try {
                $pyExePath = if ($script:PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $script:PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
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
            } catch {}
            $script:launchOnFinish = {
                Start-Process -FilePath "net" -ArgumentList "start", "GlanceRF" -Verb RunAs -Wait -ErrorAction SilentlyContinue
                try {
                    $pyExePath = if ($script:PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $script:PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
                    $pythonwPath = $pyExePath -replace "python\.exe$", "pythonw.exe"
                    if (-not (Test-Path $pythonwPath)) { $pythonwPath = $pyExePath }
                    Start-Process -FilePath $pythonwPath -ArgumentList "-m glancerf.desktop.tray_helper" -WorkingDirectory $ProjectPath -WindowStyle Hidden
                } catch {}
            }
            $script:unitsDone++
        }
    }

    # Startup task for desktop and browser modes (run at logon)
    $startupTaskCreated = $false
    if ($WantStartup -and $desktopMode -ne "headless") {
        Update-Progress "Creating startup task..." (90 + [int](($script:unitsDone / $script:totalUnits) * 10))
        try {
            Import-Module ScheduledTasks -ErrorAction SilentlyContinue
            $pyExePath = if ($script:PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $script:PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
            $exeForTask = $pyExePath
            $Action = New-ScheduledTaskAction -Execute $exeForTask -Argument "run.py" -WorkingDirectory $ProjectPath
            $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            Unregister-ScheduledTask -TaskName "GlanceRF" -ErrorAction SilentlyContinue
            Register-ScheduledTask -TaskName "GlanceRF" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
            $startupTaskCreated = $true
        } catch {}
        $script:unitsDone++
    }

    # Desktop shortcut
    if ($WantShortcut) {
        Update-Progress "Creating desktop shortcut..." (90 + [int](($script:unitsDone / $script:totalUnits) * 10))
        try {
            $desktop = [Environment]::GetFolderPath("Desktop")
            if ($desktopMode -eq "headless") {
                # Service mode: create URL shortcut to web page (not Python)
                $port = 8080
                try {
                    $configObj = Get-Content $configPath -Raw | ConvertFrom-Json
                    if ($configObj -and $configObj.port) { $port = $configObj.port }
                } catch {}
                $urlPath = Join-Path $desktop "GlanceRF.url"
                $urlContent = "[InternetShortcut]`nURL=http://localhost:$port`n"
                $logoIco = Join-Path $ProjectPath "logos\logo.ico"
                if (Test-Path $logoIco) {
                    $urlContent += "IconIndex=0`nIconFile=$logoIco`n"
                }
                [System.IO.File]::WriteAllText($urlPath, $urlContent)
            } else {
                # Desktop/browser mode: create .lnk to python run.py
                $pythonExe = if ($script:PythonCmd -eq "py -3") { (py -3 -c "import sys; print(sys.executable)" 2>$null).Trim() } else { (& $script:PythonCmd -c "import sys; print(sys.executable)" 2>$null).Trim() }
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
            }
        } catch {}
        $script:unitsDone++
    }

    $completeMsg = "Install complete."
    if ($desktopMode -eq "headless" -and $serviceInstallOk) {
        $configObj = $null
        try { $configObj = Get-Content $configPath -Raw | ConvertFrom-Json } catch {}
        $port = if ($configObj -and $configObj.port) { $configObj.port } else { 8080 }
        $completeMsg = "Install complete. GlanceRF will start when you click Finish. Open http://localhost:$port in your browser. Click the tray icon to open GlanceRF."
    } elseif ($WantStartup -and $startupTaskCreated) {
        $script:launchOnFinish = {
            try { Start-ScheduledTask -TaskName "GlanceRF" -ErrorAction Stop } catch {}
        }
        $completeMsg = "Install complete. GlanceRF will start when you click Finish (and will run at logon)."
    }
    Update-Progress $completeMsg 100

    $btnCancel.Visible = $true
    $btnCancel.Enabled = $true
})

$btnCancel.Add_Click({
    if ($script:launchOnFinish) {
        $btnCancel.Enabled = $false
        $lblStatus.Text = "Starting GlanceRF..."
        [System.Windows.Forms.Application]::DoEvents()
        try { & $script:launchOnFinish } catch {}
    }
    $form.Close()
})

[void]$form.ShowDialog()
exit 0
