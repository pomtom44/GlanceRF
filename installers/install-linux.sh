#!/bin/bash
# GlanceRF Linux installer: detects distribution (Debian/Ubuntu, Fedora/RHEL, Arch, etc.),
# then runs the appropriate install method for that distro.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Do not run as root; we escalate with sudo only for package installs
if [ "$(id -u)" -eq 0 ]; then
    echo "Do not run this script as root or with sudo."
    echo "Run as your normal user; the script will use sudo only when installing packages (apt/dnf etc.)."
    echo "  Example: ./install-linux.sh"
    exit 1
fi

echo "GlanceRF Linux installer"
echo "------------------------"
echo "Run as your normal user; sudo is used only for package installs (apt/dnf etc.)."
echo ""

# --- Distro detection (using /etc/os-release when available) ---
DISTRO_ID=""
DISTRO_ID_LIKE=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-}"
    DISTRO_ID_LIKE="${ID_LIKE:-}"
fi

# Classify distro and set PKG_INSTALL_ALL = one command to update + install python stack + ffmpeg
PKG_INSTALL_ALL=""
DISTRO_NAME=""

case "${DISTRO_ID}" in
    debian|ubuntu|linuxmint|pop|elementary|raspbian)
        DISTRO_NAME="Debian/Ubuntu (apt)"
        PKG_INSTALL_ALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv ffmpeg"
        ;;
    fedora|rhel|centos|rocky|almalinux|ol)
        if command -v dnf &>/dev/null; then
            DISTRO_NAME="Fedora/RHEL (dnf)"
            PKG_INSTALL_ALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv ffmpeg"
        else
            DISTRO_NAME="RHEL/CentOS (yum)"
            PKG_INSTALL_ALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv ffmpeg"
        fi
        ;;
    arch|manjaro|endeavouros)
        DISTRO_NAME="Arch (pacman)"
        PKG_INSTALL_ALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip ffmpeg"
        ;;
    opensuse*|sles)
        DISTRO_NAME="openSUSE/SLE (zypper)"
        PKG_INSTALL_ALL="sudo zypper refresh && sudo zypper install -y python3 python3-pip python3-venv ffmpeg"
        ;;
    *)
        case "${DISTRO_ID_LIKE}" in
            *debian*|*ubuntu*)
                DISTRO_NAME="Debian-like (apt)"
                PKG_INSTALL_ALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv ffmpeg"
                ;;
            *rhel*|*fedora*)
                if command -v dnf &>/dev/null; then
                    DISTRO_NAME="Fedora/RHEL-like (dnf)"
                    PKG_INSTALL_ALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv ffmpeg"
                else
                    DISTRO_NAME="RHEL-like (yum)"
                    PKG_INSTALL_ALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv ffmpeg"
                fi
                ;;
            *arch*)
                DISTRO_NAME="Arch-like (pacman)"
                PKG_INSTALL_ALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip ffmpeg"
                ;;
            *)
                if [ -f /etc/debian_version ]; then
                    DISTRO_NAME="Debian-based (apt)"
                    PKG_INSTALL_ALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv ffmpeg"
                elif [ -f /etc/redhat-release ]; then
                    if command -v dnf &>/dev/null; then
                        DISTRO_NAME="Fedora/RHEL (dnf)"
                        PKG_INSTALL_ALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv ffmpeg"
                    else
                        DISTRO_NAME="RHEL (yum)"
                        PKG_INSTALL_ALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv ffmpeg"
                    fi
                elif command -v pacman &>/dev/null; then
                    DISTRO_NAME="Arch (pacman)"
                    PKG_INSTALL_ALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip ffmpeg"
                elif command -v zypper &>/dev/null; then
                    DISTRO_NAME="openSUSE (zypper)"
                    PKG_INSTALL_ALL="sudo zypper refresh && sudo zypper install -y python3 python3-pip python3-venv ffmpeg"
                else
                    DISTRO_NAME="unknown (install Python and ffmpeg manually if needed)"
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

# --- Ask startup and headless before installing ---
WANT_STARTUP=false
read -r -p "Run GlanceRF at logon? (y/n) " startup_resp
case "$startup_resp" in
    y|Y) WANT_STARTUP=true ;;
esac

WANT_HEADLESS=false
read -r -p "Run in desktop (window) or headless (browser only)? (desktop/headless) " mode_resp
case "$mode_resp" in
    headless|Headless|HEADLESS) WANT_HEADLESS=true ;;
esac

WANT_SHORTCUT=false
read -r -p "Create a desktop shortcut? (y/n) " shortcut_resp
case "$shortcut_resp" in
    y|Y) WANT_SHORTCUT=true ;;
