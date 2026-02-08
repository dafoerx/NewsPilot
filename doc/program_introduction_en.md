<!--
 * @Author: WangQiushuo 185886867@qq.com
 * @Date: 2026-02-08
 * @FilePath: \code\NewsPilot\program_introduction.md
 * @Description: NewsPilot System Architecture Documentation
 * 
 * Copyright (c) 2026, All Rights Reserved. 
-->

# NewsPilot System Architecture (V0.1)

## 1. Project Overview
NewsPilot is a modular intelligence analysis system designed to automate the acquisition, processing, and semantic understanding of global news. It supports two main operational modes: **General Daily Reports** for industry-wide updates and **Personalized Insights** for user-specific intelligence, driven by LLMs (Large Language Models).

---

## 2. Directory Structure

```text
NewsPilot/
├── program_introduction.md         # Architecture design document
├── README.md                       # Project overview
├── requirements.txt                # Python dependencies
├── config/                         # [Configuration Center]
│   ├── keys.py                     # API keys and credentials
│   ├── prompts.py                  # LLM Prompt Registry
│   ├── settings.json               # General system settings
│   ├── user_profile.json           # Default user profile settings
│   └── docker/                     # Docker composition files
│       
├── core/                           # [Domain Core]
│   ├── news_schemas.py             # Data models (Pydantic Schemas for News)
│   └── user_schemas.py             # User profile & preference models
│
├── data/                           # [Data Storage]
│   ├── daily_reports/              # Generated markdown daily reports
│   └── personal_report/            # Personalized user insights
│
├── src/                            # [Source Code]
    │
    ├── data_acquisition/           # [Data Layer] (ELT Pipeline)
    │   ├── daemon_orchestrator.py  # [Async] Long-running service manager
    │   ├── orchestrator.py         # [Sync] On-demand acquisition orchestrator
    │   ├── fetchers/               # Source adapters (NewsAPI, RSSHub, Reuters, etc.)
    │   ├── processors/             # Processing pipeline (Clean -> Translate -> Summarize -> Embed)
    │   └── module/                 # Low-level crawler tools (Download, Parsing)
    │
    ├── intelligence/               # [AI Layer]
    │   ├── new_analyzer.py         # General daily report engine (Expert Outlook)
    │   └── insight_generator.py    # Personalized insight engine 
    │
    ├── storage/                    # [Persistence Layer]
    │   ├── models.py               # SQL Alchemy ORM Models
    │   ├── repository.py           # Database Repository Pattern
    │   └── db_config.py            # Database connection setup
    │
    ├── workflows/                  # [Entry Points]
    │   ├── run_news_service.py     # Service: Starts the Daemon Orchestrator
    │   ├── run_daily_report.py     # Task: Generates general daily reports
    │   └── main_pipeline.py        # Task: Runs full personalized analysis pipeline
    │
    └── module/                     # [Infrastructure]
        ├── init_client.py          # LLM Client Factory (OpenAI/Gemini compatible)
        └── tools.py                # System-wide utilities

```

---

## 3. Core Architecture

The system follows a **Layered Architecture**, decoupling **Data Production** from **Intelligence Consumption**.

### 3.1 Infrastructure Track: Data Acquisition Service
Responsible for building a high-quality, continuous knowledge base of global news.

*   **Entry Point**: `src/workflows/run_news_service.py`
*   **Operational Mode**: Daemon Service (Long-running)
*   **Component**: `DaemonOrchestrator` (`src/data_acquisition/daemon_orchestrator.py`)
*   **Workflow**:
    1.  **Acquisition Job**: Periodically fetches raw data using adapters in `fetchers/`. Stores data in a staging area.
    2.  **Processing Worker**: Continuously polls the staging area.
    3.  **Pipeline Execution**: Applies normalization, translation (LLM), summarization (LLM), and vector embedding to raw news.
    4.  **Storage**: Persists refined data into PostgreSQL (with pgvector).

### 3.2 Application Track: Intelligence Generation
Consumes refined data to produce human-readable intelligence.

#### A. General Intelligence (Daily Reports)
*   **Entry Point**: `src/workflows/run_daily_report.py`
*   **Engine**: `NewsAnalyzer` (`src/intelligence/new_analyzer.py`)
*   **Scenario**: Scheduled task (e.g., Daily at 8:00 AM).
*   **Logic**: Aggregates news from the last 24 hours, categorizes them by sector, and uses an "Expert Outlook" model to generate a structured markdown report.

#### B. Personalized Intelligence (User Insights)
*   **Entry Point**: `src/workflows/main_pipeline.py`
*   **Engine**: `InsightGenerator` (`src/intelligence/insight_generator.py`)
*   **Scenario**: On-demand or user-triggered.
*   **Logic**:
    *   Loads user profile (holdings, interests, risk tolerance) from `core/user_schemas.py`.
    *   Generates exclusive insights and relevance scores for the specific user.


---

## 4. Key Technical Components

### 4.1 Data Layer (`src/data_acquisition`)
*   **Fetchers**: Modular adapters for different news sources (`newsapi_fetcher.py`, `rsshub_fetcher.py`, `reuters_fetcher.py`).
*   **Processors**: A pipeline architecture (`processors/pipeline.py`) that orchestrates individual steps like `translator.py`, `summarizer.py`, and `embedding.py`.

### 4.2 Storage Layer (`src/storage`)
*   **Repository Pattern**: `StorageRepository` abstracts all database interactions, allowing business logic to remain agnostic of SQL details.
*   **Schema**: `core/news_schemas.py` defines the contract for data flowing through the system (`NewsItemRaw`, `NewsItemRefined`).

### 4.3 Intelligence Layer (`src/intelligence`)
*   **Context Window Management**: Analyzers are designed to handle large context windows to process an entire day's worth of news in single or batched LLM calls.

---

## 5. Release Status (V0.1 MVP)
*   **Capabilities**:
    *   Full-stack automation from acquisition to analysis.
    *   Dual-mode operation (Background Service + On-demand Reporting)
  
*   **Infrastructure**:
    *   PostgreSQL
    *   Docker containerization support.
