<div align="center">

# 📰 NewsPilot 
### Intelligent News Intelligence Analysis System

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue?logo=docker)]()
[![Model](https://img.shields.io/badge/Powered%20By-LLM-green)]()

> ⚠️ **Note**: This documentation is translated from the Chinese version. In case of any discrepancy, the [Simplified Chinese version](../README.md) shall prevail.

**NewsPilot** is an automated intelligence analysis system based on Large Language Models (LLM), designed to transform massive global news into **personalized, actionable insights**. It is not just a news aggregation tool, but a 24/7 intelligent intelligence assistant that understands your profession, holdings, and interests.

[简体中文/Simplified Chinese](../README.md)

[📖 Architecture Documentation (English)](program_introduction.md) [📊 Industry Daily Report Demo](../data/daily_reports/2026-01-30)  [🎯 Personal Insight Demo](../data/personal_report/2026-01-11/daily_report.md)

> 💡 **Looks good! But don't want to deploy, need daily auto-push?**  
> If you have a need for daily customized daily reports delivered automatically (e.g., via Email, Feishu, DingTalk), please contact the author via email: `1835886867@qq.com`.


</div>

---

## ✨ Core Capabilities

| Module | Description | Key Tech |
| :--- | :--- | :--- |
| **🌍 Global Acquisition** | Integrates multi-source data from NewsAPI, RSSHub, Reuters, with automatic cleaning and deduplication. | `Playwright`, `Feedparser` |
| **🧠 Deep Understanding** | Built-in multi-model translation engine, automatically converting foreign news into concise summaries; semantic-based vector encoding. | `DeepSeek`, `Qwen-Embedding` |
| **🎯 Dual-Track Intel** | **Track A (General)**: Automatically aggregates top 10 sectors daily, generating in-depth industry reports.<br>**Track B (Personalized)**: Based on user profiles (Holdings/Profession), retrieves relevant news to generate exclusive suggestions. | `Gemini-Thinking` |

---

## 🏗️ Quick Start

### 1. Prerequisites

- **Python 3.12+**
- **Docker** (Recommended, for quick deployment of PostgreSQL and RSSHub)
- **API Keys**:
  - `Google Gemini` / `OpenAI` / `DeepSeek`: For core reasoning, translation, and summarization.
  - `NewsAPI` (or other RSS sources): For data acquisition.

### 2. Installation & Configuration

```bash
# 1. Clone repository
git clone https://github.com/yourusername/NewsPilot.git
cd NewsPilot

# 2. Install dependencies
pip install -r requirements.txt
```

**Configure API Keys**:
Edit `config/keys.py`:
```python
openai_api = "your keys"
deepseek_api = "your keys"
gemini_api = "your keys"
qwen_api = "your keys"
```

**Start Infrastructure (Docker)**:
```bash
# Windows
docker-compose -f config/docker/docker-compose_postgresql_win.yml up -d
docker-compose -f config/docker/docker-compose_rsshub_win.yml up -d

# Linux/Mac
# Use config/docker/docker-compose_postgresql_ubuntu22.04.yml etc.
```

### 3. Running Modes

| Mode | Command | Description |
| :--- | :--- | :--- |
| **Auto Service** | `python -m src.workflows.run_news_service` | **[Recommended]** Production mode. Runs in background, polls collection every 120 mins, cleans and stores data. |
| **General Report** | `python -m src.workflows.run_daily_report` | Manual/Scheduled trigger. Analyzes daily news, generates general industry daily reports. |
| **Personal Insight** | `python -m src.workflows.main_pipeline` | Reads `user_profile.json`, generates personalized investment and action suggestions. |

---

## 🧩 System Logic

### Step 1: Infrastructure
> Runs silently in the background, building an exclusive knowledge base

1. **Collection**: `DaemonOrchestrator` schedules Fetchers (NewsAPI, RSS, etc.) periodically.
2. **Processing**: `ProcessorPipeline` pipeline processing:
    - 🧹 **Cleaning**: Removes ads, standardizes format.
    - 🔄 **Translation**: Calls DeepSeek/GPT to translate foreign texts.
    - 📝 **Summarization**: Extracts core facts, removes redundancy.
    - 🔢 **Vectorization**: Uses Qwen-Embedding to convert news into vectors.

### Step 2: Intelligence
> When you need intelligence, the brain starts working

- **General Path**: `NewsAnalyzer` extracts recent 24h news -> Clusters by sector -> Expert Model (LLM) performs "Fact-Reaction-Judgment" analysis -> Outputs Markdown Daily Report.
- **Personal Path**: `InsightGenerator` reads your profile -> Retrieves strong relevant news -> Generates "Opportunity/Risk" assessment -> Outputs Markdown Personal Brief.

---

## 🙏 Acknowledgments

This project is made possible by the support of the following excellent foundation models and open-source services:

*   **Core Intelligence**: [Google Gemini](https://ai.google.dev/) (Thinking Model), [OpenAI GPT-4o](https://openai.com/)
*   **Cost-Effective LLM**: [DeepSeek](https://www.deepseek.com/) (V3/R1) - Used for large-scale translation and summarization tasks.
*   **Semantic Embedding**: [Qwen (Tongyi Qianwen)](https://tongyi.aliyun.com/) - Provides excellent Chinese semantic vector support.
*   **Data Sources**: [NewsAPI](https://newsapi.org/), [Reuters](https://www.reuters.com/).

---

## ⚠️ License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute the source code of this project, including for commercial purposes. You only need to include the original author's copyright notice and license notice in the software copy.

**Disclaimer**: The investment suggestions and analysis generated by this system are for reference only and do not constitute actual investment basis.

---

## 🤝 Contribute

NewsPilot is still iterating fast, your participation is very welcome!

*   **Star 🌟**: If you like this project, please click Star in the upper right corner to support it!
*   **Fork & PR**: Welcome to submit code to fix bugs or add new features (such as connecting more news sources, Web UI optimization, etc.).
*   **Issue**: Encounter problems or have new ideas? Please submit an Issue for discussion.

---

## 📬 Contact

*   **Author**: Wang Qiushuo
*   **Email**: 185886867@qq.com

*   **GitHub**: [NewsPilot Repository](https://github.com/Thislu13/NewsPilot)

---

<div align="center">
  <sub>Generated by NewsPilot Team · 2026</sub>
</div>
