#!/usr/bin/env python3
"""自动写作工具流：采集热点新闻并生成公众号风格稿件。"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from typing import Iterable


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
DEFAULT_OUTPUT_DIR = pathlib.Path("output")
DEFAULT_LANG = "zh-CN"
DEFAULT_COUNTRY = "CN"
DEFAULT_EDITION = "CN:zh-Hans"


KEYWORDS = [
    "Elon Musk",
    "马斯克",
    "AI",
    "人工智能",
    "科技巨头",
    "富豪 争议",
    "娱乐 八卦",
    "社会 热点",
]


COLUMN_DEFINITIONS = {
    "global_digest": {
        "title": "栏目1：每日全球资讯",
        "style": "简报体 + 深度点评，强调事实、影响和后续观察点",
    },
    "meme_digest": {
        "title": "栏目2：每日玩梗",
        "style": "轻松、犀利、可传播，适合社交媒体转发，但避免低俗与失实",
    },
}


@dataclass
class NewsItem:
    title: str
    link: str
    published: str
    source: str
    keyword: str
    score: int


def build_demo_news() -> list[NewsItem]:
    """离线演示数据：用于网络受限时的稳定试运行。"""
    return [
        NewsItem(
            title="马斯克再谈 AI 监管边界，科技圈争议升级",
            link="https://example.com/news/musk-ai-regulation",
            published="Mon, 17 Feb 2026 08:00:00 GMT",
            source="DemoWire",
            keyword="马斯克",
            score=96,
        ),
        NewsItem(
            title="全球科技巨头加码 AI 投资，算力争夺进入白热化",
            link="https://example.com/news/ai-capex-race",
            published="Mon, 17 Feb 2026 09:00:00 GMT",
            source="TechPulse",
            keyword="AI",
            score=92,
        ),
        NewsItem(
            title="富豪言论引发舆论两极化，社交平台热议不断",
            link="https://example.com/news/billionaire-controversy",
            published="Mon, 17 Feb 2026 10:00:00 GMT",
            source="GlobalView",
            keyword="富豪 争议",
            score=88,
        ),
        NewsItem(
            title="头部综艺嘉宾发言冲上热搜，娱乐营销再成焦点",
            link="https://example.com/news/entertainment-trending",
            published="Mon, 17 Feb 2026 11:00:00 GMT",
            source="娱记快报",
            keyword="娱乐 八卦",
            score=83,
        ),
        NewsItem(
            title="社会议题短视频爆火，平台治理与表达自由再被讨论",
            link="https://example.com/news/social-platform-debate",
            published="Mon, 17 Feb 2026 12:00:00 GMT",
            source="社会观察局",
            keyword="社会 热点",
            score=81,
        ),
    ]


class NewsCollector:
    def __init__(self, language: str = DEFAULT_LANG, country: str = DEFAULT_COUNTRY, edition: str = DEFAULT_EDITION):
        self.language = language
        self.country = country
        self.edition = edition

    def _build_url(self, keyword: str, when_hours: int = 24) -> str:
        query = f"{keyword} when:{when_hours}h"
        params = {
            "q": query,
            "hl": self.language,
            "gl": self.country,
            "ceid": self.edition,
        }
        return f"{GOOGLE_NEWS_RSS}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _compute_score(title: str, keyword: str) -> int:
        score = 50
        title_lower = title.lower()
        keyword_lower = keyword.lower()

        hot_signals = {
            "马斯克": 20,
            "elon": 20,
            "争议": 15,
            "controvers": 15,
            "ai": 10,
            "人工智能": 10,
            "首发": 8,
            "突发": 8,
            "财报": 8,
            "收购": 8,
            "绯闻": 6,
            "封禁": 8,
            "监管": 10,
        }

        for signal, points in hot_signals.items():
            if signal in title_lower:
                score += points

        if keyword_lower in title_lower:
            score += 12

        if any(x in title_lower for x in ["live", "最新", "just in", "breaking"]):
            score += 6

        return min(score, 100)

    def fetch_by_keyword(self, keyword: str, timeout: int = 12) -> list[NewsItem]:
        url = self._build_url(keyword)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AutoWriterBot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read()

        root = ET.fromstring(payload)
        items: list[NewsItem] = []
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            published = (item.findtext("pubDate") or "").strip()
            source_elem = item.find("source")
            source = source_elem.text.strip() if source_elem is not None and source_elem.text else "Unknown"

            if not title or not link:
                continue

            items.append(
                NewsItem(
                    title=title,
                    link=link,
                    published=published,
                    source=source,
                    keyword=keyword,
                    score=self._compute_score(title=title, keyword=keyword),
                )
            )
        return items

    def collect_hot_news(self, keywords: Iterable[str], max_items: int = 30) -> list[NewsItem]:
        merged: dict[str, NewsItem] = {}
        for keyword in keywords:
            try:
                news_items = self.fetch_by_keyword(keyword)
            except Exception as exc:  # noqa: BLE001 - 容错用于抓取失败继续流程
                print(f"[WARN] 抓取关键词失败: {keyword} -> {exc}")
                continue

            for item in news_items:
                if item.link not in merged or item.score > merged[item.link].score:
                    merged[item.link] = item

        ranking = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return ranking[:max_items]


class ArticleWriter:
    def __init__(self, brand_name: str = "热点放大镜"):
        self.brand_name = brand_name

    @staticmethod
    def _group_news(items: list[NewsItem]) -> dict[str, list[NewsItem]]:
        tech, society, entertainment = [], [], []
        for item in items:
            title = item.title.lower()
            if any(k in title for k in ["ai", "人工智能", "科技", "tesla", "x.com", "苹果", "谷歌", "musk", "马斯克"]):
                tech.append(item)
            elif any(k in title for k in ["娱乐", "明星", "电影", "音乐", "综艺", "网红", "八卦"]):
                entertainment.append(item)
            else:
                society.append(item)
        return {"tech": tech, "society": society, "entertainment": entertainment}

    def _render_global_digest(self, items: list[NewsItem], today: str) -> str:
        groups = self._group_news(items)
        top_items = items[:8]

        sections = [f"# {COLUMN_DEFINITIONS['global_digest']['title']}（{today}）", ""]
        sections.append("## 今日焦点导语")
        sections.append("今天的全球热点呈现出三个关键词：**技术竞速、社会情绪、流量叙事**。下面用最短时间看懂最关键动态。")
        sections.append("")

        for idx, item in enumerate(top_items, start=1):
            sections.extend(
                [
                    f"### {idx}. {item.title}",
                    f"- 来源：{item.source}",
                    f"- 热度分：{item.score}/100",
                    f"- 链接：{item.link}",
                    "- 影响点评：这条消息可能影响相关行业预期和舆论走向，建议继续观察后续官方回应与市场反馈。",
                    "",
                ]
            )

        sections.append("## 板块分布")
        sections.append(f"- 科技类：{len(groups['tech'])} 条")
        sections.append(f"- 社会类：{len(groups['society'])} 条")
        sections.append(f"- 娱乐类：{len(groups['entertainment'])} 条")
        sections.append("")
        sections.append("## 明日观察点")
        sections.append("1. 马斯克及相关平台是否再发争议言论。")
        sections.append("2. AI 公司是否发布新产品或合作。")
        sections.append("3. 娱乐与社会事件是否继续跨圈层发酵。")
        return "\n".join(sections)

    def _render_meme_digest(self, items: list[NewsItem], today: str) -> str:
        top_items = items[:6]
        sections = [f"# {COLUMN_DEFINITIONS['meme_digest']['title']}（{today}）", ""]
        sections.append("## 今日梗概：世界是个巨大的评论区")
        sections.append("今天我们继续坚持三件事：**盯马斯克、看热搜、提炼可转发的梗**。")
        sections.append("")

        for idx, item in enumerate(top_items, start=1):
            sections.extend(
                [
                    f"### 梗位 {idx}：{item.title}",
                    f"- 一句话总结：这事儿的传播点在于『{item.keyword} + 情绪冲突』。",
                    "- 玩梗文案：",
                    f"  - 正经版：当{item.keyword}遇上全网围观，信息差就是今天的流量密码。",
                    "  - 沙雕版：网友：我只是吃瓜；平台：你已经在参与历史。",
                    f"- 原文链接：{item.link}",
                    "",
                ]
            )

        sections.append("## 发布建议")
        sections.append("- 时间：午间 12:00 或晚间 20:00。")
        sections.append("- 结构：先上情绪梗，再补背景，最后抛互动问题。")
        sections.append("- 互动问题模板：『这条新闻你站哪边？留言区见。』")
        return "\n".join(sections)

    def generate_columns(self, items: list[NewsItem]) -> dict[str, str]:
        today = dt.datetime.now().strftime("%Y-%m-%d")
        return {
            "global_digest": self._render_global_digest(items, today),
            "meme_digest": self._render_meme_digest(items, today),
        }


def save_json(items: list[NewsItem], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(x) for x in items], ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: pathlib.Path) -> list[NewsItem]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [NewsItem(**row) for row in raw]


def save_markdown(outputs: dict[str, str], output_dir: pathlib.Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, text in outputs.items():
        file_path = output_dir / f"{key}.md"
        file_path.write_text(text, encoding="utf-8")
        print(f"[OK] 已输出: {file_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="自动写作工具流：自动抓热点并生成公众号栏目稿件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            使用示例:
              python auto_writer_flow.py run
              python auto_writer_flow.py run --demo
              python auto_writer_flow.py collect --max-items 40
              python auto_writer_flow.py write --input output/hot_news.json
            """
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="抓取热点新闻")
    collect.add_argument("--max-items", type=int, default=30)
    collect.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR / "hot_news.json"))
    collect.add_argument("--demo", action="store_true", help="使用内置演示新闻，不访问外网")

    write = sub.add_parser("write", help="根据抓取结果写两大栏目")
    write.add_argument("--input", default=str(DEFAULT_OUTPUT_DIR / "hot_news.json"))
    write.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))

    run = sub.add_parser("run", help="抓取 + 写稿一键执行")
    run.add_argument("--max-items", type=int, default=30)
    run.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    run.add_argument("--demo", action="store_true", help="使用内置演示新闻，不访问外网")

    return parser


