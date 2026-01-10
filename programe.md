<!--
 * @Author: WangQiushuo 185886867@qq.com
 * @Date: 2025-12-18 20:09:29
 * @LastEditors: WangQiushuo 185886867@qq.com
 * @LastEditTime: 2025-12-18 22:50:47
 * @FilePath: \NewsPilot\programe.md
 * @Description: 
 * 
 * Copyright (c) 2025 by WangQiushuo, All Rights Reserved. 
-->



your_news_analysis_system/
├── .env.example                    # 环境变量示例文件
├── .gitignore
├── README.md                       # 项目总览
├── requirements.txt                # 项目依赖
├── pyproject.toml                  # 现代项目配置（可选，但推荐）
├── docker-compose.yml              # 服务编排（数据库、缓存等）
├── Dockerfile                      # 应用容器化
│
├── config/                         # 配置文件
│   ├── __init__.py
│   ├── settings.py                 # 主设置，从环境变量读取
│   ├── logging_config.py           # 日志配置
│   └── prompts/                    # 所有提示词模板
│       ├── __init__.py
│       ├── news_summary.yaml
│       ├── user_analysis.yaml
│       └── ...
│
├── src/                            # 主要源代码
│   ├── __init__.py
│   │
│   ├── core/                       # 核心领域模型与抽象
│   │   ├── __init__.py
│   │   ├── schemas.py              # Pydantic数据模型（定义新闻、用户画像等结构）
│   │   └── events.py               # 领域事件定义（为未来事件驱动预留）
│   │
│   ├── data_acquisition/           # 对应“新闻抓取模块”
│   │   ├── __init__.py
│   │   ├── fetchers/               # 各渠道抓取器实现
│   │   │   ├── __init__.py
│   │   │   ├── base_fetcher.py     # 抽象基类
│   │   │   ├── reuters_fetcher.py
│   │   │   └── ...
│   │   ├── normalizer.py           # 规范化处理，输出统一格式
│   │   ├── deduplicator.py         # 去重与冲突裁决逻辑
│   │   └── document_manager.py     # 官方文档处理逻辑
│   │
│   ├── data_processing/            # 对应“新闻整理模块”（已拆分）
│   │   ├── __init__.py
│   │   ├── fact_extractor.py       # 事实摘要提取器
│   │   ├── insight_generator.py    # 关联与洞察生成器
│   │   └── graph_updater.py        # 关联图谱更新器（异步后台任务）
│   │
│   ├── user_profile/               # 对应“用户画像模块”和“反馈模块”
│   │   ├── __init__.py
│   │   ├── manager.py              # 用户画像的CRUD和提示词组装
│   │   ├── memory_backend.py       # 记忆存储后端抽象（可接Mem0或向量库）
│   │   ├── feedback_handler.py     # 处理用户反馈，触发画像更新
│   │   └── models.py               # 用户画像数据模型
│   │
│   ├── intelligence/               # 智能核心层（对应“建议”和“提问”模块）
│   │   ├── __init__.py
│   │   ├── query_service.py        # 【关键】统一查询服务
│   │   ├── suggestion_agent.py     # 建议生成智能体
│   │   ├── questioning_agent.py    # 针对性提问智能体
│   │   └── llm_client.py           # 统一的大模型客户端封装
│   │
│   ├── storage/                    # 数据存储层
│   │   ├── __init__.py
│   │   ├── database.py             # 数据库连接与会话管理
│   │   ├── repositories/           # 各实体的数据访问对象
│   │   │   ├── __init__.py
│   │   │   ├── news_repository.py
│   │   │   └── user_repository.py
│   │   └── vector_store.py         # 向量数据库客户端封装
│   │
│   ├── tasks/                      # 异步任务与调度（Celery）
│   │   ├── __init__.py
│   │   ├── celery_app.py           # Celery应用实例
│   │   └── periodic_tasks.py       # 定时任务（如每日新闻抓取）
│   │
│   ├── api/                        # 对外接口层（如未来提供API）
│   │   ├── __init__.py
│   │   ├── v1/                     # API版本
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/          # 各个端点
│   │   │   └── dependencies.py     # FastAPI依赖项
│   │   └── app.py                  # FastAPI应用实例
│   │
│   └── utils/                      # 通用工具函数
│       ├── __init__.py
│       ├── logger.py               # 日志记录器
│       ├── cache.py                # 缓存工具（Redis）
│       └── metrics.py              # 监控指标（为未来预留）
│
├── tests/                          # 测试目录（与src结构镜像）
│   ├── __init__.py
│   ├── conftest.py
│   └── ...
│
├── scripts/                        # 部署、数据迁移等脚本
│   ├── __init__.py
│   ├── init_database.py
│   └── ...
│
└── logs/                           # 日志目录（应在.gitignore中忽略）

src/core/：这是系统的心脏，存放所有领域模型（如 NewsArticle, UserProfile）。修改这里的数据结构（schemas.py）会影响整个系统。未来无论UI或API如何变，核心业务逻辑都基于此。

按模块分包 (data_acquisition/, intelligence/等)：每个之前讨论的功能模块对应一个清晰的包。这符合“高内聚、低耦合”原则。例如，要更换新闻源，只需修改 fetchers/ 目录下的文件。

intelligence/query_service.py：这是之前讨论的统一查询服务的实现位置，也是未来缓存优化的核心。所有智能体都通过它获取数据，这里是性能和扩展性的关键控制点。

config/prompts/：将提示词外部化为YAML/JSON文件。这意味着优化提示词无需改动代码，甚至可以开发一个后台界面动态管理提示词。

storage/ 与 tasks/：将数据访问和异步任务抽象成独立层。未来更换数据库（如从PostgreSQL到MySQL）或任务队列（从Celery到Kafka）时，影响范围会被隔离在这两个目录内。

api/ 目录预留：虽然初期可能用脚本或Streamlit触发，但预留API层能为未来提供Web界面、移动端或第三方集成打下基础。