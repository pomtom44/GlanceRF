#!/bin/bash
# GlanceRF Linux installer: detects distribution (Debian/Ubuntu, Fedora/RHEL, Arch, etc.),
# then runs the appropriate install method for that distro.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "GlanceRF Linux installer"
echo "------------------------"
echo ""

# --- Distro detection (using /etc/os-release when available) ---
DISTRO_ID=""
DISTRO_ID_LIKE=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-}"
    DISTRO_ID_LIKE="${ID_LIKE:-}"
fi

# Classify into: debian | fedora | rhel_yum | arch | suse | unknown
# and set PKG_UPDATE + PKG_INSTALL_PYTHON for "install Python via package manager"
PKG_UPDATE=""
PKG_INSTALL_PYTHON=""
DISTRO_NAME=""

case "${DISTRO_ID}" in
    debian|ubuntu|linuxmint|pop|elementary|raspbian)
        DISTRO_NAME="Debian/Ubuntu (apt)"
        PKG_UPDATE="sudo apt-get update"
        PKG_INSTALL_PYTHON="sudo apt-get install -y python3 python3-pip python3-venv"
        ;;
    fedora|rhel|centos|rocky|almalinux|ol)
        if command -v dnf &>/dev/null; then
            DISTRO_NAME="Fedora/RHEL (dnf)"
            PKG_UPDATE="sudo dnf check-update || true"
            PKG_INSTALL_PYTHON="sudo dnf install -y python3 python3-pip"
        else
            DISTRO_NAME="RHEL/CentOS (yum)"
            PKG_UPDATE="sudo yum check-update || true"
            PKG_INSTALL_PYTHON="sudo yum install -y python3 python3-pip"
        fi
        ;;
    arch|manjaro|endeavouros)
        DISTRO_NAME="Arch (pacman)"
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL_PYTHON="sudo pacman -S --noconfirm python python-pip"
        ;;
    opensuse*|sles)
        DISTRO_NAME="openSUSE/SLE (zypper)"
        PKG_UPDATE="sudo zypper refresh"
        PKG_INSTALL_PYTHON="sudo zypper install -y python3 python3-pip"
        ;;
    *)
        # Fallback: try ID_LIKE or probe for known package managers
        case "${DISTRO_ID_LIKE}" in
            *debian*|*ubuntu*)
                DISTRO_NAME="Debian-like (apt)"
                PKG_UPDATE="sudo apt-get update"
                PKG_INSTALL_PYTHON="sudo apt-get install -y python3 python3-pip python3-venv"
                ;;
            *rhel*|*fedora*)
                if command -v dnf &>/dev/null; then
                    DISTRO_NAME="Fedora/RHEL-like (dnf)"
                    PKG_UPDATE="sudo dnf check-update || true"
                    PKG_INSTALL_PYTHON="sudo dnf install -y python3 python3-pip"
                else
                    DISTRO_NAME="RHEL-like (yum)"
                    PKG_UPDATE="sudo yum check-update || true"
                    PKG_INSTALL_PYTHON="sudo yum install -y python3 python3-pip"
                fi
                ;;
            *arch*)
                DISTRO_NAME="Arch-like (pacman)"
                PKG_UPDATE="sudo pacman -Sy"
                PKG_INSTALL_PYTHON="sudo pacman -S --noconfirm python python-pip"
                ;;
            *)
                if [ -f /etc/debian_version ]; then
                    DISTRO_NAME="Debian-based (apt)"
                    PKG_UPDATE="sudo apt-get update"
                    PKG_INSTALL_PYTHON="sudo apt-get install -y python3 python3-pip python3-venv"
                elif [ -f /etc/redhat-release ]; then
                    if command -v dnf &>/dev/null; then
                        DISTRO_NAME="Fedora/RHEL (dnf)"
                        PKG_UPDATE="sudo dnf check-update || true"
                        PKG_INSTALL_PYTHON="sudo dnf install -y python3 python3-pip"
                    else
                        DISTRO_NAME="RHEL (yum)"
                        PKG_UPDATE="sudo yum check-update || true"
                        PKG_INSTALL_PYTHON="sudo yum install -y python3 python3-pip"
                    fi
                elif command -v pacman &>/dev/null; then
                    DISTRO_NAME="Arch (pacman)"
                    PKG_UPDATE="sudo pacman -Sy"
                    PKG_INSTALL_PYTHON="sudo pacman -S --noconfirm python python-pip"
                elif command -v zypper &>/dev/null; then
                    DISTRO_NAME="openSUSE (zypper)"
                    PKG_UPDATE="sudo zypper refresh"
                    PKG_INSTALL_PYTHON="sudo zypper install -y python3 python3-pip"
                else
                    DISTRO_NAME="unknown (install Python manually if needed)"
                fi
                ;;
        esac
        ;;
