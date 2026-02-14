#!/usr/bin/env python3
"""Simple self-media writing agent (no platform API)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ArticlePlan:
    topic: str
    audience: str
    pain_point: str
    promise: str
    cta: str


def build_plan(topic: str) -> ArticlePlan:
    return ArticlePlan(
        topic=topic,
        audience="想用 AI 提升工作效率、但缺少可执行方法的上班族与自由职业者",
        pain_point="每天忙到很晚，却总觉得产出不成体系，时间被碎片任务吞噬",
        promise="用 3 个可当天上手的 AI 工作流，把内容产出效率提升到“有节奏、可复用、可变现”",
        cta="评论区回复【清单】领取《一周内容生产 SOP 模板》",
    )


def render_wechat_article(plan: ArticlePlan) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""# 别再瞎忙了：3 个 AI 工作流，让你把内容产出效率拉满（附可执行清单）

> 发布时间：{today}
> 适合人群：{plan.audience}

很多人做自媒体，卡在同一个地方：

- 选题时靠感觉，导致“今天写、明天废”；
- 写作时堆信息，结果读者看完没有行动；
- 发布后不复盘，爆不爆全靠运气。

如果你也有这种状态，你不是不努力，而是缺一套“可重复”的生产系统。

今天我把自己在项目里反复验证的 **3 个 AI 工作流** 拆给你。目标只有一个：
**让你从“随机输出”走向“稳定产出 + 稳定转化”。**

---

## 工作流一：10 分钟生成“可变现”选题池

### 为什么你总是选题焦虑？
因为你在问“写什么”，而不是问“写给谁，解决什么问题，怎么变现”。

### 正确做法（AI 提示词框架）
给 AI 一个结构化任务：

1. 赛道：例如 AI 效率、职场成长、副业变现；
2. 人群：例如新媒体运营、个人 IP 创作者；
3. 目标：高搜索 + 中低竞争 + 可商业化；
4. 输出：选题角度、痛点、承接产品、平台建议。

### 你会得到什么
- 一次性拿到 20~30 个候选题；
- 每个选题都自带“可卖点”；
- 选题从“灵感型”升级成“经营型”。

---

## 工作流二：一稿三改，适配三平台而不机械重复

你不需要“重复写三遍”，你需要“同观点，不同包装”。

### 平台改写最小规则
- **公众号**：深度论证（方法 + 案例 + 清单）；
- **小红书**：结果先行（场景 + 步骤 + 互动钩子）；
- **百家号**：信息增量（背景 + 观点 + 趋势）。

### 实操建议
先产出一个“母稿”，然后让 AI 输出：
- 每个平台 3 个标题；
- 1 篇正文；
- 1 段摘要；
- 5 个标签；
- 2 句评论引导。

这样做的好处是：
**观点统一，文风差异化，平台更容易给自然流量。**

---

## 工作流三：发布前 5 分钟风控审校

很多账号不是死在内容质量，而是死在“表达越界”。

发布前一定让 AI 做一次风控检查，重点扫这 4 类：

1. 夸大承诺（比如“稳赚”“100%有效”）；
2. 敏感建议（医疗、金融、法律）；
3. 侵权风险（图片、引用、商标）；
4. 平台违规词与诱导表达。

你会明显感受到：
- 账号安全性更高；
- 内容可信度更高；
- 用户咨询质量更高。

---

## 一周执行节奏（可直接照抄）

- **周一**：批量生成 20 个选题，筛出 7 个；
- **周二到周四**：每天完成 2 篇母稿 + 三平台改写；
- **周五**：统一排期发布；
- **周末**：复盘“点击率、读完率、收藏率、私信率”。

> 记住：爆款不是一篇文章赌出来的，而是一套系统跑出来的。

---

## 最后一句

{plan.pain_point}。
你真正需要的不是更拼，而是更“系统”。

从今天开始，就用这套三步法：
**选题经营化 → 内容平台化 → 发布合规化**。

{plan.promise}。

**{plan.cta}**
"""


def save_article(text: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an article with a local writing agent")
    parser.add_argument("--topic", default="AI 提效写作", help="Article topic")
    parser.add_argument(
        "--output",
        default="outputs/article_wechat.md",
        help="Output markdown file path",
    )
    args = parser.parse_args()

    plan = build_plan(args.topic)
    article = render_wechat_article(plan)
    out_path = Path(args.output)
    save_article(article, out_path)
    print(f"[writer-agent] generated: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
