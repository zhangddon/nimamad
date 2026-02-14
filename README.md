# Autopilot Trend Agent（热点写作 + 信号生成）

这个项目现在提供一个可在服务器自动运行的 Agent：
- 根据趋势文本（例如你抓取/整理的推特热点）自动生成文章；
- 对股票/虚拟币做情绪打分并给出信号；
- 输出订单计划（默认仅仿真，不直接下单）。

> ⚠️ 不保证盈利；高波动市场有重大风险。默认 `paper mode`，请先长期回测再考虑实盘。

## 1) 快速开始

```bash
python3 autopilot_agent.py --input data/hot_trends.json --outdir outputs
```

或使用内置 mock 数据：

```bash
python3 autopilot_agent.py --mock --outdir outputs
```

生成文件：
- `outputs/daily_article.md`：自动写作稿
- `outputs/signals.json`：情绪信号
- `outputs/orders.json`：订单计划（默认 dry_run）

## 2) 运行参数

```bash
python3 autopilot_agent.py \
  --input data/hot_trends.json \
  --outdir outputs \
  --watchlist TSLA NVDA BTC ETH DOGE \
  --account-size 10000 \
  --risk-per-trade 1 \
  --max-open-positions 3
```

开启“实盘意图输出”（仍需你自己接券商/交易所执行层）：

```bash
python3 autopilot_agent.py --input data/hot_trends.json --live
```

## 3) 自动运行（服务器）

### 3.1 cron 每小时执行一次

```bash
crontab -e
```

加入：

```cron
0 * * * * cd /workspace/nimamad && /usr/bin/python3 autopilot_agent.py --input data/hot_trends.json --outdir outputs >> logs/agent.log 2>&1
```

### 3.2 systemd（推荐生产）

可拆成 `agent.service` + `agent.timer`，实现开机自启、失败重启与日志统一收集。

## 4) 数据输入格式

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

## 5) 建议的赚钱路径（合规版）

1. 用 `daily_article.md` 发公众号/小红书/百家号，赚流量与咨询；
2. 用 `signals.json` 做“研究复盘内容”，卖会员通讯或策略课；
3. `orders.json` 先做纸面交易，连续稳定后再小资金实盘；
4. 固定周复盘：胜率、盈亏比、最大回撤、内容转化率。

## 6) 风控底线（必须）

- 单笔风险不超过总资金 1%；
- 最大同时持仓不超过 3 个；
- 每天达到亏损阈值立即停止；
- 不把任何单一“大佬发言”当确定性信号。
