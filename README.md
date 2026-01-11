# 📰 NewsPilot - 个性化新闻分析系统

一个基于大语言模型（LLM）的智能新闻分析系统，自动抓取、翻译、分析每日新闻，并结合个人画像生成**个性化、可执行的洞察与建议**。

## ✨ 核心特性

- ✅ **多源新闻采集**：支持 NewsAPI、Reuters 等多渠道新闻源，自动去重与标准化存储
- ✅ **智能内容处理**：
  - 自动翻译（支持 DeepSeek/GPT 多模型切换）
  - 智能摘要（保留关键信息，去除冗余）
  - 异步批处理（5并发限流，高效处理大量新闻）
- ✅ **个性化洞察引擎**：基于用户画像（职业、兴趣、资产配置等），使用 Gemini 深度思考模型生成可行性建议
- ✅ **完整工作流程**：新闻采集 → 翻译 → 摘要 → 洞察生成 → Markdown 报告输出
- ✅ **模块化架构**：清晰分层设计，易于扩展和维护
- 🚧 **World Engine**（规划中）：长期记忆与事件关联分析
- 🚧 **RAG 检索增强**（规划中）：结合历史信息提供更深层次洞察

## 📊 Demo 展示

系统每日自动生成个性化报告，包含：
- 📈 **个性化洞察**：基于用户画像的机会分析、风险提示、行动建议
- 📰 **新闻摘要列表**：经过翻译和摘要的核心新闻
- 📚 **深度阅读推荐**：根据用户背景推荐最相关的新闻

示例报告：[data/reports/2026-01-11/daily_report.md](data/reports/2026-01-11/daily_report.md)

**示例洞察片段**：
```markdown
## 🎯 值得关注的机会

### 1. 捕捉"AI算力能源化"的投资与职业红利
- **机会描述**：Meta与OpenAI正疯狂签署核能与能源基础设施协议...
- **相关性说明**：你持有美股 QQQ (纳指ETF)，但目前AI的瓶颈已从"芯片"转向"电力/能源"...
- **建议行动**：
    - 投资调整：考虑配置清洁能源或公用事业ETF...
    - 职业发展：关注边缘计算优化或低功耗算法项目...
```

## 🏗️ 系统架构

系统采用三层架构，核心流程如下：

```
┌─────────────────────────────────────────────────────────────┐
│                   主流程 (NewsPilotPipeline)                 │
│                  workflows/main_pipeline.py                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│ 新闻采集层 ✅ │      │ 用户画像 🚧   │     │ World Engine │
│              │      │              │     │ (长期记忆) 🚧 │
│ NewsData     │      │ - 加载画像 ✅ │     │              │
│ Orchestrator │      │ - 更新机制 🚧 │     │ - 状态管理🚧  │
│              │      │              │     │ - 信号处理🚧  │
└──────────────┘      └──────────────┘     └──────────────┘
        │
        ├─► NewsAPI Fetcher ✅
        ├─► Reuters Fetcher 🚧
        │
        ├─► Translation Pipeline ✅
        │   (DeepSeek/GPT 异步批处理)
        │
        └─► Summarization Pipeline ✅
            (DeepSeek 智能摘要)
                    │
                    ▼
            ┌──────────────────┐
            │ 洞察生成引擎 ✅    │
            │ InsightGenerator │
            │                  │
            │ - Gemini Deep    │
            │   Thinking ✅    │
            │ - 个性化分析 ✅   │
            │ - 行动建议 ✅     │
            └──────────────────┘
                    │
                    ▼
            ┌──────────────────┐
            │   输出结果 ✅     │
            │                  │
            │ - JSON 洞察报告   │
            │ - Markdown 报告   │
            │ - 中间数据存储     │
            └──────────────────┘
```

**图例说明**：
- ✅ 已实现并测试
- 🚧 已规划或部分实现

### 核心模块

#### 1. 数据采集层 ✅
- **NewsDataOrchestrator**：协调新闻获取和处理服务
- **NewsAPIFetcher**：从 NewsAPI 获取新闻（支持分类、关键词过滤）
- **ReutersFetcher** 🚧：路透社新闻源（待实现）
- **Other** 🚧：更多的新闻源（待实现）

#### 2. 数据处理层 ✅
- **Translator**：多模型翻译支持（DeepSeek/GPT/Gemini），异步批处理
- **Summarizer**：智能摘要生成，保留关键信息

#### 3. 智能分析层 ✅
- **InsightGenerator**：基于 Gemini 深度思考，生成个性化建议
- **用户画像加载** ✅：从 JSON 文件读取用户背景、兴趣、资产配置

#### 4. 工作流编排层 ✅
- **NewsPilotPipeline**：主流程控制器，串联所有模块
- 支持中间结果保存、错误处理、日志记录

#### 5. World Engine 🚧（长期记忆系统）
- **状态管理**：多层次世界状态（L0-L3）
- **信号处理**：将新闻事件转化为状态更新信号
- **持久化**：增量历史记录

---

## 📂 项目结构

