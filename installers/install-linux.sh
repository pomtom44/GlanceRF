#!/bin/bash
# GlanceRF Linux installer - text-based, user inputs
# Mirrors Windows installer: mode selection, shortcut, dependencies, config, service (headless)
# Supports Debian/Ubuntu, Fedora/RHEL, Arch, openSUSE

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run a command quietly with a spinner; returns command exit code
run_quiet() {
    local msg="$1"
    shift
    local spinstr='|/-\'
    ("$@" >/dev/null 2>&1) &
    local pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf "\r%s [%c] " "$msg" "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep 0.1
    done
    wait $pid
    local ret=$?
    if [ $ret -eq 0 ]; then
        printf "\r%s done\n" "$msg"
    else
        printf "\r%s failed\n" "$msg"
    fi
    return $ret
}

# Do not run as root; use sudo only for package installs
if [ "$(id -u)" -eq 0 ]; then
    echo "Do not run this script as root or with sudo."
    echo "Run as your normal user; the script will use sudo only when installing packages."
    echo "  Example: ./install-linux.sh"
    exit 1
fi

echo "=========================================="
echo "  GlanceRF Linux Installer"
echo "=========================================="
echo "Run as your normal user; sudo is used only for package installs."

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

# --- Distro detection ---
DISTRO_ID=""
DISTRO_ID_LIKE=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-}"
    DISTRO_ID_LIKE="${ID_LIKE:-}"
fi

PKG_INSTALL=""
DISTRO_NAME=""

case "${DISTRO_ID}" in
    debian|ubuntu|linuxmint|pop|elementary|raspbian)
        DISTRO_NAME="Debian/Ubuntu (apt)"
        PKG_INSTALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
        ;;
    fedora|rhel|centos|rocky|almalinux|ol)
        if command -v dnf &>/dev/null; then
            DISTRO_NAME="Fedora/RHEL (dnf)"
            PKG_INSTALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv"
        else
            DISTRO_NAME="RHEL/CentOS (yum)"
            PKG_INSTALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv"
        fi
        ;;
    arch|manjaro|endeavouros)
        DISTRO_NAME="Arch (pacman)"
        PKG_INSTALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip"
        ;;
    opensuse*|sles)
        DISTRO_NAME="openSUSE/SLE (zypper)"
        PKG_INSTALL="sudo zypper refresh && sudo zypper install -y python3 python3-pip python3-venv"
        ;;
    *)
        case "${DISTRO_ID_LIKE}" in
            *debian*|*ubuntu*)
                DISTRO_NAME="Debian-like (apt)"
                PKG_INSTALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
                ;;
            *rhel*|*fedora*)
                if command -v dnf &>/dev/null; then
                    DISTRO_NAME="Fedora/RHEL-like (dnf)"
                    PKG_INSTALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv"
                else
                    DISTRO_NAME="RHEL-like (yum)"
                    PKG_INSTALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv"
                fi
                ;;
            *arch*)
                DISTRO_NAME="Arch-like (pacman)"
                PKG_INSTALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip"
                ;;
            *)
                if [ -f /etc/debian_version ]; then
                    DISTRO_NAME="Debian-based (apt)"
                    PKG_INSTALL="sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
                elif [ -f /etc/redhat-release ]; then
                    DISTRO_NAME="RHEL/Fedora"
                    if command -v dnf &>/dev/null; then
                        PKG_INSTALL="sudo dnf check-update || true; sudo dnf install -y python3 python3-pip python3-virtualenv"
                    else
                        PKG_INSTALL="sudo yum check-update || true; sudo yum install -y python3 python3-pip python3-virtualenv"
                    fi
                elif command -v pacman &>/dev/null; then
                    DISTRO_NAME="Arch (pacman)"
                    PKG_INSTALL="sudo pacman -Sy && sudo pacman -S --noconfirm python python-pip"
                elif command -v zypper &>/dev/null; then
                    DISTRO_NAME="openSUSE (zypper)"
                    PKG_INSTALL="sudo zypper refresh && sudo zypper install -y python3 python3-pip python3-venv"
                else
                    DISTRO_NAME="unknown"
                fi
                ;;
        esac
        ;;