def run_collect(args: argparse.Namespace) -> None:
    if args.demo:
        items = build_demo_news()[: args.max_items]
    else:
        collector = NewsCollector()
        items = collector.collect_hot_news(KEYWORDS, max_items=args.max_items)
        if not items:
            print("[WARN] 未抓到在线新闻，自动回退到 demo 数据以保障流程可运行。")
            items = build_demo_news()[: args.max_items]

    output_path = pathlib.Path(args.output)
    save_json(items, output_path)
    print(f"[OK] 已抓取 {len(items)} 条热点 -> {output_path}")


def run_write(args: argparse.Namespace) -> None:
    input_path = pathlib.Path(args.input)
    items = load_json(input_path)
    writer = ArticleWriter()
    outputs = writer.generate_columns(items)
    save_markdown(outputs, pathlib.Path(args.output_dir))


def run_all(args: argparse.Namespace) -> None:
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.demo:
        items = build_demo_news()[: args.max_items]
    else:
        collector = NewsCollector()
        items = collector.collect_hot_news(KEYWORDS, max_items=args.max_items)
        if not items:
            print("[WARN] 未抓到在线新闻，自动回退到 demo 数据以保障流程可运行。")
            items = build_demo_news()[: args.max_items]

    data_path = output_dir / "hot_news.json"
    save_json(items, data_path)

    writer = ArticleWriter()
    outputs = writer.generate_columns(items)
    save_markdown(outputs, output_dir)

    print("[DONE] 工具流执行完成")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "collect":
        run_collect(args)
    elif args.command == "write":
        run_write(args)
    else:
        run_all(args)


if __name__ == "__main__":
    if os.getenv("TZ") is None:
        os.environ["TZ"] = "Asia/Shanghai"
    main()
