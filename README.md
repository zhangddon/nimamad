# Autopilot Trend Agent（热点写作 + 美股信号）

该项目支持：
- 自动读取热点文本并生成文章；
- 生成美股情绪信号与订单计划（默认 dry-run）；
- 本地/服务器一键启动控制台；
- 打包完整运行环境（可附带 `.venv`）并快速部署。

## 1) 本地一键启动（推荐）

方式 A（根目录按钮脚本）：

```bash
bash start_agent.sh
```

方式 B（脚本目录）：

```bash
bash scripts/one_click_start.sh
```

停止：

```bash
bash stop_agent.sh
# 或
bash scripts/one_click_stop.sh
```

启动后访问：
- `http://127.0.0.1:8787`（本机）
- `http://<服务器IP>:8787`（远程）

页面内提供按钮：
- 一键启动 Agent
- 停止 Agent
- 刷新状态

## 2) 手动运行 Agent

```bash
python3 autopilot_agent.py --input data/hot_trends.json --outdir outputs
```

输出文件：
- `outputs/daily_article.md`
- `outputs/signals.json`
- `outputs/orders.json`

## 3) 打包完整环境（支持本地离线快速部署）

```bash
bash scripts/package_release.sh
```

将生成：
- `dist/autopilot_agent_YYYYMMDD_HHMMSS.tar.gz`

说明：
- 若当前目录存在 `.venv`，打包脚本会自动把 `.venv` 一并打进压缩包（适合同系统快速迁移）。
- 若目标机器系统差异较大，建议删除包内 `.venv` 后再执行 `start.sh`，自动重新创建虚拟环境。

解压后启动：

```bash
tar -xzf dist/autopilot_agent_YYYYMMDD_HHMMSS.tar.gz
cd dist/autopilot_agent_YYYYMMDD_HHMMSS
bash start.sh
```

## 4) Docker 一键部署（可选）

```bash
docker compose up -d --build
```

访问：`http://<服务器IP>:8787`

## 5) 腾讯云服务器部署（101.35.254.128）

### 5.1 上传项目

```bash
rsync -avz --exclude '.git' ./ root@101.35.254.128:/opt/autopilot-agent/
```

### 5.2 服务器执行

```bash
ssh root@101.35.254.128
cd /opt/autopilot-agent
bash start_agent.sh
```

## 6) 参数示例

```bash
python3 autopilot_agent.py \
  --input data/hot_trends.json \
  --outdir outputs \
  --watchlist TSLA NVDA AAPL MSFT META \
  --account-size 10000 \
  --risk-per-trade 1 \
  --max-open-positions 3
```

## 7) 合规说明

- 不提供绕过平台规则、隐藏违规内容等功能；
- 默认仅输出研究与仿真计划；
- 真正实盘执行需你自行接入券商层并承担风险。
