#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-31 17:29:22
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-31 17:40:17
# FilePath: \NewsPilot\src\workflows\acquisition_workflow.py
# Description:
# 
# Copyright (c) 2026 by , All Rights Reserved. 


import asyncio
import logging
import time
from datetime import datetime

# 引入数据库管理器和模型
from src.storage import db_manager, RawNews

# 模拟引用你的 orchestrator
# from src.data_acquisition.orchestrator import NewsAcquisitionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AcquisitionWorkflow")

class AcquisitionWorkflow:
    def __init__(self):
        # 1. 在初始化阶段或运行前，强制检查数据库状态
        self._ensure_infrastructure()
        
        # self.fetcher = NewsAcquisitionService()

    def _ensure_infrastructure(self):
        """
        核心需求实现：
        每次运行数据抓取部分的时候先检查是否存在期望中的一些表，如果没有再重建
        """
        logger.info("Verifying database infrastructure...")
        db_manager.verify_and_create_tables()

    async def run_once(self):
        """
        单次运行逻辑实例
        """
        logger.info("Starting acquisition job...")
        
        session = db_manager.get_session()
        try:
            # --- 模拟：获取数据 ---
            # raw_items = await self.fetcher.run()
            # 这里的字段要模拟 NewsItemRawSchema 转换后的数据
            mock_news = {
                "source_url": f"https://example.com/news/{int(time.time())}",
                "title": f"Example News at {datetime.now()}",
                "body": "Some content from the news body...",
                "source_channel": "mock_source",
                "published_at": datetime.now(),
                "extra_data": {"original_response": "foo"},
                "authors": ["Alice", "Bob"]
            }
            logger.info(f"Fetched news: {mock_news['title']}")

            # --- 模拟：检查去重与保存 ---
            # 这里对应 NewsItemRawSchema.source_url -> RawNews.source_url
            exists = session.query(RawNews).filter_by(source_url=mock_news['source_url']).first()
            if not exists:
                new_article = RawNews(
                    source_url=mock_news['source_url'],
                    title=mock_news['title'],
                    body=mock_news['body'],
                    source_channel=mock_news['source_channel'],
                    published_at=mock_news['published_at'],
                    authors=mock_news['authors'],
                    extra_data=mock_news['extra_data']
                )
                session.add(new_article)
                session.commit()
                logger.info(f"Saved new article to DB: {new_article.unique_id}")
                
            else:
                logger.info("News already exists, skipping.")

        except Exception as e:
            session.rollback()
            logger.error(f"Job failed: {e}", exc_info=True)
        finally:
            session.close()

    async def start_loop(self, interval=60):
        while True:
            await self.run_once()
            logger.info(f"Sleeping for {interval}s...")
            await asyncio.sleep(interval)

if __name__ == "__main__":
    workflow = AcquisitionWorkflow()
    # 运行一次演示
    asyncio.run(workflow.run_once())
