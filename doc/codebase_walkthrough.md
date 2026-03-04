# NewsPilot 代码工程走读报告

## 一、项目概述

**NewsPilot** 是一套基于大语言模型（LLM）的**自动化全球新闻情报分析系统**。核心定位是将海量全球新闻转化为**个性化、可执行的洞察与建议**，充当 7×24 小时智能情报助理，能够理解用户的职业、持仓和兴趣，提供定制化情报服务。

系统具备**双轨情报能力**：

- **Track A（通用日报）**：自动聚合十大行业板块（政策法规、宏观经济、金融市场、公司商业、科技前沿、能源大宗、地缘政治、社会安全、环境气候、医疗健康），生成专业级行业深度研报。
- **Track B（个性化洞察）**：基于用户画像（持仓/职业/兴趣），检索相关新闻生成专属的投资建议和行动指南。

**版本**：V0.1 MVP | **许可证**：MIT

---

## 二、工程目录结构

```
NewsPilot/
├── config/                          # 配置中心
│   ├── keys.py                      # [.gitignore] API 密钥（OpenAI/DeepSeek/Gemini/Qwen/NewsAPI）
│   ├── prompts.py                   # LLM 提示词库（6大类 Prompt 模板）
│   ├── settings.json                # 系统通用配置（预留）
│   ├── user_profile.json            # [.gitignore] 默认用户画像
│   └── docker/                      # Docker 编排（PostgreSQL + RSSHub，Win/Linux 双版本）
│
├── core/                            # 领域核心（数据契约层）
│   ├── news_schemas.py              # 核心数据模型（Pydantic）：Raw/Refined/SupportingDoc
│   └── user_schemas.py              # 用户画像模型（预留）
│
├── src/                             # 源代码
│   ├── module/                      # 基础设施工具
│   │   ├── init_client.py           # LLM 客户端工厂（GPT/DeepSeek/Gemini/Qwen）
│   │   └── tools.py                 # 通用工具：UUIDv7、URL提取、文本规范化
│   │
│   ├── data_acquisition/            # 数据采集层
│   │   ├── orchestrator.py          # 按需采集编排器
│   │   ├── daemon_orchestrator.py   # 守护进程编排器（长期驻留服务）
│   │   ├── fetchers/                # 数据抓取器
│   │   │   ├── base_fetcher.py      # 抓取器抽象基类
│   │   │   ├── newsapi_fetcher.py   # NewsAPI 适配器
│   │   │   ├── rsshub_fetcher.py    # RSSHub 适配器（6个RSS源）
│   │   │   └── reuters_fetcher.py   # Reuters 抓取器（预留）
│   │   ├── processors/              # 数据处理流水线
│   │   │   ├── pipeline.py          # 处理编排：翻译→摘要→向量化→对齐
│   │   │   └── module/
│   │   │       ├── translator.py    # 翻译模块（DeepSeek/Qwen）
│   │   │       ├── summarizer.py    # 摘要+分类+评分模块（DeepSeek）
│   │   │       ├── embedding.py     # 向量化模块（Qwen text-embedding-v4）
│   │   │       └── normalize.py     # 数据对齐模块
│   │   └── module/                  # 采集辅助工具
│   │       ├── download.py          # Playwright 爬虫（JS渲染页面）
│   │       ├── get_article_from_url.py  # URL 正文抓取
│   │       ├── get_content.py       # 批量内容丰富
│   │       └── paser_html.py        # HTML 解析器
│   │
│   ├── intelligence/                # AI 智能分析层
│   │   ├── new_analyzer.py          # 通用日报引擎（NewsAnalyzer）
│   │   └── insight_generator.py     # 个性化洞察引擎（InsightGenerator）
│   │
│   ├── storage/                     # 持久化层
│   │   ├── db_config.py             # 数据库连接管理器
│   │   ├── models.py                # SQLAlchemy ORM 模型（4张表）
│   │   └── repository.py           # 仓储模式 CRUD 封装
│   │
│   └── workflows/                   # 入口点/工作流
│       ├── run_news_service.py      # 全自动服务入口
│       ├── run_daily_report.py      # 通用日报入口
│       └── main_pipeline.py         # 个性化洞察入口
│
├── data/                            # 数据存储
│   ├── daily_reports/               # 通用日报输出
│   └── personal_report/             # 个性化报告输出
│
└── doc/                             # 文档
```

