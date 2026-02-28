#!/bin/bash
# X Patrol — Full Flow Runner
# 启动 Chrome → 抓取 → 输出 JSON → 清理
# Usage: bash run-patrol.sh [--port 9222] [--keep-chrome]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=9222
KEEP_CHROME=false
PROFILE="$HOME/.openclaw/browser-profiles/openclaw/"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --keep-chrome) KEEP_CHROME=true; shift ;;
        *) shift ;;
    esac
done

echo "[patrol] Starting Chrome headless on port $PORT..." >&2

# Clean up stale Chrome
pkill -f "chrome.*$PORT" 2>/dev/null || true
sleep 1
rm -f "$PROFILE/SingletonLock"

# Start Chrome
nohup google-chrome --headless --no-sandbox --disable-gpu \
    --remote-debugging-port=$PORT \
    --user-data-dir="$PROFILE" \
    about:blank > /tmp/chrome-patrol.log 2>&1 &
CHROME_PID=$!

# Wait for CDP ready
echo "[patrol] Waiting for CDP..." >&2
for i in $(seq 1 15); do
    if curl -s "http://127.0.0.1:$PORT/json/version" > /dev/null 2>&1; then
        echo "[patrol] Chrome ready (PID $CHROME_PID)" >&2
        break
    fi
    if [ $i -eq 15 ]; then
        echo "[patrol] ERROR: Chrome failed to start" >&2
        kill $CHROME_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Run scraper
echo "[patrol] Running scraper..." >&2
python3 "$SCRIPT_DIR/scraper.py" --port $PORT

# Cleanup
if [ "$KEEP_CHROME" = false ]; then
    echo "[patrol] Cleaning up Chrome..." >&2
    kill $CHROME_PID 2>/dev/null || true
    sleep 1
    pkill -f "chrome.*$PORT" 2>/dev/null || true
    rm -f "$PROFILE/SingletonLock"
fi

echo "[patrol] Done." >&2
