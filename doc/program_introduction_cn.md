<!--
 * @Author: WangQiushuo 185886867@qq.com
 * @Date: 2026-02-08
 * @FilePath: \code\NewsPilot\program_introduction_cn.md
 * @Description: NewsPilot 系统架构文档
 * 
 * Copyright (c) 2026, All Rights Reserved. 
-->

# NewsPilot 系统架构 (V0.1)

## 1. 项目概述 (Project Overview)
NewsPilot 是一套模块化的智能新闻分析系统，旨在通过自动化流水线完成全球新闻的采集、处理及语义理解。V0.1 版本支持两种核心运行模式：面向行业动态的**通用日报生成**，以及由 LLM（大语言模型）驱动的符合用户偏好的**个性化洞察**。

---

## 2. 目录结构 (Directory Structure)

```text
NewsPilot/
├── program_introduction.md         # 架构设计文档 (英文原版)
├── program_introduction_cn.md      # 架构设计文档 (中文版)
├── README.md                       # 项目说明
├── requirements.txt                # Python 依赖清单
├── config/                         # [配置中心]
│   ├── keys.py                     # API 密钥与凭证
│   ├── prompts.py                  # LLM 提示词库
│   ├── settings.json               # 系统通用配置
│   ├── user_profile.json           # 默认用户画像配置
│   └── docker/                     # Docker 编排文件
│       
├── core/                           # [领域核心]
│   ├── news_schemas.py             # 数据模型 (Pydantic Schemas)
│   └── user_schemas.py             # 用户画像与偏好模型
│
├── data/                           # [数据存储]
│   ├── daily_reports/              # 生成的 Markdown 日报
│   └── personal_report/            # 个性化用户洞察
│
├── src/                            # [源代码]
    │
    ├── data_acquisition/           # [数据层] (ELT 流水线)
    │   ├── daemon_orchestrator.py  # [异步] 长期驻留服务管理器
    │   ├── orchestrator.py         # [同步] 按需采集编排器
    │   ├── fetchers/               # 数据源适配器 (NewsAPI, RSSHub, Reuters 等)
    │   ├── processors/             # 处理流水线 (清洗 -> 翻译 -> 摘要 -> 向量化)
    │   └── module/                 # 底层爬虫工具 (下载, 解析)
    │
    ├── intelligence/               # [AI 层]
    │   ├── new_analyzer.py         # 通用日报引擎 (专家视角)
    │   └── insight_generator.py    # 个性化洞察引擎 
    │
    ├── storage/                    # [持久化层]
    │   ├── models.py               # SQL Alchemy ORM 模型
    │   ├── repository.py           # 数据库仓储模式
    │   └── db_config.py            # 数据库连接设置
    │
    ├── workflows/                  # [入口点]
    │   ├── run_news_service.py     # 服务：启动后台守护进程编排器
    │   ├── run_daily_report.py     # 任务：生成通用日报
    │   └── main_pipeline.py        # 任务：运行全流程个性化分析
    │
    └── module/                     # [基础设施]
        ├── init_client.py          # LLM 客户端工厂 (兼容 OpenAI/Gemini)
        └── tools.py                # 系统级通用工具

```

---

## 3. 核心架构 (Core Architecture)

本系统采用**分层架构**，将**数据生产**与**智能消费**解耦。

### 3.1 基础设施轨：数据采集服务 (Infrastructure Track)
负责构建高质量、持续更新的全球新闻知识库。

*   **入口点**: `src/workflows/run_news_service.py`
*   **运行模式**: 守护进程服务 (长期驻留)
*   **组件**: `DaemonOrchestrator` (`src/data_acquisition/daemon_orchestrator.py`)
*   **工作流程**:
    1.  **采集任务 (Acquisition Job)**: 周期性使用 `fetchers/` 中的适配器获取原始数据，并存入暂存区。
    2.  **处理工作者 (Processing Worker)**: 持续轮询暂存区。
    3.  **流水线执行**: 对原始新闻执行清洗、翻译 (LLM)、摘要 (LLM) 和向量化嵌入 (Vector Embedding)。
    4.  **存储**: 将精炼后的数据持久化至 PostgreSQL (支持 pgvector)。

### 3.2 应用轨：智能生成 (Application Track)
消费已精炼的数据以产出人类可读的情报。

#### A. 通用情报 (日报)
*   **入口点**: `src/workflows/run_daily_report.py`
*   **引擎**: `NewsAnalyzer` (`src/intelligence/new_analyzer.py`)
*   **场景**: 定时任务 (例如：每日 8:00 AM)。
*   **逻辑**: 聚合过去 24 小时的新闻，按板块分类，并使用“专家展望 (Expert Outlook)”模型生成结构化的 Markdown 研报。

#### B. 个性化情报 (用户洞察)
*   **入口点**: `src/workflows/main_pipeline.py`
*   **引擎**: `InsightGenerator` (`src/intelligence/insight_generator.py`)
*   **场景**: 按需触发或用户触发。
*   **逻辑**:
    *   从 `core/user_schemas.py` 加载用户画像（持仓、兴趣、风险偏好）。
    *   为特定用户生成独家洞察和相关性评分。


---

## 4. 关键技术组件 (Key Technical Components)

### 4.1 数据层 (`src/data_acquisition`)
*   **Fetchers (采集器)**: 用于不同新闻源的模块化适配器 (`newsapi_fetcher.py`, `rsshub_fetcher.py`, `reuters_fetcher.py`)。
*   **Processors (处理器)**: 一个流水线架构 (`processors/pipeline.py`)，负责编排如 `translator.py` (翻译), `summarizer.py` (摘要), 和 `embedding.py` (向量化) 等独立步骤。

### 4.2 存储层 (`src/storage`)
*   **Repository Pattern (仓储模式)**: `StorageRepository` 抽象了所有数据库交互，使业务逻辑无需关心 SQL 细节。
*   **Schema (模式)**: `core/news_schemas.py` 定义了在系统中流动的数据契约 (`NewsItemRaw`, `NewsItemRefined`)。

### 4.3 智能层 (`src/intelligence`)
*   **上下文窗口管理**: 分析器被设计为可以处理大上下文窗口，以便在单次或分批 LLM 调用中处理全天的新闻。

---

## 5. 发布状态 (V0.1 MVP)
*   **功能能力**:
    *   从采集到分析的全栈自动化。
    *   双模式运行（后台服务 + 按需报告）。

*   **基础设施**:
    *   PostgreSQL
    *   Docker 容器化支持。