---

## 三、核心模块实现原理

### 3.1 数据采集（Fetcher）

采用**策略模式**，所有 Fetcher 继承 `BaseFetcher` 抽象基类：

```
BaseFetcher（抽象基类）
  ├── fetch_raw_data()         → 异步获取原始数据（字典列表）
  ├── normalize_data()         → 单条数据标准化为 NewsItemRawSchema
  └── fetch_and_normalize()    → 模板方法：抓取 + 标准化
```

| Fetcher | 实现细节 |
|---------|----------|
| **NewsAPIFetcher** | 使用 `newsapi_python` SDK，按类别（business/science/technology）和指定来源（reuters/bloomberg 等 7 个）获取头条新闻 |
| **RSSHubFetcher** | 通过 `aiohttp` + `feedparser` 异步获取 RSS 订阅，支持 6 个源（Reuters、Bloomberg、东方财富、财联社、BBC、FT中文网），含重试和指数退避逻辑 |

每条新闻通过 `generate_uuid7()` 生成时间有序的唯一 ID（UUIDv7 模拟），确保数据库写入性能。

### 3.2 数据处理流水线（Pipeline）

`NewsProcessingPipeline` 串联四个处理步骤：

```
原始新闻列表 (NewsItemRawSchema[])
    │
    ▼ [1] Translator（翻译）
    │   使用 DeepSeek/Qwen，将标题+摘要+正文批量翻译为中文
    │   并发控制：BoundedSemaphore(5)，带 tqdm 进度条
    │
    ▼ [2] Summarizer（摘要+分类+评分）
    │   使用 DeepSeek，一次性完成：
    │   - 生成中文摘要（abstract）
    │   - 选择 1-3 个新闻类别（10 大分类 + other）
    │   - 综合评分 0-100（信息完整性/可信度/重要性/可读性）
    │   含严格 JSON 校验和重试逻辑
    │
    ▼ [3] EmbeddingGenerator（向量化）
    │   使用 Qwen text-embedding-v4，生成 1024 维向量
    │   用于后续语义检索和去重
    │
    ▼ [4] align_news_lists（对齐）
        将翻译后的 Raw 和摘要后的 Refined 按 unique_id 一一匹配
        将分类和评分回写到 Raw 上
        输出：(aligned_raw[], aligned_refined[])
```

### 3.3 编排器（Orchestrator）

系统提供两种编排模式：

#### 按需编排 — `NewsDataOrchestrator`

- 同步接口 `run()`，内部调 `asyncio.run()`
- 适用于 `main_pipeline.py` 的一次性运行场景

#### 守护进程编排 — `DaemonOrchestrator`

- 两个并发协程通过 `asyncio.gather()` 同时运行：
  - **Acquisition Loop**（低频，默认 120 分钟）：抓取 → 去重（staging 表 + raw 表双重检查）→ 入暂存区
  - **Processing Worker**（高频，默认 60 秒轮询）：拉取 pending → 标记 processing → 调用 Pipeline → 归档 → 清理
- 完整状态机：`pending → processing → completed / failed`
- 异常恢复：启动时自动重置 `processing / retry_later` 状态的卡死任务

### 3.4 智能分析（Intelligence）

#### NewsAnalyzer — 通用日报引擎

1. 从数据库拉取指定时间窗口的 RefinedNews
2. 按 `categories` 字段分类到 10 大板块
3. **并行**（`asyncio.gather`）为每个板块调用 LLM 生成分析
4. Prompt 要求 LLM 输出严格 JSON 结构，包含：
   - `meta`（元信息）
   - `overall_commentary`（重点综述）
   - `core_events[]`（核心情报：事实层→反应层→研判层，含反向推演）
   - `industry_scan[]`（行业扫描）
   - `market_monitor`（市场监测）
