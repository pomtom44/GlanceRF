#!/bin/bash
# Install GlanceRF as a systemd user service (starts at logon).
# Run from the Project folder: ./scripts/startup/install-systemd.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="glancerf.service"
USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
PYTHON3="$(command -v python3)"

if [ -z "$PYTHON3" ]; then
    echo "Error: python3 not found in PATH."
    exit 1
fi
if [ ! -f "$PROJECT_DIR/run.py" ]; then
    echo "Error: run.py not found. Expected Project dir: $PROJECT_DIR"
    exit 1
fi

mkdir -p "$USER_UNIT_DIR"
sed -e "s|YOUR_PROJECT_PATH|$PROJECT_DIR|g" \
    -e "s|YOUR_PYTHON3_PATH|$PYTHON3|g" \
    "$SCRIPT_DIR/glancerf.service" > "$USER_UNIT_DIR/$SERVICE_NAME"

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
echo "Installed $USER_UNIT_DIR/$SERVICE_NAME"
echo "Start now: systemctl --user start glancerf"
echo "Status:   systemctl --user status glancerf"
