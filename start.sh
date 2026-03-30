#!/bin/bash
set -e

PROJ_DIR="/mnt/nvme/clawspace/asr-compare"
LOG_FILE="$PROJ_DIR/logs/uvicorn.log"
PORT=8400
# Use conda env python / uvicorn
CONDA_ENV_BIN="/data/miniconda3/envs/asr-compare/bin"
UVICORN_BIN="/home/david/.local/bin/uvicorn"
PYTHON_BIN="$CONDA_ENV_BIN/python3.10"

# ── Env vars ──────────────────────────────────────────────
export HF_ENDPOINT=https://hf-mirror.com
export HF_TOKEN="${HF_TOKEN:-hf_}"
export HF_HOME="$PROJ_DIR/models/hf_cache"
export MODELSCOPE_CACHE="$PROJ_DIR/models/ms_cache"
export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=0
# Ensure conda env site-packages take priority
export PYTHONPATH="$CONDA_ENV_BIN/../lib/python3.10/site-packages:$PYTHONPATH"

mkdir -p "$PROJ_DIR/logs" "$HF_HOME" "$MODELSCOPE_CACHE"

# ── Check if already running ──────────────────────────────
if ss -tlnp | grep -q ":$PORT "; then
    echo "[WARN] Port $PORT is already in use. Run stop.sh first."
    exit 1
fi

cd "$PROJ_DIR"

# ── Start uvicorn with conda env python ───────────────────
nohup "$PYTHON_BIN" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PROJ_DIR/logs/uvicorn.pid"

sleep 2

if kill -0 $PID 2>/dev/null; then
    echo "✅ ASR Compare started (PID=$PID)"
    echo "   Python: $PYTHON_BIN"
    echo "   Access: http://$(hostname -I | awk '{print $1}'):$PORT"
    echo "   Logs:   tail -f $LOG_FILE"
else
    echo "❌ Failed to start. Check logs: $LOG_FILE"
    exit 1
fi