5. 将 JSON 渲染为结构化 Markdown 报告
6. 使用 Gemini-3-pro-preview + Thinking（思维链）+ Google Search 工具

#### InsightGenerator — 个性化洞察引擎

1. 从文件加载用户画像（持仓、职业、兴趣等）
2. 格式化新闻上下文
3. 调用 Gemini Thinking 模型（temperature=0.7），启用 Google Search
4. Prompt 定位为"资深新闻政策解读与个人发展战略顾问"
5. 输出：值得关注的机会 + 潜在风险提示 + 深度阅读推荐

### 3.5 持久化层（Storage）

基于 **PostgreSQL + SQLAlchemy ORM + 仓储模式**：

```
raw_news_staging  ──(处理后归档)──→  raw_news  ←──(1:1外键)──  refined_news
                                                                    ↑
                                                          supporting_documents
```

4 张数据库表：

| 表名 | 作用 |
|------|------|
| `raw_news_staging` | 暂存区/队列表，实现采集与处理解耦 |
| `raw_news` | 原始新闻永久表 |
| `refined_news` | 精炼新闻表（含摘要、分类、评分、向量） |
| `supporting_documents` | 支撑文档表 |

`StorageRepository` 封装所有 CRUD 操作，支持外部事务传入，含 upsert、时间范围查询、URL 去重检查、Staging 队列操作等。

---

## 四、整体数据流

### 4.1 全自动服务模式（`run_news_service.py`）

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DaemonOrchestrator.start()                      │
│                                                                     │
│  ┌──── acquisition_loop() ────┐    ┌─── processing_worker() ───┐   │
│  │  每 120 分钟执行一次       │    │  每 60 秒轮询一次         │   │
│  │                            │    │                            │   │
│  │  NewsAcquisitionService    │    │  fetch_staging(pending)    │   │
│  │    ├─ NewsAPIFetcher       │    │       │                    │   │
│  │    └─ RSSHubFetcher        │    │  mark → processing        │   │
│  │       ├─ Reuters RSS       │    │       │                    │   │
│  │       ├─ Bloomberg RSS     │    │  NewsProcessingPipeline   │   │
│  │       ├─ Eastmoney RSS     │    │    ├─ Translator (Qwen)   │   │
│  │       ├─ CLS RSS           │    │    ├─ Summarizer (DSK)    │   │
│  │       ├─ BBC RSS           │    │    ├─ Embedding (Qwen)    │   │
│  │       └─ FTChinese RSS     │    │    └─ align_news_lists    │   │
│  │         │                  │    │       │                    │   │
│  │  去重(staging+raw 双重)    │    │  归档 → raw_news 表       │   │
│  │         │                  │    │  归档 → refined_news 表   │   │
│  │  写入 → raw_news_staging   │    │  删除 staging 记录        │   │
│  └────────────────────────────┘    └────────────────────────────┘   │
│                                                                     │
│                     asyncio.gather(并发运行)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 通用日报模式（`run_daily_report.py`）

```
run_daily_report.py
    │
    ▼ 计算时间窗口(昨天 8:00 → 今天 8:00)
    │
    ▼ NewsAnalyzer.generate_all_daily_reports()
       │
       ├─ _fetch_news()  ←── StorageRepository.list_refined_news()  ←── PostgreSQL
       ├─ _classify_news()  →  10 大板块分类
       ├─ asyncio.gather(并行 10 个板块)
       │   └─ _generate_single_category_content()
       │       ├─ 构造 Prompt
       │       ├─ _call_llm()  →  Gemini-3-pro (Thinking + Search)
       │       ├─ JSON 校验 + 重试(最多 3 次)
       │       └─ _render_json_to_md()  →  结构化 Markdown
       └─ _save_md_file()  →  data/daily_reports/YYYY-MM-DD/{category}.md
```

### 4.3 个性化洞察模式（`main_pipeline.py`）

