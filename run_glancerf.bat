@echo off
setlocal
cd /d "%~dp0"

set PYCMD=
echo Checking Python...
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
    echo Python 3.8 or higher is required but not found or too old.
    echo Please install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo Download the Windows installer, run it, and tick "Add Python to PATH".
    echo Then run this batch file again.
    echo.
    pause
    exit /b 1
)

echo Python OK.
echo.

echo Installing requirements...
%PYCMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install requirements.
    echo.
    pause
    exit /b 1
)

echo Verifying (import fastapi)...
%PYCMD% -c "import fastapi" 2>nul
if errorlevel 1 (
    echo.
    echo Requirements did not install correctly for this Python.
    echo Open a terminal in this folder and run:
    echo   %PYCMD% -m pip install -r requirements.txt
    echo Then run this batch file again.
    echo.
    pause
    exit /b 1
)

echo Requirements OK.
echo.
echo Starting GlanceRF...
echo.
%PYCMD% run.py
if errorlevel 1 (
    echo.
    pause
    exit /b 1
)

endlocal