esac
echo ""

# --- 1. Install system packages once (Python, venv, ffmpeg) ---
if [ -n "$PKG_INSTALL_ALL" ]; then
    echo "Installing system packages (Python, pip, venv, ffmpeg)..."
    if ! eval "$PKG_INSTALL_ALL"; then
        echo "System package install had warnings or failures; continuing if Python is available."
    fi
    echo ""
fi

# --- 2. Find Python ---
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
    echo "Python 3.8 or higher not found. Install it from your distro or https://www.python.org/downloads/"
    [ -n "$PKG_INSTALL_ALL" ] && echo "  Or run: $PKG_INSTALL_ALL"
    exit 1
fi
echo "Python OK: $PYTHON3"

if ! "$PYTHON3" -c "import ensurepip" 2>/dev/null; then
    echo "Python venv module (ensurepip) not available. Install python3-venv (e.g. sudo apt-get install -y python3-venv) and run this script again."
    exit 1
fi
echo ""

# --- 3. Create venv and install requirements ---
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ -d "$VENV_DIR" ] && ! "$VENV_PYTHON" -m pip --version &>/dev/null; then
    echo "Removing broken venv (no pip); will recreate."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    if ! "$PYTHON3" -m venv "$VENV_DIR"; then
        echo "Failed to create venv. Install python3-venv (e.g. sudo apt-get install -y python3-venv) and run this script again."
        exit 1
    fi
fi

echo "Checking requirements..."
REQUIREMENTS_PATH="$PROJECT_DIR/requirements.txt"
if ! "$VENV_PYTHON" -c "import fastapi" 2>/dev/null; then
    echo "Installing requirements..."
    if ! "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_PATH"; then
        echo "Failed to install requirements in the project venv."
        echo "  Check $REQUIREMENTS_PATH and your network. On some distros you may need development headers (e.g. python3-dev on Debian/Ubuntu, python3-devel on Fedora/RHEL) to build packages."
        exit 1
    fi
fi
echo "Requirements OK."
echo ""

# --- 4. ffmpeg (optional; already installed with system packages) ---
command -v ffmpeg &>/dev/null && echo "ffmpeg OK." || echo "ffmpeg not found (optional; for Webcam Local server install with apt/dnf/pacman)."
echo ""

# --- 5. Update config ---
USE_DESKTOP="True"
[ "$WANT_HEADLESS" = true ] && USE_DESKTOP="False"
export GLANCERF_PROJECT="$PROJECT_DIR"
"$VENV_PYTHON" -c "
import json, os
p = os.path.join(os.environ.get('GLANCERF_PROJECT',''), 'glancerf_config.json')
if os.path.exists(p):
    with open(p,'r',encoding='utf-8') as f: c = json.load(f)
else:
    c = {'port':8080,'readonly_port':8081,'use_desktop':True,'first_run':True,'max_grid_scale':10,'grid_columns':3,'grid_rows':3,'aspect_ratio':'16:9','orientation':'landscape','layout':[['','',''],['','',''],['','','']],'cell_spans':{},'module_settings':{}}
c['use_desktop'] = $USE_DESKTOP
with open(p,'w',encoding='utf-8') as f: json.dump(c, f, indent=2)
" || true
echo "Config: $([ "$WANT_HEADLESS" = true ] && echo 'headless' || echo 'desktop')."
echo ""

# --- 6. Desktop shortcut ---

if [ "$WANT_SHORTCUT" = true ]; then
    DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
    mkdir -p "$DESKTOP_DIR"
    DESKTOP_FILE="$DESKTOP_DIR/GlanceRF.desktop"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=GlanceRF
Comment=GlanceRF dashboard
Exec=$VENV_PYTHON run.py
Path=$PROJECT_DIR
Terminal=false
Categories=Utility;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "Shortcut created: $DESKTOP_FILE"
    echo ""
fi

# --- 7. Create startup job (run at logon) ---
HAS_SYSTEMD="no"
command -v systemctl &>/dev/null && systemctl --user is-system-running &>/dev/null && HAS_SYSTEMD="yes"

if [ "$WANT_STARTUP" = true ]; then
    if [ "$HAS_SYSTEMD" = "yes" ]; then
        USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
        mkdir -p "$USER_UNIT_DIR"
        SERVICE_FILE="$USER_UNIT_DIR/glancerf.service"
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=GlanceRF dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PYTHON run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
        systemctl --user daemon-reload 2>/dev/null
        systemctl --user enable glancerf.service 2>/dev/null
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
    exec "$VENV_PYTHON" run.py
fi
