#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-07 22:40:42
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-08 00:07:30
# FilePath: \NewsPilot\src\data_acquisition\orchestrator.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 
import asyncio
import json

from typing import List

from src.data_acquisition.fetchers.newsapi_fetcher import NewsAPIFetcher
from core.news_schemas import NewsItemRawSchema
from config import keys
# from config.settings import settings


class NewsAcquisitionService:
    """
    统一管理新闻抓取流程
    """

    def __init__(self):
        # self.fetchers = [
        #     NewsAPIFetcher(api_key=settings.NEWSAPI_KEY),
        #     # ReutersFetcher(...)
        # ]
        self.fetchers = [
            NewsAPIFetcher(api_key=keys.newsapi_api),
            # ReutersFetcher(...)
        ]

    async def run(self) -> List[NewsItemRawSchema]:
        all_news: List[NewsItemRawSchema] = []

        for fetcher in self.fetchers:
            items = await fetcher.fetch_and_normalize()
            all_news.extend(items)

        return all_news

if __name__ == "__main__":
    orchestrator = NewsAcquisitionService()
    news_items = asyncio.run(orchestrator.run())
    print(f"Fetched total {len(news_items)} news items.")
    print(news_items[0])
    from pathlib import Path
    save_path = Path(r"data/temp/news/news_items.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(
            [item.dict() for item in news_items],
            f,
            ensure_ascii=False,
            indent=4,
            default=str  # 自动把 datetime 转成字符串
        )