esac

echo "Detected distro: ${DISTRO_NAME:-unknown}"

# --- Desktop vs Server detection ---
HAS_DISPLAY="no"
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    HAS_DISPLAY="yes"
fi

if [ "$HAS_DISPLAY" = "yes" ]; then
    echo "Desktop environment detected (display available)."
    echo "How would you like to run GlanceRF?"
    echo "  1) Terminal + Browser - Terminal visible, opens browser"
    echo "  2) Terminal only      - Terminal visible, no browser"
    echo "  3) Service           - Runs in background (systemd)"
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
    echo "Server mode detected (no display - SSH, TTY, or headless)."
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
echo "Installing... (this may take a few minutes)"

# --- 1. Install system packages (Python, pip, venv) ---
if [ -n "$PKG_INSTALL" ]; then
    if ! run_quiet "Installing system packages (Python, pip, venv)" bash -c "$PKG_INSTALL"; then
        echo "System package install had warnings; continuing if Python is available."
    fi
fi

# --- 2. Find Python ---
PYTHON3=""
for cmd in python3 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON3="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON3" ]; then
    echo "Python 3.8 or higher not found. Install it from your distro or https://www.python.org/downloads/"
    [ -n "$PKG_INSTALL" ] && echo "  Or run: $PKG_INSTALL"
    exit 1
fi
echo "Python OK: $PYTHON3"

if ! "$PYTHON3" -c "import ensurepip" 2>/dev/null; then
    echo "Python venv module not available. Install python3-venv (e.g. sudo apt-get install -y python3-venv) and run again."
    exit 1
fi

# --- 3. Create venv ---
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ -d "$VENV_DIR" ] && ! "$VENV_PYTHON" -m pip --version &>/dev/null 2>&1; then
    echo "Removing broken venv; will recreate."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    if ! run_quiet "Creating virtual environment" "$PYTHON3" -m venv "$VENV_DIR"; then
        echo "Failed to create venv. Install python3-venv and run again."
        exit 1
    fi
fi

# --- 4. Install dependencies (based on mode) ---
install_deps() {
    if [ -f "$HEADLESS_REQ" ]; then
        "$VENV_PYTHON" -m pip install -r "$HEADLESS_REQ" -q
    else
        "$VENV_PYTHON" -m pip install pystray Pillow -q
    fi
}
HEADLESS_REQ="$PROJECT_DIR/requirements/requirements-linux.txt"
if ! run_quiet "Installing dependencies" install_deps; then
    echo "Retrying with full output..."
    install_deps || exit 1
fi

# --- 5. Update config ---
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

# --- 6. Desktop shortcut ---
if [ "$WANT_SHORTCUT" = true ] && [ "$HAS_DISPLAY" = "yes" ]; then
    DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
    mkdir -p "$DESKTOP_DIR"
    if [ "$DESKTOP_MODE" = "headless" ]; then
        # Service mode: shortcut opens browser to web page
        PORT="$("$VENV_PYTHON" -c "import json; c=json.load(open('$PROJECT_DIR/glancerf_config.json')); print(c.get('port',8080))" 2>/dev/null || echo "8080")"
        DESKTOP_FILE="$DESKTOP_DIR/GlanceRF.desktop"
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=GlanceRF
Comment=GlanceRF dashboard
Exec=xdg-open http://localhost:$PORT
Terminal=false
Categories=Utility;
EOF
        chmod +x "$DESKTOP_FILE"
        echo "Shortcut: $DESKTOP_FILE (opens browser)"
    else
        # Terminal + Browser or Terminal only: shortcut runs GlanceRF
        DESKTOP_FILE="$DESKTOP_DIR/GlanceRF.desktop"
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=GlanceRF
Comment=GlanceRF dashboard
Exec=$VENV_PYTHON run.py
Path=$PROJECT_DIR
Terminal=true
Categories=Utility;
EOF
        chmod +x "$DESKTOP_FILE"
        echo "Shortcut: $DESKTOP_FILE"
    fi
