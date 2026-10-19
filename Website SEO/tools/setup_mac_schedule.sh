#!/bin/bash
# Setup the Mac's 30-minute HARO fallback run (the Gemini drafter)
# haro_agent.py (Antigravity + Claude) takes new digests every 10 minutes. This run fires every
# 30 minutes the Mac is awake (launchd catches up after sleep): while that pipeline is alive it
# takes only the digests handed over to it, and when it is down, digests older than 3 hours.

PLIST_NAME="com.aiprofitlab.haro.plist"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_DIR/$PLIST_NAME"
PROJECT_DIR="/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO"
PYTHON_BIN="$(which python3)"
SCRIPT_PATH="$PROJECT_DIR/execution/haro_email_processor.py"
LOG_OUT="$PROJECT_DIR/.tmp/haro_stdout.log"
LOG_ERR="$PROJECT_DIR/.tmp/haro_stderr.log"

mkdir -p "$LAUNCH_DIR"
mkdir -p "$PROJECT_DIR/.tmp"

# Unload existing if loaded
launchctl unload "$PLIST_PATH" 2>/dev/null

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiprofitlab.haro</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$SCRIPT_PATH</string>
        <string>--defer-to-agent</string>
        <string>--min-age-hours</string>
        <string>3</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>StandardOutPath</key>
    <string>$LOG_OUT</string>
    <key>StandardErrorPath</key>
    <string>$LOG_ERR</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"

echo "[+] Scheduled the HARO fallback on your Mac every 30 minutes while it is awake."
echo "    Plist location: $PLIST_PATH"
echo "    Output logs: $LOG_OUT"
