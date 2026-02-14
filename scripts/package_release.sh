#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
DIST_DIR="dist"
PKG_DIR="$DIST_DIR/autopilot_agent_$STAMP"

mkdir -p "$PKG_DIR"
cp autopilot_agent.py writer_agent.py control_panel.py README.md Dockerfile docker-compose.yml "$PKG_DIR"/
cp -r data outputs scripts "$PKG_DIR"/

cat > "$PKG_DIR/start.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
bash scripts/one_click_start.sh
SH
chmod +x "$PKG_DIR/start.sh"

cat > "$PKG_DIR/stop.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
bash scripts/one_click_stop.sh
SH
chmod +x "$PKG_DIR/stop.sh"

# Optional: bundle current virtualenv for same-OS fast local deployment
if [ -d ".venv" ]; then
  cp -r .venv "$PKG_DIR/.venv"
fi

tar -czf "$DIST_DIR/autopilot_agent_$STAMP.tar.gz" -C "$DIST_DIR" "autopilot_agent_$STAMP"
echo "[ok] package created: $DIST_DIR/autopilot_agent_$STAMP.tar.gz"
