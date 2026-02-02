@echo off
setlocal
cd /d "%~dp0"
echo Running GlanceRF installer...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"
if errorlevel 1 (
    echo.
    echo Installer finished with an error. See messages above.
    pause
)
endlocal
