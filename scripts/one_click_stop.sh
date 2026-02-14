#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f "logs/control_panel.pid" ]; then
  echo "[ok] 未发现控制台进程"
  exit 0
fi

PID="$(cat logs/control_panel.pid || true)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "[ok] 已停止控制台 (pid=$PID)"
else
  echo "[ok] 控制台进程不存在，清理旧 PID 文件"
fi

rm -f logs/control_panel.pid
