#!/bin/bash
# GlanceRF macOS installer: checks/installs Python (including via Homebrew),
# requirements, config, optional desktop shortcut and launchd run-at-login.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "GlanceRF macOS installer"
echo "------------------------"
echo "Detected: macOS ($(uname -s))"
echo ""

# --- Project path ---
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

# --- 1. Check / install Python ---
PYTHON3=""
for cmd in python3 python3.12 python3.11 python3.10 python; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON3="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON3" ]; then
    echo "Python 3.8 or higher not found."
    read -r -p "Try to install Python via Homebrew? (y/n) " install
    if [ "$install" = "y" ] || [ "$install" = "Y" ]; then
        if command -v brew &>/dev/null; then
            brew install python
            # Homebrew python: prefer python3 from PATH or (brew --prefix python)/bin/python3
            if command -v python3 &>/dev/null && python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
                PYTHON3="python3"
            else
                BREW_PY="$(brew --prefix python 2>/dev/null)/bin/python3"
                [ -x "$BREW_PY" ] && PYTHON3="$BREW_PY" || PYTHON3="python3"
            fi
        else
            echo "Homebrew not found. Install from https://brew.sh or install Python from https://www.python.org/downloads/"
            exit 1
        fi
    else
        echo "Install Python from https://www.python.org/downloads/ or run: brew install python"
        exit 1
    fi
fi
echo "Python OK: $PYTHON3"
echo ""

# --- 2. Check / install requirements ---
echo "Checking requirements..."
REQUIREMENTS_PATH="$PROJECT_DIR/requirements.txt"
if ! "$PYTHON3" -c "import fastapi" 2>/dev/null; then
    echo "Installing requirements..."
    "$PYTHON3" -m pip install -r "$REQUIREMENTS_PATH"
    if [ $? -ne 0 ]; then
        echo "Failed to install requirements."
        exit 1
    fi
fi
echo "Requirements OK."
echo ""

# --- 3. Run on startup? ---
WANT_STARTUP=false
read -r -p "Run GlanceRF at logon? (y/n) " startup_resp
case "$startup_resp" in
    y|Y) WANT_STARTUP=true ;;
esac

# --- 4. Desktop or headless? ---
WANT_HEADLESS=false
read -r -p "Run in desktop (window) or headless (browser only)? (desktop/headless) " mode_resp
case "$mode_resp" in
    headless|Headless|HEADLESS) WANT_HEADLESS=true ;;
esac

# --- 5. Update config ---
USE_DESKTOP="True"
[ "$WANT_HEADLESS" = true ] && USE_DESKTOP="False"
export GLANCERF_PROJECT="$PROJECT_DIR"
"$PYTHON3" -c "
import json, os
p = os.path.join(os.environ.get('GLANCERF_PROJECT',''), 'glancerf_config.json')
if os.path.exists(p):
    with open(p,'r',encoding='utf-8') as f: c = json.load(f)
else:
    c = {'port':8080,'readonly_port':8081,'use_desktop':True,'first_run':True,'max_grid_scale':10,'grid_columns':3,'grid_rows':3,'aspect_ratio':'16:9','orientation':'landscape','layout':[['','',''],['','',''],['','','']],'cell_spans':{},'module_settings':{}}
c['use_desktop'] = $USE_DESKTOP
with open(p,'w',encoding='utf-8') as f: json.dump(c, f, indent=2)
" || true
echo "Config set to $([ "$WANT_HEADLESS" = true ] && echo 'headless' || echo 'desktop')."
echo ""

# --- 6. Desktop shortcut? ---
WANT_SHORTCUT=false
read -r -p "Create a shortcut on your desktop? (y/n) " shortcut_resp
case "$shortcut_resp" in
    y|Y) WANT_SHORTCUT=true ;;
esac

if [ "$WANT_SHORTCUT" = true ]; then
    PYTHON_EXE="$("$PYTHON3" -c "import sys; print(sys.executable)")"
    DESKTOP_DIR="$HOME/Desktop"
    mkdir -p "$DESKTOP_DIR"
    SHORTCUT_FILE="$DESKTOP_DIR/GlanceRF.command"
    cat > "$SHORTCUT_FILE" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
exec "$PYTHON_EXE" run.py
EOF
    chmod +x "$SHORTCUT_FILE"
    echo "Shortcut created: $SHORTCUT_FILE (double-click to run GlanceRF)"
    echo ""
fi

# --- 7. Create startup job (launchd) if requested ---
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS/com.glancerf.plist"
LOG_FILE="$PROJECT_DIR/glancerf.log"

if [ "$WANT_STARTUP" = true ]; then
    PYTHON_PATH="$(command -v $PYTHON3)"
    mkdir -p "$LAUNCH_AGENTS"
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glancerf</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
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
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"
    echo "Startup agent installed: $PLIST_FILE"
    echo "  Log file: $LOG_FILE"
    echo ""
fi

# --- 8. Run now or start via launchd ---
if [ "$WANT_STARTUP" = true ]; then
    echo "GlanceRF is set to run at logon and has been started now."
    echo "  Stop:  launchctl unload $PLIST_FILE"
    echo "  Start: launchctl load $PLIST_FILE"
else
    echo "Starting GlanceRF..."
    cd "$PROJECT_DIR"
    exec "$PYTHON3" run.py
fi
