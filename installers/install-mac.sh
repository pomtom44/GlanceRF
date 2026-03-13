#!/bin/bash
# GlanceRF macOS installer - text-based, user inputs
# Mirrors Windows/Linux installer: mode selection, shortcut, dependencies, config, launchd (headless/startup)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# macOS only
if [ "$(uname -s)" != "Darwin" ]; then
    echo "This installer is for macOS only."
    exit 1
fi

echo ""
echo "=========================================="
echo "  GlanceRF macOS Installer"
echo "=========================================="
echo ""
echo "Detected: macOS ($(uname -s))"
echo ""

# --- Resolve project path ---
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ ! -f "$PROJECT_DIR/run.py" ]; then
    PROJECT_DIR="$(pwd)"
fi
if [ ! -f "$PROJECT_DIR/run.py" ]; then
    echo "Error: run.py not found. Run this script from the Project folder or Project/installers."
    exit 1
fi
echo "Project folder: $PROJECT_DIR"
echo ""

# --- Desktop vs Server detection ---
# SSH session = server mode (no display); local Terminal = desktop mode
HAS_DISPLAY="yes"
if [ -n "${SSH_CONNECTION:-}" ] || [ -n "${SSH_TTY:-}" ]; then
    HAS_DISPLAY="no"
fi

if [ "$HAS_DISPLAY" = "yes" ]; then
    echo "Desktop mode detected (local session)."
    echo ""
    echo "How would you like to run GlanceRF?"
    echo "  1) Terminal + Browser - Terminal visible, opens browser"
    echo "  2) Terminal only      - Terminal visible, no browser"
    echo "  3) Service           - Runs in background (launchd)"
    echo ""
    read -r -p "Enter choice (1/2/3) [1]: " mode_choice
    mode_choice="${mode_choice:-1}"
    case "$mode_choice" in
        2) DESKTOP_MODE="terminal" ;;
        3) DESKTOP_MODE="headless" ;;
        *) DESKTOP_MODE="browser" ;;
    esac

    # Desktop shortcut and run at logon (modes 1 and 2 only)
    WANT_SHORTCUT=false
    WANT_STARTUP=false
    if [ "$DESKTOP_MODE" != "headless" ]; then
        read -r -p "Create a shortcut on your desktop? (y/n) [n]: " shortcut_resp
        case "$shortcut_resp" in
            y|Y) WANT_SHORTCUT=true ;;
        esac
        read -r -p "Run GlanceRF at logon? (y/n) [n]: " startup_resp
        case "$startup_resp" in
            y|Y) WANT_STARTUP=true ;;
        esac
    else
        # Service mode: desktop shortcut to web page only
        read -r -p "Create a desktop shortcut to open GlanceRF in browser? (y/n) [n]: " shortcut_resp
        case "$shortcut_resp" in
            y|Y) WANT_SHORTCUT=true ;;
        esac
    fi
else
    echo "Server mode detected (SSH session)."
    echo ""
    read -r -p "Install as a service (runs in background)? (y/n) [y]: " service_resp
    service_resp="${service_resp:-y}"
    case "$service_resp" in
        y|Y) INSTALL_AS_SERVICE=true ;;
        *) INSTALL_AS_SERVICE=false ;;
    esac
    DESKTOP_MODE="headless"
    WANT_SHORTCUT=false
    WANT_STARTUP=false
fi
echo ""

# 1. Quick Python check
PYTHON3=""
for cmd in python3 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON3="$cmd"
            break
        fi
    fi
done

NEED_PYTHON_INSTALL=false
if [ -z "$PYTHON3" ]; then
    echo "Python 3.8 or higher not found."
    read -r -p "Try to install Python via Homebrew? (y/n) " install
    if [ "$install" = "y" ] || [ "$install" = "Y" ]; then
        NEED_PYTHON_INSTALL=true
    else
        echo "Install Python from https://www.python.org/downloads/ or run: brew install python"
        exit 1
    fi
fi

# --- PROCESSING (Python install, venv, dependencies, config, etc.) ---
echo "Installing... (this may take a few minutes)"
echo ""

