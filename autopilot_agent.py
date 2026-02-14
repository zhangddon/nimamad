#!/usr/bin/env python3
"""Autopilot trend agent: content generation + market signal generation.

IMPORTANT:
- This tool does NOT guarantee profits.
- Trading execution is disabled by default (paper mode) to reduce risk.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


POSITIVE_WORDS = {
    "breakthrough",
    "launch",
    "record",
    "growth",
    "partnership",
    "bullish",
    "surge",
    "approved",
    "upgrade",
    "beats",
}

NEGATIVE_WORDS = {
    "ban",
    "lawsuit",
    "hack",
    "delay",
    "bearish",
    "downgrade",
    "crash",
    "fraud",
    "investigation",
    "misses",
}

DEFAULT_WATCHLIST = ["TSLA", "NVDA", "AAPL", "MSFT", "META"]


@dataclass
class TrendItem:
    source: str
    author: str
    text: str
    timestamp: str


@dataclass
class MarketSignal:
    symbol: str
    score: float
    action: str
    confidence: float
    reason: str


@dataclass
class RiskConfig:
    account_size_usd: float = 10000.0
    risk_per_trade_pct: float = 1.0
    max_open_positions: int = 3
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0


def load_trends(path: Path) -> list[TrendItem]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [TrendItem(**item) for item in raw]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def sentiment_score(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    return (pos - neg) / max(len(tokens), 1)


def symbol_mentions(text: str, watchlist: Iterable[str]) -> set[str]:
    upper = text.upper()
    return {s for s in watchlist if s in upper}


def build_signals(trends: list[TrendItem], watchlist: list[str]) -> list[MarketSignal]:
    scores = {symbol: 0.0 for symbol in watchlist}
    reasons = {symbol: [] for symbol in watchlist}

    for item in trends:
        s = sentiment_score(item.text)
        for symbol in symbol_mentions(item.text, watchlist):
            scores[symbol] += s
            reasons[symbol].append(f"{item.author}: {item.text[:80]}")

    output: list[MarketSignal] = []
    for symbol in watchlist:
        score = scores[symbol]
        if score > 0.02:
            action = "BUY"
        elif score < -0.02:
            action = "SELL"
        else:
            action = "HOLD"
        confidence = min(0.9, abs(score) * 8 + 0.1)
        reason = " | ".join(reasons[symbol][:3]) if reasons[symbol] else "no significant mentions"
        output.append(
            MarketSignal(
                symbol=symbol,
                score=round(score, 4),
                action=action,
                confidence=round(confidence, 2),
                reason=reason,
            )
        )
    return output


def position_size_usd(risk: RiskConfig) -> float:
    return round(risk.account_size_usd * (risk.risk_per_trade_pct / 100.0), 2)


def render_article(trends: list[TrendItem], signals: list[MarketSignal]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    hot = "\n".join([f"- {t.author}: {t.text}" for t in trends[:8]])
    picks = sorted(signals, key=lambda s: abs(s.score), reverse=True)[:3]
    picks_md = "\n".join(
        [f"- {s.symbol}: {s.action}（score={s.score}, confidence={s.confidence}）" for s in picks]
    )

    return f"""# 今日热点情报：科技大佬动态与市场机会（自动生成）

> 生成时间：{now}
> 说明：本文由本地 Agent 根据趋势文本自动生成，仅作研究参考，不构成投资建议。

## 1) 热门趋势摘要
{hot}

## 2) 情绪驱动信号（股票）
{picks_md}

## 3) 可执行写作方向
1. 马斯克/科技大佬发声后，相关资产波动逻辑是什么？
2. 如何把“热点”转成“有转化的内容结构”（标题、开头、CTA）？
3. 新手如何建立风控底线（仓位、止损、复盘）？

## 4) 风险提示
- 热点驱动策略容易出现假突破与消息反转；
- 单一热点容易反转，仓位必须分散并设置止损；
- 严禁将模型输出当作确定性盈利信号。
"""


def save_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_text(data: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def build_orders(signals: list[MarketSignal], risk: RiskConfig, dry_run: bool) -> list[dict]:
    per_trade = position_size_usd(risk)
    candidates = [s for s in signals if s.action in {"BUY", "SELL"}]
    candidates.sort(key=lambda s: s.confidence, reverse=True)
    candidates = candidates[: risk.max_open_positions]

    orders = []
    for s in candidates:
        orders.append(
            {
                "symbol": s.symbol,
                "side": s.action,
                "notional_usd": per_trade,
                "stop_loss_pct": risk.stop_loss_pct,
                "take_profit_pct": risk.take_profit_pct,
                "dry_run": dry_run,
                "note": "paper mode" if dry_run else "requires broker integration",
            }
        )
    return orders


def generate_mock_trends(seed: int, count: int = 12) -> list[TrendItem]:
    random.seed(seed)
    templates = [
        ("x", "@elonmusk", "New partnership discussion around AI chips and robotics."),
        ("x", "@techinsider", "NVDA beats expectations with strong growth and record demand."),
        ("x", "@marketwatcher", "AAPL supplier upgrade may improve shipment outlook this quarter."),
        ("x", "@macroalpha", "TSLA launch event may drive sentiment surge."),
        ("x", "@streetalpha", "MSFT announces enterprise AI partnership and cloud growth guidance."),
        ("x", "@growthdaily", "META advertising recovery beats analyst expectations."),
    ]

    output: list[TrendItem] = []
    for i in range(count):
        source, author, text = random.choice(templates)
        output.append(
            TrendItem(
                source=source,
                author=author,
                text=text,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Autopilot trend agent (content + stock signals)")
    parser.add_argument("--input", help="JSON trend input path")
    parser.add_argument("--outdir", default="outputs", help="Output directory")
    parser.add_argument("--watchlist", nargs="*", default=DEFAULT_WATCHLIST)
    parser.add_argument("--account-size", type=float, default=10000)
    parser.add_argument("--risk-per-trade", type=float, default=1.0)
    parser.add_argument("--max-open-positions", type=int, default=3)
    parser.add_argument("--live", action="store_true", help="Enable live intent output (still needs broker integration)")
    parser.add_argument("--mock", action="store_true", help="Use mock trends if no input")
    args = parser.parse_args()

    if args.input:
        trends = load_trends(Path(args.input))
    elif args.mock:
        trends = generate_mock_trends(seed=42)
    else:
        raise SystemExit("Provide --input <json> or use --mock")

    signals = build_signals(trends, args.watchlist)
    risk = RiskConfig(
        account_size_usd=args.account_size,
        risk_per_trade_pct=args.risk_per_trade,
        max_open_positions=args.max_open_positions,
    )
    dry_run = not args.live
    orders = build_orders(signals, risk, dry_run=dry_run)

    outdir = Path(args.outdir)
    article = render_article(trends, signals)
    save_text(article, outdir / "daily_article.md")
    save_json([asdict(s) for s in signals], outdir / "signals.json")
    save_json(orders, outdir / "orders.json")

    print(f"[autopilot-agent] article: {outdir / 'daily_article.md'}")
    print(f"[autopilot-agent] signals: {outdir / 'signals.json'}")
    print(f"[autopilot-agent] orders : {outdir / 'orders.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
