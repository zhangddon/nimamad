#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
DIST_DIR="dist"
PKG_DIR="$DIST_DIR/autopilot_agent_$STAMP"

mkdir -p "$PKG_DIR"
cp autopilot_agent.py writer_agent.py control_panel.py README.md "$PKG_DIR"/
cp -r data outputs scripts "$PKG_DIR"/

cat > "$PKG_DIR/start.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
mkdir -p logs outputs
nohup .venv/bin/python control_panel.py --host 0.0.0.0 --port 8787 > logs/control_panel.log 2>&1 &
echo "control panel: http://127.0.0.1:8787"
SH
chmod +x "$PKG_DIR/start.sh"

tar -czf "$DIST_DIR/autopilot_agent_$STAMP.tar.gz" -C "$DIST_DIR" "autopilot_agent_$STAMP"
echo "[ok] package created: $DIST_DIR/autopilot_agent_$STAMP.tar.gz"
