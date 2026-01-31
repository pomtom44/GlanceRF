<#
Script: install-windows-task.ps1
Created by:
Created Date:
Modified By:
Modified Date:
Description: Creates a Windows Task Scheduler task to run GlanceRF at user logon.
             Run from the Project folder (the folder that contains run.py).
#>

# Project folder: the directory that contains run.py, glancerf, glancerf_config.json
$ProjectPath = (Get-Location).Path
if (-not (Test-Path -Path (Join-Path $ProjectPath "run.py"))) {
    Write-Host "Error: run.py not found in current directory. Run this script from the Project folder (e.g. cd C:\Path\To\Project)."
    exit 1
}

$TaskName = "GlanceRF"
$BatchPath = Join-Path $ProjectPath "run_glancerf.bat"
if (Test-Path $BatchPath) {
    $Action = New-ScheduledTaskAction -Execute $BatchPath -WorkingDirectory $ProjectPath -WindowStyle Hidden
} else {
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"cd /d `"$ProjectPath`" && py -3 run.py`"" -WorkingDirectory $ProjectPath -WindowStyle Hidden
}
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Write-Host "Creating scheduled task '$TaskName' to run GlanceRF at logon."
Write-Host "Project path: $ProjectPath"
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled."
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
Write-Host "Task created. GlanceRF will start when you log on."
Write-Host "To remove: Unregister-ScheduledTask -TaskName 'GlanceRF' -Confirm:`$false"
Write-Host "To show a console window instead of hidden, edit this script and change -WindowStyle Hidden to -WindowStyle Normal."
