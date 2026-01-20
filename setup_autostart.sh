#!/bin/bash

# Define paths
USER_DIR="/home/daoq"
PROJECT_DIR="$USER_DIR/rutube"
SYSTEMD_DIR="$USER_DIR/.config/systemd/user"
PYTHON_EXEC="/usr/bin/python3" # Assuming system python, as venv failed earlier

# Ensure systemd user directory exists
mkdir -p "$SYSTEMD_DIR"

# 1. Create File Server Service
echo "📝 Creating rutube-server.service..."
cat <<EOF > "$SYSTEMD_DIR/rutube-server.service"
[Unit]
Description=Rutube Local File Server
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC server_simple.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/server.log
StandardError=append:$PROJECT_DIR/server.log

[Install]
WantedBy=default.target
EOF

# 2. Create Scheduler/Bot Service
echo "📝 Creating rutube-bot.service..."
cat <<EOF > "$SYSTEMD_DIR/rutube-bot.service"
[Unit]
Description=Rutube Sync Scheduler Bot
After=network.target rutube-server.service

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC scheduler.py
Restart=always
RestartSec=60
StandardOutput=append:$PROJECT_DIR/scheduler.log
StandardError=append:$PROJECT_DIR/scheduler.log

[Install]
WantedBy=default.target
EOF

# 3. Enable and Start
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload

echo "🛑 Stopping old manual instances..."
# Kill manually started scripts to avoid conflicts
pkill -f server_simple.py
pkill -f scheduler.py

echo "🚀 Enabling and Starting Services..."
systemctl --user enable --now rutube-server.service
systemctl --user enable --now rutube-bot.service

# 4. Enable Linger (Critical for 24/7)
echo "🔓 Enabling Linger (Run when logged out)..."
if command -v loginctl &> /dev/null; then
    loginctl enable-linger $USER
else
    echo "⚠️ 'loginctl' not found. Ensure lingering is enabled manually if this is a VPS."
fi

echo "✅ DONE! Your bot is now a system service."
echo "   Status Check: systemctl --user status rutube-bot"
echo "   Logs: tail -f scheduler.log"