# 1. Install Python via Homebrew if needed
if [ "$NEED_PYTHON_INSTALL" = true ]; then
    if command -v brew &>/dev/null; then
        brew install python
        if command -v python3 &>/dev/null && python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON3="python3"
        else
            BREW_PY="$(brew --prefix python 2>/dev/null)/bin/python3"
            [ -x "$BREW_PY" ] && PYTHON3="$BREW_PY" || PYTHON3="python3"
        fi
    else
        echo "Homebrew not found. Install from https://brew.sh or Python from https://www.python.org/downloads/"
        exit 1
    fi
fi
echo "Python OK: $PYTHON3"

if ! "$PYTHON3" -c "import ensurepip" 2>/dev/null; then
    echo "Python venv module not available. Install python3 (brew install python) and run again."
    exit 1
fi
echo ""

# --- 2. Create venv ---
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ -d "$VENV_DIR" ] && ! "$VENV_PYTHON" -m pip --version &>/dev/null 2>&1; then
    echo "Removing broken venv; will recreate."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    if ! "$PYTHON3" -m venv "$VENV_DIR"; then
        echo "Failed to create venv."
        exit 1
    fi
fi
echo ""

# --- 3. Install dependencies (based on mode) ---
echo "Installing dependencies..."

if [ "$DESKTOP_MODE" = "headless" ]; then
    HEADLESS_REQ="$PROJECT_DIR/requirements/requirements-mac.txt"
    if [ -f "$HEADLESS_REQ" ]; then
        "$VENV_PYTHON" -m pip install -r "$HEADLESS_REQ" -q 2>/dev/null || "$VENV_PYTHON" -m pip install -r "$HEADLESS_REQ"
    else
        "$VENV_PYTHON" -m pip install pystray Pillow -q 2>/dev/null || "$VENV_PYTHON" -m pip install pystray Pillow
    fi
else
    # browser or terminal mode
    HEADLESS_REQ="$PROJECT_DIR/requirements/requirements-mac.txt"
    if [ -f "$HEADLESS_REQ" ]; then
        "$VENV_PYTHON" -m pip install -r "$HEADLESS_REQ" -q 2>/dev/null || "$VENV_PYTHON" -m pip install -r "$HEADLESS_REQ"
    else
        "$VENV_PYTHON" -m pip install pystray Pillow -q 2>/dev/null || "$VENV_PYTHON" -m pip install pystray Pillow
    fi
fi
echo "Dependencies OK."
echo ""

# --- 4. Update config ---
echo "Saving config..."
CONFIG_PATH="$PROJECT_DIR/glancerf_config.json"
export GLANCERF_PROJECT="$PROJECT_DIR"
export GLANCERF_DESKTOP_MODE="$DESKTOP_MODE"
"$VENV_PYTHON" -c "
import json, os
p = os.path.join(os.environ.get('GLANCERF_PROJECT',''), 'glancerf_config.json')
c = json.load(open(p, 'r', encoding='utf-8')) if os.path.exists(p) else {'port': 8080, 'desktop_mode': 'browser'}
c['desktop_mode'] = os.environ.get('GLANCERF_DESKTOP_MODE', 'browser')
json.dump(c, open(p, 'w', encoding='utf-8'), indent=2)
" 2>/dev/null || true
echo "Config: desktop_mode=$DESKTOP_MODE"
echo ""

# --- 5. Desktop shortcut ---
if [ "$WANT_SHORTCUT" = true ] && [ "$HAS_DISPLAY" = "yes" ]; then
    DESKTOP_DIR="$HOME/Desktop"
    mkdir -p "$DESKTOP_DIR"
    if [ "$DESKTOP_MODE" = "headless" ]; then
        # Service mode: shortcut opens browser to web page
        PORT="$("$VENV_PYTHON" -c "import json; c=json.load(open('$PROJECT_DIR/glancerf_config.json')); print(c.get('port',8080))" 2>/dev/null || echo "8080")"
        SHORTCUT_FILE="$DESKTOP_DIR/GlanceRF.command"
        cat > "$SHORTCUT_FILE" << EOF