```
NewsPilot/
├── config/                      # 配置文件
│   ├── keys.py                  # API 密钥配置 ✅
│   ├── prompts.py               # LLM 提示词模板 ✅
│   └── settings.json            # 系统配置
│
├── core/                        # 核心数据模型
│   ├── news_schemas.py          # 新闻数据结构 (Pydantic) ✅
│   ├── user_schemas.py          # 用户画像结构 🚧
│   └── analysis_schemas.py      # 分析结果结构 🚧
│
├── src/
│   ├── data_acquisition/        # 新闻采集 ✅
│   │   ├── orchestrator.py      # 采集服务编排器 ✅
│   │   ├── fetchers/
│   │   │   ├── base_fetcher.py      # Fetcher 基类 ✅
│   │   │   ├── newsapi_fetcher.py   # NewsAPI 实现 ✅
│   │   │   └── reuters_fetcher.py   # Reuters 实现 🚧
│   │   └── processors/
│   │       ├── pipeline.py          # 处理流水线 ✅
│   │       └── module/
│   │           ├── translator.py    # 翻译模块 ✅
│   │           └── summarizer.py    # 摘要模块 ✅
│   │
│   ├── intelligence/            # 智能分析 ✅
│   │   └── insight_generator.py # 洞察生成器 ✅
│   │
│   ├── module/                  # 公共模块
│   │   └── init_client.py       # LLM 客户端工厂 ✅
│   │
│   ├── workflows/               # 工作流编排 ✅
│   │   └── main_pipeline.py     # 主流程控制器 ✅
│   │
│   └── world_engine/            # 长期记忆系统 🚧
│       ├── domain/              # 领域模型
│       ├── engine/              # 引擎逻辑
│       ├── pipeline/            # 处理流水线
│       ├── adapters/            # 适配器
│       └── storage/             # 存储
│
├── data/                        # 数据存储
│   ├── reports/                 # 分析报告 ✅
│   │   └── YYYY-MM-DD/
│   │       ├── raw_news.json          # 原始新闻
│   │       ├── translated_news.json   # 翻译后新闻
│   │       ├── summarized_news.json   # 摘要新闻
│   │       ├── personalized_insights.json  # 洞察报告
│   │       └── daily_report.md        # Markdown 报告
│   ├── logs/                    # 日志文件 ✅
│   ├── user_profile.json        # 用户画像 ✅
│   └── WorldState.json          # 世界状态 🚧
│
├── README.md                    # 项目文档
├── LICENSE                      # MIT 许可证
└── programe.md                  # 开发日志
```

---

## 🚀 快速开始

### 前提条件

