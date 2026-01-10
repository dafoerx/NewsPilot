#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-07 22:40:42
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-10 17:52:12
# FilePath: \NewsPilot\src\data_acquisition\orchestrator.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 
import asyncio
import json

from typing import List, Optional

from src.data_acquisition.fetchers.newsapi_fetcher import NewsAPIFetcher
from src.data_acquisition.processors.pipeline import NewsProcessingPipeline
from core.news_schemas import NewsItemRawSchema, NewsItemRefinedSchema
from config import keys
# from config.settings import settings


class NewsAcquisitionService:
    """
    统一管理新闻抓取流程
    """

    def __init__(
        self,
        sources: Optional[List[str]] = None,
    ):
        """
        :param sources: 指定启用的新闻源，如 ["newsapi", "reuters"]
                        None 表示启用全部
        """
        self.sources = set(sources) if sources else None

        self.fetchers = {
            "newsapi": NewsAPIFetcher(api_key=keys.newsapi_api),
            # "reuters": ReutersFetcher(...),
        }

    async def run(self) -> List[NewsItemRawSchema]:
        all_news: List[NewsItemRawSchema] = []

        for name, fetcher in self.fetchers.items():
            if self.sources and name not in self.sources:
                continue

            items = await fetcher.fetch_and_normalize()
            all_news.extend(items)

        return all_news
    

class NewsProcessingService:
    """
    统一管理新闻处理流程
    """

    def __init__(
            self, 
            translator_flag: bool = True, translator_model: str = "deepseek", target_language: str = "zh",
            summarizer_flag: bool = True, summarizer_model: str = "deepseek",
        ):
        self.translator_flag = translator_flag
        self.summarizer_flag = summarizer_flag
        self.target_language = target_language
        self.translator_model = translator_model
        self.summarizer_model = summarizer_model
        self.pipeline = NewsProcessingPipeline(
            translotor_flag=self.translator_flag,
            summarizer_flag=self.summarizer_flag,
            translator_model=self.translator_model,
            target_language=self.target_language,
            summarizer_model=self.summarizer_model,
        )

    async def run(self, news_list: List[NewsItemRawSchema]) -> List[NewsItemRefinedSchema]:
        
        processed_news = await self.pipeline.process_async(news_list)
        return processed_news



class NewsDataOrchestrator():
    def __init__(self, news_config: dict = {}):
        self.news_config = news_config
        self.m_init()

    def m_init(self):
        
        self.source = self.news_config.get('source', 'newsapi')

        self.translator_flag = self.news_config.get('translator_flag', True)
        self.summarizer_flag = self.news_config.get('summarizer_flag', True)
        self.target_language = self.news_config.get('target_language', 'zh')
        self.translator_model = self.news_config.get('translator_model', 'deepseek')
        self.summarizer_model = self.news_config.get('summarizer_model', 'deepseek')


        self.news_acquisition_service = NewsAcquisitionService(sources=[self.source])
        self.news_processing_service = NewsProcessingService(
            translator_flag=self.translator_flag, translator_model=self.translator_model, target_language=self.target_language,
            summarizer_flag=self.summarizer_flag, summarizer_model=self.summarizer_model,
        )

    async def run_async(self) -> List[NewsItemRefinedSchema]:
        news_items_raw = await self.news_acquisition_service.run()
        news_items = await self.news_processing_service.run(news_items_raw)
        
        return news_items

    def run(self) -> List[NewsItemRefinedSchema]:
        return asyncio.run(self.run_async())



if __name__ == "__main__":
    news_config = {
        'source': 'newsapi',

        'translator_flag': True,
        'summarizer_flag': True,
        'target_language': 'zh',
        'translator_model': 'deepseek',
        'summarizer_model': 'deepseek',
    }


    news_data_orchestrator = NewsDataOrchestrator(news_config=news_config)
    news_items = news_data_orchestrator.run()
    print(f"Fetched total {len(news_items)} news items.")
    print(news_items[0])
    from pathlib import Path
    save_path = Path(r"E:\code\NewsPilot\data\temp\news\refined_news_items.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(
            [item.dict() for item in news_items],
            f,
            ensure_ascii=False,
            indent=4,
            default=str  # 自动把 datetime 转成字符串
        )