```
main_pipeline.py → NewsPilotPipeline.run()
    │
    ├─ [Step 1] NewsDataOrchestrator.run()
    │   ├─ NewsAcquisitionService.run()    → 抓取原始新闻
    │   └─ NewsProcessingService.run()     → 翻译 + 摘要 + 向量化
    │
    ├─ 保存中间结果: raw_news.json / translated_news.json / summarized_news.json
    │
    ├─ [Step 2] InsightGenerator.generate_insights()
    │   ├─ 加载用户画像 (user_profile.json)
    │   ├─ 格式化新闻上下文
    │   └─ 调用 Gemini Thinking  →  个性化建议
    │
    └─ [Step 3] 保存结果
        ├─ personalized_insights.json
        └─ daily_report.md
```

---

## 五、LLM 多模型协作策略

```
LLMClientFactory
    ├─ GPT      → AsyncOpenAI(api.openai.com)           ← 预留
    ├─ DeepSeek → AsyncOpenAI(api.deepseek.com)          ← 翻译 & 摘要（高性价比）
    ├─ Qwen     → AsyncOpenAI(dashscope.aliyuncs.com)    ← 翻译（备选）& Embedding
    └─ Gemini   → genai.Client(google)                   ← 日报分析 & 个性化洞察（高质量推理）
```

| 模型 | 用途 | 选型理由 |
|------|------|----------|
| DeepSeek V3 (`deepseek-chat`) | 翻译、摘要、分类、评分 | 高性价比，处理高频低成本任务 |
| Qwen (`qwen-flash` / `text-embedding-v4`) | 翻译（备选）、向量化嵌入（1024 维） | 中文能力强，向量质量高 |
| Gemini 3 Pro Preview (Thinking) | 日报生成、个性化洞察 | 高质量推理 + 内置 Google Search |

---

## 六、技术栈总览

| 领域 | 技术选型 |
|------|----------|
| 编程语言 | Python 3.12+，全面异步化（asyncio） |
| LLM SDK | `openai>=1.0.0`（兼容 DeepSeek/Qwen）、`google-genai>=0.3.0` |
| 数据采集 | `newsapi_python`、`feedparser`、`aiohttp`、`playwright` |
| 正文提取 | `trafilatura`（主力）、`readability-lxml`（兜底）、`beautifulsoup4` |
| 数据建模 | `pydantic>=2.0.0` |
| 数据库 | PostgreSQL 16 + `SQLAlchemy>=2.0.0` + `psycopg[binary]>=3.1.0` |
| 基础设施 | Docker / Docker Compose（PostgreSQL + RSSHub） |
| 进度展示 | `tqdm` 异步进度条 |

---

## 七、架构亮点

1. **分层解耦**：数据采集（Fetcher）→ 数据处理（Pipeline）→ 智能分析（Intelligence）→ 工作流（Workflow）四层清晰分离。
2. **双模式运行**：守护进程服务（7×24h 后台常驻）和按需任务（手动/定时触发）并存。
3. **Staging 队列模式**：通过 `raw_news_staging` 暂存表实现采集和处理的解耦，支持失败重试和状态追踪。
4. **多模型协作**：DeepSeek 处理高频低成本任务、Qwen 处理向量化、Gemini Thinking 处理高质量分析，各取所长。
5. **LLM 输出可靠性**：JSON 校验 + 重试逻辑 + 字段约束验证，确保结构化输出稳定。
6. **策略模式扩展**：Fetcher 基于抽象基类，新增数据源只需实现接口即可接入。

## 八、待完善事项

| 项目 | 说明 |
|------|------|
| `reuters_fetcher.py` | 空文件，Reuters 直接抓取功能预留 |
| `user_schemas.py` | 空文件，用户画像模型未独立定义 |
| `settings.json` | 为空，部分配置硬编码在代码中 |
| 路径硬编码 | `insight_generator.py` 中用户画像路径硬编码为 Windows 绝对路径，跨平台兼容性待优化 |
| 内容丰富 | `get_content.py` 的全文抓取功能在 fetcher 中被注释掉，未启用 |