- **Python 3.10+**
- **API 密钥**：
  - [NewsAPI](https://newsapi.org/) - 新闻数据源
  - [DeepSeek](https://www.deepseek.com/) - 翻译和摘要
  - [Google Gemini](https://ai.google.dev/) - 洞察生成

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/NewsPilot.git
   cd NewsPilot
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 API 密钥**
   
   编辑 `config/keys.py`：
   ```python
   NEWS_API_KEY = "your_newsapi_key"
   DEEPSEEK_API_KEY = "your_deepseek_key"
   GEMINI_API_KEY = "your_gemini_key"
   ```

4. **配置用户画像**
   
   编辑 `data/user_profile.json`，填入您的个人信息：
   ```json
   {
     "user_id": "0001",
     "basic_info": {
       "name": "Your Name",
       "occupation": "Your Job",
       "location": "Your City"
     },
     "interests": ["AI", "Finance", "Technology"],
     "assets": {
       "stock_holdings": ["QQQ", "AAPL"],
       "investment_focus": ["Tech", "Clean Energy"]
     }
   }
   ```

5. **运行主流程**
   ```bash
   python -m src.workflows.main_pipeline
   ```

6. **查看结果**
   
   生成的报告位于 `data/reports/YYYY-MM-DD/`：
   - `daily_report.md` - Markdown 格式的完整报告
   - `personalized_insights.json` - JSON 格式的洞察数据
   - `summarized_news.json` - 摘要后的新闻列表

---

## 🛠️ 配置说明

### 主流程配置

编辑 `src/workflows/main_pipeline.py` 的 `main()` 函数：

```python
news_config = {
    'source': 'newsapi',              # 新闻源
    'translator_flag': True,          # 是否翻译
    'summarizer_flag': True,          # 是否摘要
    'target_language': 'zh',          # 目标语言
    'translator_model': 'deepseek',   # 翻译模型
    'summarizer_model': 'deepseek',   # 摘要模型
}

pipeline = NewsPilotPipeline(
    news_config=news_config,
    insight_model="gemini",           # 洞察生成模型
    output_dir="data/reports"         # 输出目录
)

result = pipeline.run(
    save_intermediate=True,           # 保存中间结果
    max_news_for_insight=None         # 限制分析新闻数量（None=全部）
)
```

### NewsAPI 配置

编辑 `src/data_acquisition/fetchers/newsapi_fetcher.py`：

```python
params = {
    'q': 'technology OR AI OR finance',  # 搜索关键词
    'language': 'en',                     # 新闻语言
    'sortBy': 'publishedAt',              # 排序方式
    'pageSize': 100                       # 每次获取数量
}
```

### 提示词配置

编辑 `config/prompts.py` 自定义洞察生成的提示词：

```python
PERSONALIZED_INSIGHT_PROMPT = {
    "SYSTEM_PROMPT": """你是一位资深的个人决策顾问...""",
    "USER_PROMPT_TEMPLATE": """基于以下用户画像和新闻..."""
}
```

### 日志配置

系统自动记录日志到：
- 控制台输出（INFO 级别）
- `data/logs/pipeline.log`（完整日志）

已过滤第三方库的冗余日志（httpx, urllib3, google, openai 等）

---

## 📈 开发路线

### ✅ 已完成（MVP）

- [x] NewsAPI 数据源集成
- [x] 异步翻译流水线（支持多模型）
- [x] 智能摘要生成
- [x] 基于 Gemini 的个性化洞察生成
- [x] 完整的主流程编排
- [x] 中间结果保存（原始/翻译/摘要/洞察）
- [x] Markdown 报告生成
- [x] 日志系统与错误处理
- [x] 用户画像加载机制

### 🚧 进行中

- [ ] **用户画像系统完善**
  - [ ] 动态更新机制
  - [ ] 画像版本管理
  - [ ] 反馈学习循环

- [ ] **World Engine（长期记忆）**
  - [ ] 多层状态管理（L0-L3）
  - [ ] 信号处理系统
  - [ ] 增量更新机制

- [ ] **数据源扩展**
  - [ ] Reuters 新闻源
  - [ ] RSS 订阅支持
  - [ ] 自定义爬虫

### 📋 待开发

- [ ] **用户交互层**
  - [ ] Web UI（Streamlit/Gradio）
  - [ ] 反馈收集接口
  - [ ] 对话式查询

- [ ] **高级分析功能**
  - [ ] RAG 检索增强（历史新闻关联）
  - [ ] 知识图谱构建
  - [ ] 趋势预测

- [ ] **数据存储优化**
  - [ ] 向量数据库集成（用于语义搜索）
  - [ ] 关系型数据库支持
  - [ ] 缓存机制（Redis）

- [ ] **系统优化**
  - [ ] 成本优化（Token 使用统计）
  - [ ] 性能监控
  - [ ] 定时任务调度（Celery/APScheduler）
  - [ ] 容器化部署（Docker）

- [ ] **测试与文档**
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] API 文档

---

## 💡 技术栈

- **语言**：Python 3.10+
- **数据验证**：Pydantic v2
- **异步处理**：asyncio, aiohttp
- **LLM 集成**：
  - OpenAI SDK (DeepSeek 兼容)
  - Google Gemini SDK
- **数据源**：NewsAPI, Reuters (规划中)
- **存储**：JSON 文件（当前）/ PostgreSQL + pgvector（规划中）

---

## 🎯 使用场景

NewsPilot 适合以下用户：

- 📊 **投资者/交易员**：基于个人资产配置，获取市场机会与风险提示
- 💼 **职场人士**：根据职业背景，发现行业趋势与职业发展建议
- 🎓 **研究人员**：快速获取领域相关新闻的深度分析
- 🌐 **信息消费者**：每天收到个性化的新闻摘要，节省时间

---

## 🔧 常见问题

### Q: 如何更换翻译/摘要模型？

编辑主流程配置中的 `translator_model` 和 `summarizer_model`：
```python
news_config = {
    'translator_model': 'gpt',  # 可选: deepseek, gpt, gemini
    'summarizer_model': 'gpt',  # 可选: deepseek, gpt, gemini
}
```

### Q: 如何减少 API 成本？

1. 设置 `max_news_for_insight` 限制分析的新闻数量
2. 关闭翻译或摘要：`translator_flag=False` 或 `summarizer_flag=False`
3. 使用更经济的模型（DeepSeek 比 GPT-4 便宜约 95%）

### Q: 如何定时运行？

**Linux/macOS**（使用 crontab）：
```bash
# 每天早上 8 点运行
0 8 * * * cd /path/to/NewsPilot && python -m src.workflows.main_pipeline
```

**Windows**（使用任务计划程序）：

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器为每天 8:00
4. 操作选择"启动程序"，填入 Python 路径和脚本路径

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发优先级

当前急需贡献的方向：
- 🔴 **高优先级**：用户画像动态更新机制、Web UI
- 🟡 **中优先级**：Reuters 数据源、RAG 检索、单元测试
- 🟢 **低优先级**：Docker 部署、监控告警

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 🙏 致谢

- [NewsAPI](https://newsapi.org/) - 新闻数据源
- [DeepSeek](https://www.deepseek.com/) - 高性价比的 LLM 服务
- [Google Gemini](https://ai.google.dev/) - 强大的深度思考能力
- [ChatGPT (OpenAI)](https://platform.openai.com/) - 通用能力全面的大语言模型服务

---

## 📧 联系方式

- **作者**：Wang Qiushuo
- **邮箱**：185886867@qq.com
- **项目主页**：[GitHub - NewsPilot](https://github.com/yourusername/NewsPilot)

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

**开始构建您专属的智能新闻分析助手吧！** 🚀