#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip >/dev/null

mkdir -p logs outputs
nohup .venv/bin/python control_panel.py --host 0.0.0.0 --port 8787 > logs/control_panel.log 2>&1 &

echo "[ok] 控制台已启动: http://127.0.0.1:8787"
echo "[ok] 如在远程服务器，请放行 8787 端口后访问 http://<server-ip>:8787"
