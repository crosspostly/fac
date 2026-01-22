#!/bin/bash
# start_safe.sh - Script to safely restart the server and scheduler

echo "🔍 Checking for zombie servers on port 5005..."
# Find PID listening on 5005
PID=$(lsof -t -i:5005)

if [ -n "$PID" ]; then
    echo "💀 Found zombie process (PID $PID). Killing it..."
    kill -9 $PID
    echo "✅ Zombie killed."
else
    echo "✅ Port 5005 is free."
fi

echo "🚀 Starting file server..."
nohup /home/daoq/rutube/venv/bin/python3 server_simple.py > server.log 2>&1 &
echo "✅ Server started (PID $!)."

echo "📅 Starting scheduler..."
nohup /home/daoq/rutube/venv/bin/python3 scheduler.py > scheduler.log 2>&1 &
echo "✅ Scheduler started (PID $!)."

echo "🎉 System restarted successfully!"
