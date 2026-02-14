# Autopilot Trend Agent（热点写作 + 美股信号）

该项目用于在服务器自动运行一个“内容+研究”Agent：
- 根据热点文本（如你整理的 X/推特趋势）自动生成可发布文章；
- 对美股观察池做情绪打分并输出研究信号；
- 生成订单计划（默认仅仿真，不自动实盘下单）。

> 说明：本项目不提供“隐藏违规内容/绕过平台规则”能力。建议完全移除不支持类目并走合规变现。

## 1) 快速运行

```bash
python3 autopilot_agent.py --input data/hot_trends.json --outdir outputs
```

或使用内置模拟数据：

```bash
python3 autopilot_agent.py --mock --outdir outputs
```

输出文件：
- `outputs/daily_article.md`：自动写作稿
- `outputs/signals.json`：美股情绪信号
- `outputs/orders.json`：订单计划（默认 dry_run）

## 2) 参数示例

```bash
python3 autopilot_agent.py \
  --input data/hot_trends.json \
  --outdir outputs \
  --watchlist TSLA NVDA AAPL MSFT META \
  --account-size 10000 \
  --risk-per-trade 1 \
  --max-open-positions 3
```

如果你后续接入券商执行层，可启用“实盘意图输出”（本项目本身不连券商 API）：

```bash
python3 autopilot_agent.py --input data/hot_trends.json --live
```

## 3) 部署到腾讯云（101.35.254.128）

> 你需要先准备服务器 SSH 登录权限（用户名 + 私钥）。

### 3.1 服务器初始化（首次）

```bash
ssh root@101.35.254.128
apt update && apt install -y python3 python3-venv git
mkdir -p /opt/autopilot-agent && cd /opt/autopilot-agent
```

### 3.2 上传代码（本地执行）

```bash
rsync -avz --exclude '.git' ./ root@101.35.254.128:/opt/autopilot-agent/
```

### 3.3 创建运行环境（服务器执行）

```bash
cd /opt/autopilot-agent
python3 -m venv .venv
. .venv/bin/activate
python3 -m py_compile autopilot_agent.py
python3 autopilot_agent.py --input data/hot_trends.json --outdir outputs
```

### 3.4 设置定时任务（服务器执行）

```bash
mkdir -p /opt/autopilot-agent/logs
crontab -e
```

添加：

```cron
0 * * * * cd /opt/autopilot-agent && ./.venv/bin/python autopilot_agent.py --input data/hot_trends.json --outdir outputs >> logs/agent.log 2>&1
```

## 4) 数据格式

`data/hot_trends.json` 示例：

```json
[
  {
    "source": "x",
    "author": "@elonmusk",
    "text": "AI + robotics partnership could unlock new growth cycle for manufacturing.",
    "timestamp": "2026-02-14T08:00:00Z"
  }
]
```

## 5) 合规赚钱路径（不碰受限类目）

1. 用 `daily_article.md` 做多平台内容分发（公众号/小红书/百家号）；
2. 用 `signals.json` 做“市场观察日报”会员订阅；
3. 用 `orders.json` 做纸面交易复盘内容，提高咨询/课程转化；
4. 周度复盘：阅读转化率、策略胜率、最大回撤、用户留存。

## 6) 风控底线

- 单笔风险 <= 总资金 1%；
- 最大同时持仓 <= 3；
- 连续亏损触发“暂停交易 + 仅产出内容”；
- 不将任何单一大 V 发言视为确定性交易信号。
