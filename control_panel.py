#!/usr/bin/env python3
"""Simple local control panel with one-click agent start button."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
PID_FILE = LOG_DIR / "agent.pid"
LOG_FILE = LOG_DIR / "agent.log"


def is_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        Path(f"/proc/{pid}").exists()
        return Path(f"/proc/{pid}").exists()
    except Exception:
        return False


def start_agent() -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if is_running():
        return {"ok": True, "message": "agent already running"}

    cmd = [
        "python3",
        "autopilot_agent.py",
        "--input",
        "data/hot_trends.json",
        "--outdir",
        "outputs",
    ]
    with LOG_FILE.open("a", encoding="utf-8") as logf:
        logf.write(f"\n[{datetime.now().isoformat()}] starting agent...\n")
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=logf, stderr=logf)

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    return {"ok": True, "message": f"agent started pid={proc.pid}"}


def stop_agent() -> dict:
    if not PID_FILE.exists():
        return {"ok": True, "message": "agent not running"}
    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    try:
        subprocess.run(["kill", str(pid)], check=False)
    finally:
        PID_FILE.unlink(missing_ok=True)
    return {"ok": True, "message": f"agent stop signal sent pid={pid}"}


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Autopilot Agent 控制台</title>
  <style>
    body { font-family: sans-serif; margin: 40px; max-width: 720px; }
    button { padding: 10px 14px; margin-right: 8px; cursor: pointer; }
    pre { background: #f4f4f4; padding: 12px; }
  </style>
</head>
<body>
  <h2>Autopilot Agent 一键控制台</h2>
  <p>点击按钮可启动/停止 Agent。输出日志：<code>logs/agent.log</code></p>
  <button onclick="call('/start')">一键启动 Agent</button>
  <button onclick="call('/stop')">停止 Agent</button>
  <button onclick="call('/status')">刷新状态</button>
  <pre id="out">loading...</pre>
  <script>
    async function call(path) {
      const r = await fetch(path, {method: 'POST'});
      const j = await r.json();
      document.getElementById('out').textContent = JSON.stringify(j, null, 2);
    }
    call('/status');
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/start":
            self._send_json(start_agent())
            return
        if self.path == "/stop":
            self._send_json(stop_agent())
            return
        if self.path == "/status":
            self._send_json(
                {
                    "ok": True,
                    "running": is_running(),
                    "pid_file": str(PID_FILE),
                    "log_file": str(LOG_FILE),
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one-click control panel")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[control-panel] http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
