@echo off
setlocal
cd /d "%~dp0"

set PYCMD=
echo Testing Python...
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
if not errorlevel 1 (
    set PYCMD=py -3
)
if not defined PYCMD (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
    if not errorlevel 1 (
        set PYCMD=python
    )
)
if not defined PYCMD (
    echo.
    echo Python 3.8 or higher was not found or is too old.
    echo Please install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo Download the Windows installer, run it, and tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo.
%PYCMD% --version
echo.
echo Python is installed and working properly.
echo You can continue with the quickstart (install dependencies, then run GlanceRF).
echo.
pause
endlocal
