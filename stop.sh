#!/bin/bash
PORT=8400
PROJ_DIR="/mnt/nvme/clawspace/asr-compare"
PID_FILE="$PROJ_DIR/logs/uvicorn.pid"

# Try pid file first
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "✅ Stopped PID=$PID"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Fallback: kill by port
PIDS=$(ss -tlnp | grep ":$PORT " | grep -oP 'pid=\K[0-9]+')
if [ -z "$PIDS" ]; then
    echo "ℹ️  No process found on port $PORT"
    exit 0
fi

for PID in $PIDS; do
    kill "$PID" && echo "✅ Killed PID=$PID (port $PORT)"
done
