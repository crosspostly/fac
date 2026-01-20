#!/bin/bash

# Define paths
USER_DIR="/home/daoq"
PROJECT_DIR="$USER_DIR/rutube"
SYSTEMD_DIR="$USER_DIR/.config/systemd/user"
PYTHON_EXEC="/usr/bin/python3"

# 1. Update Scheduler Service with Unbuffered Output
echo "📝 Updating rutube-bot.service..."
cat <<EOF > "$SYSTEMD_DIR/rutube-bot.service"
[Unit]
Description=Rutube Sync Scheduler Bot
After=network.target rutube-server.service

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC scheduler.py
Restart=always
RestartSec=60
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:$PROJECT_DIR/scheduler.log
StandardError=append:$PROJECT_DIR/scheduler.log

[Install]
WantedBy=default.target
EOF

# 2. Reload and Restart
echo "🔄 Reloading systemd..."
systemctl --user daemon-reload
echo "🔄 Restarting bot..."
systemctl --user restart rutube-bot

echo "✅ Logging fix applied (PYTHONUNBUFFERED=1)."