esac

echo "Detected distro: $DISTRO_NAME"
if [ -n "$DISTRO_ID" ]; then
    echo "  (/etc/os-release ID: $DISTRO_ID)"
fi
echo ""

if [ -z "$PKG_INSTALL_PYTHON" ]; then
    echo "No package manager detected for automatic Python install."
    echo "Install Python 3.8+ and pip yourself, then run this script again."
    echo ""
fi

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
    if [ -z "$PKG_INSTALL_PYTHON" ]; then
        echo "Python 3.8 or higher not found. Install it from your distro or https://www.python.org/downloads/"
        exit 1
    fi
    echo "Python 3.8 or higher not found."
    read -r -p "Install Python via $DISTRO_NAME? (y/n) " install
    if [ "$install" = "y" ] || [ "$install" = "Y" ]; then
        [ -n "$PKG_UPDATE" ] && $PKG_UPDATE
        $PKG_INSTALL_PYTHON
        PYTHON3="python3"
        # Arch uses 'python' not 'python3' for the binary
        if [ "$DISTRO_NAME" = "Arch (pacman)" ] || [ "$DISTRO_NAME" = "Arch-like (pacman)" ]; then
            PYTHON3="python"
        fi
    else
        echo "Install Python from your package manager or https://www.python.org/downloads/, then run this script again."
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
    DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
    mkdir -p "$DESKTOP_DIR"
    DESKTOP_FILE="$DESKTOP_DIR/GlanceRF.desktop"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=GlanceRF
Comment=GlanceRF dashboard
Exec=$PYTHON_EXE run.py
Path=$PROJECT_DIR
Terminal=false
Categories=Utility;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "Shortcut created: $DESKTOP_FILE"
    echo ""
fi

# --- 7. Create startup job if requested ---
HAS_SYSTEMD="no"
command -v systemctl &>/dev/null && systemctl --user 2>/dev/null && HAS_SYSTEMD="yes"

if [ "$WANT_STARTUP" = true ]; then
    if [ "$HAS_SYSTEMD" = "yes" ]; then
        USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
        mkdir -p "$USER_UNIT_DIR"
        PYTHON_PATH="$(command -v $PYTHON3)"
        SERVICE_FILE="$USER_UNIT_DIR/glancerf.service"
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=GlanceRF dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
        systemctl --user daemon-reload
        systemctl --user enable glancerf.service
        echo "Startup service installed: $SERVICE_FILE"
    else
        echo "systemd not available; skipping run-at-login."
    fi
    echo ""
fi

# --- 8. Run now or start service ---
if [ "$WANT_STARTUP" = true ] && [ "$HAS_SYSTEMD" = "yes" ]; then
    echo "Starting GlanceRF now (and at next logon)..."
    systemctl --user start glancerf.service 2>/dev/null || true
    echo "Started. Status: systemctl --user status glancerf"
else
    echo "Starting GlanceRF..."
    cd "$PROJECT_DIR"
    exec "$PYTHON3" run.py
fi
