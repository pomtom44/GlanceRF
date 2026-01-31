#!/bin/bash
# Install GlanceRF as a launchd LaunchAgent (starts at logon).
# Run from the Project folder: ./scripts/startup/install-mac-launchd.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLIST_NAME="com.glancerf.plist"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PYTHON3="$(command -v python3)"

if [ -z "$PYTHON3" ]; then
    echo "Error: python3 not found in PATH."
    exit 1
fi
if [ ! -f "$PROJECT_DIR/run.py" ]; then
    echo "Error: run.py not found. Expected Project dir: $PROJECT_DIR"
    exit 1
fi

mkdir -p "$LAUNCH_AGENTS"
sed -e "s|YOUR_PROJECT_PATH|$PROJECT_DIR|g" \
    -e "s|YOUR_PYTHON3_PATH|$PYTHON3|g" \
    "$SCRIPT_DIR/$PLIST_NAME" > "$LAUNCH_AGENTS/$PLIST_NAME"

launchctl unload "$LAUNCH_AGENTS/$PLIST_NAME" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS/$PLIST_NAME"
echo "Installed $LAUNCH_AGENTS/$PLIST_NAME"
echo "Start:  launchctl load $LAUNCH_AGENTS/$PLIST_NAME"
echo "Stop:   launchctl unload $LAUNCH_AGENTS/$PLIST_NAME"
echo "Logs:   $PROJECT_DIR/glancerf.log"
