# nimamad

自动写作工具流（微信公众号方向）示例项目：
- 自动搜索全球热点新闻（优先科技/社会/娱乐）
- 重点关注马斯克动态、富豪争议、AI 行业与流量事件
- 自动产出两个固定栏目：
  1. 每日全球资讯
  2. 每日玩梗

## 在 ChatGPT（Codex）中如何运行

如果你在 ChatGPT 的代码运行环境里使用本项目，可以直接让助手执行：

```bash
python auto_writer_flow.py run --demo
```

说明：
- `--demo` 会使用内置热点样例数据，不依赖外网，适合在受限网络环境稳定试跑。
- 如果不加 `--demo`，会尝试在线抓取 Google News RSS；在线抓取失败时，脚本会自动回退到 demo 数据继续产出。

## 快速开始

```bash
python auto_writer_flow.py run
```

运行后会在 `output/` 目录下生成：
- `hot_news.json`：去重+打分后的热点素材池
- `global_digest.md`：栏目1《每日全球资讯》
- `meme_digest.md`：栏目2《每日玩梗》

## 命令说明

### 1）只抓取热点

```bash
python auto_writer_flow.py collect --max-items 40
```

离线演示模式：

```bash
python auto_writer_flow.py collect --max-items 40 --demo
```

### 2）只写稿（使用已有热点数据）

```bash
python auto_writer_flow.py write --input output/hot_news.json
```

### 3）一键执行抓取+写稿

```bash
python auto_writer_flow.py run --max-items 30
```

离线演示模式：

```bash
python auto_writer_flow.py run --max-items 30 --demo
```

## 工具流设计

1. **热点搜索层**
   - 使用 Google News RSS 搜索多个关键词。
   - 默认关键词包含：`Elon Musk`、`马斯克`、`人工智能`、`富豪 争议`、`娱乐 八卦` 等。

2. **筛选与排序层**
   - 按标题信号词（争议/监管/收购/突发等）计算热度分。
   - 按链接去重并取高分版本。

3. **内容生产层**
   - 栏目1：偏“事实 + 影响点评 + 明日观察点”。
   - 栏目2：偏“可传播梗 + 互动话题 + 发布时间建议”。

## 后续扩展建议

- 增加更多栏目模板（例如：`每日 AI 工具实测`、`每周商业人物复盘`）。
- 接入公众号自动排版与发布 API（内部系统或第三方工具）。
- 引入大模型 API，对点评和玩梗文案做个性化风格强化。
- 增加敏感词审查和事实核验流程，提升可发布性。