fi

# --- 7. Headless: systemd user service + tray autostart ---
HAS_SYSTEMD="no"
command -v systemctl &>/dev/null && systemctl --user is-system-running &>/dev/null 2>&1 && HAS_SYSTEMD="yes"

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
    if [ "$HAS_SYSTEMD" = "yes" ]; then
        USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
        mkdir -p "$USER_UNIT_DIR"
        SERVICE_FILE="$USER_UNIT_DIR/glancerf.service"
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=GlanceRF dashboard (headless)
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
        systemctl --user daemon-reload 2>/dev/null || true
        systemctl --user enable glancerf.service 2>/dev/null || true
        echo "Systemd service installed: $SERVICE_FILE"

        # Tray icon in autostart (only when desktop environment is available)
        if [ "$HAS_DISPLAY" = "yes" ]; then
            AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
            mkdir -p "$AUTOSTART_DIR"
            TRAY_FILE="$AUTOSTART_DIR/glancerf-tray.desktop"
            cat > "$TRAY_FILE" << EOF
[Desktop Entry]
Type=Application
Name=GlanceRF Tray
Comment=GlanceRF tray icon
Exec=$VENV_PYTHON -m glancerf.desktop.tray_helper
Path=$PROJECT_DIR
Terminal=false
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
            echo "Tray autostart: $TRAY_FILE"
        fi
    else
        echo "systemd not available; service requires systemd."
    fi
fi

# --- 8. Startup at logon (for terminal+browser and terminal-only modes) ---
if [ "$WANT_STARTUP" = true ] && [ "$DESKTOP_MODE" != "headless" ] && [ "$HAS_SYSTEMD" = "yes" ]; then
    USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p "$USER_UNIT_DIR"
    SERVICE_FILE="$USER_UNIT_DIR/glancerf.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=GlanceRF dashboard
After=graphical-session.target

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
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable glancerf.service 2>/dev/null || true
    echo "Startup at logon enabled: $SERVICE_FILE"
fi

# --- 9. Complete and run ---
echo "=========================================="
echo "  Install complete."
echo "=========================================="

if [ "$INSTALL_SERVICE" = true ] && [ "$HAS_SYSTEMD" = "yes" ]; then
    echo "Starting GlanceRF service..."
    systemctl --user start glancerf.service 2>/dev/null || true
    if [ "$HAS_DISPLAY" = "yes" ]; then
        (cd "$PROJECT_DIR" && nohup "$VENV_PYTHON" -m glancerf.desktop.tray_helper >/dev/null 2>&1 &)
    fi
    PORT="$("$VENV_PYTHON" -c "import json; c=json.load(open('$PROJECT_DIR/glancerf_config.json')); print(c.get('port',8080))" 2>/dev/null || echo "8080")"
    LOCAL_IP="$("$VENV_PYTHON" -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
except Exception:
    print('localhost')
finally:
    s.close()
" 2>/dev/null || echo "localhost")"
    echo "GlanceRF is running. Open http://${LOCAL_IP}:$PORT in your browser."
    if [ "$HAS_DISPLAY" = "yes" ]; then
        echo "Tray icon started. It will also start at next logon."
    fi
elif [ "$WANT_STARTUP" = true ] && [ "$HAS_SYSTEMD" = "yes" ]; then
    echo "Starting GlanceRF..."
    systemctl --user start glancerf.service 2>/dev/null || true
    echo "GlanceRF started. Status: systemctl --user status glancerf"
else
    echo "Starting GlanceRF..."
    cd "$PROJECT_DIR"
    exec "$VENV_PYTHON" run.py
fi