#!/bin/bash
open "http://localhost:$PORT"
EOF
        chmod +x "$SHORTCUT_FILE"
        echo "Shortcut created: $SHORTCUT_FILE (opens browser)"
    else
        # Terminal + Browser or Terminal only: shortcut runs GlanceRF
        SHORTCUT_FILE="$DESKTOP_DIR/GlanceRF.command"
        cat > "$SHORTCUT_FILE" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
exec "$VENV_PYTHON" run.py
EOF
        chmod +x "$SHORTCUT_FILE"
        echo "Shortcut created: $SHORTCUT_FILE (double-click to run)"
    fi
    echo ""
fi

# --- 6. Headless: launchd service + tray ---
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST_SERVER="$LAUNCH_AGENTS/com.glancerf.plist"
PLIST_TRAY="$LAUNCH_AGENTS/com.glancerf.tray.plist"
LOG_FILE="$PROJECT_DIR/glancerf.log"

# Install service: always for desktop headless; only when user said yes for server mode
INSTALL_SERVICE=false
if [ "$DESKTOP_MODE" = "headless" ]; then
    if [ "$HAS_DISPLAY" = "yes" ]; then
        INSTALL_SERVICE=true
    else
        [ "${INSTALL_AS_SERVICE:-false}" = "true" ] && INSTALL_SERVICE=true
    fi
fi

if [ "$INSTALL_SERVICE" = true ]; then
    mkdir -p "$LAUNCH_AGENTS"
    VENV_PYTHON_ABS="$(cd "$PROJECT_DIR" && "$VENV_PYTHON" -c "import sys; print(sys.executable)")"

    # Server plist
    cat > "$PLIST_SERVER" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glancerf</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON_ABS</string>
        <string>run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF

    launchctl unload "$PLIST_SERVER" 2>/dev/null || true
    launchctl load "$PLIST_SERVER"
    echo "LaunchAgent (server): $PLIST_SERVER"

    # Tray plist (only when display available)
    if [ "$HAS_DISPLAY" = "yes" ]; then
        cat > "$PLIST_TRAY" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glancerf.tray</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON_ABS</string>
        <string>-m</string>
        <string>glancerf.desktop.tray_helper</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
        launchctl unload "$PLIST_TRAY" 2>/dev/null || true
        launchctl load "$PLIST_TRAY"
        echo "LaunchAgent (tray): $PLIST_TRAY"
    fi
    echo ""
fi

# --- 7. Startup at logon (for terminal+browser and terminal-only modes) ---
if [ "$WANT_STARTUP" = true ] && [ "$DESKTOP_MODE" != "headless" ]; then
    mkdir -p "$LAUNCH_AGENTS"
    VENV_PYTHON_ABS="$(cd "$PROJECT_DIR" && "$VENV_PYTHON" -c "import sys; print(sys.executable)")"
    cat > "$PLIST_SERVER" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glancerf</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON_ABS</string>
        <string>run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
EOF
    launchctl unload "$PLIST_SERVER" 2>/dev/null || true
    launchctl load "$PLIST_SERVER"
    echo "Startup at logon enabled: $PLIST_SERVER"
    echo "  Log file: $LOG_FILE"
    echo ""
fi

# --- 8. Complete and run ---
echo "=========================================="
echo "  Install complete."
echo "=========================================="
echo ""

if [ "$INSTALL_SERVICE" = true ]; then
    PORT="$("$VENV_PYTHON" -c "import json; c=json.load(open('$PROJECT_DIR/glancerf_config.json')); print(c.get('port',8080))" 2>/dev/null || echo "8080")"
    echo "GlanceRF is running. Open http://localhost:$PORT in your browser."
    if [ "$HAS_DISPLAY" = "yes" ]; then
        echo "Tray icon started. It will also start at next logon."
    fi
    echo ""
    echo "  Stop server:  launchctl unload $PLIST_SERVER"
    echo "  Start server: launchctl load $PLIST_SERVER"
    echo ""
elif [ "$WANT_STARTUP" = true ]; then
    echo "GlanceRF started. It will also run at next logon."
    echo "  Stop:  launchctl unload $PLIST_SERVER"
    echo "  Start: launchctl load $PLIST_SERVER"
    echo ""
else
    echo "Starting GlanceRF..."
    cd "$PROJECT_DIR"
    exec "$VENV_PYTHON" run.py
fi
