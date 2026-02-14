#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs outputs

# create venv only if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# start control panel only if not running
if [ -f "logs/control_panel.pid" ]; then
  OLD_PID="$(cat logs/control_panel.pid || true)"
  if [ -n "${OLD_PID}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[ok] 控制台已在运行: http://127.0.0.1:8787 (pid=$OLD_PID)"
    exit 0
  fi
fi

nohup .venv/bin/python control_panel.py --host 0.0.0.0 --port 8787 > logs/control_panel.log 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > logs/control_panel.pid

echo "[ok] 控制台已启动: http://127.0.0.1:8787 (pid=$NEW_PID)"
echo "[ok] 如在远程服务器，请放行 8787 端口后访问 http://<server-ip>:8787"
