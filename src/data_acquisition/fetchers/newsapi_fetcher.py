#
# Author: WangQiushuo 185886867@qq.com
# Date: 2025-12-23 21:59:45
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-23 23:11:45
# FilePath: \NewsPilot\src\data_acquisition\fetchers\newsapi_fetcher.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

from typing import List, Dict, Any, Optional

import asyncio
from datetime import datetime, timezone
import uuid
from newsapi import NewsApiClient

from src.data_acquisition.fetchers.base_fetcher import BaseFetcher
from core.news_schemas import NewsItemRawSchema, Attachment

from src.data_acquisition.module.get_article_from_url import fetch_full_article_by_url

class NewsAPIFetcher(BaseFetcher):
    """
    NewsAPI 抓取器实现
    """
    
    DEFAULT_CATEGORIES = ["business", "science", "technology"]
    DEFAULT_SOURCES = [
        "reuters",
        "bloomberg",
        "the-wall-street-journal",
        "associated-press",
        "axios",
        "fortune",
        "xinhua-net",
    ]
    @property
    def SOURCE_NAME(self) -> str:
        return "NewsAPI"

    @property
    def SOURCE_TYPE(self) -> str:
        return "API"
    
    def __init__(
        self,
        api_key: str,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        language: str = "en",
    ):
        self.client = NewsApiClient(api_key=api_key)
        self.categories = categories or self.DEFAULT_CATEGORIES
        self.sources = sources or self.DEFAULT_SOURCES
        self.language = language

    async def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """
        从 NewsAPI 获取原始新闻数据
        """
        articles: List[Dict[str, Any]] = []

        # 按类别获取头条新闻
        for category in self.categories:
            resp = self.client.get_top_headlines(
                category=category,
                language=self.language,
            )
            if resp.get("status") == "ok":
                articles.extend(resp.get("articles", []))
        # 按照来源拉取新闻
        resp = self.client.get_top_headlines(
            sources=",".join(self.sources),
            language=self.language,
        )
        if resp.get("status") == "ok":
            articles.extend(resp.get("articles", []))

        return articles
    
    def normalize_data(
        self, raw_data: Dict[str, Any]
    ) -> Optional[NewsItemRawSchema]:
        """
        将 NewsAPI 的原始数据转换为 NewsItemRawSchema
        """
        # --- 基础校验 ---
        if not raw_data.get("url") or not raw_data.get("title"):
            return None
        
        # --- Source 信息 ---
        source_info = raw_data.get("source", {})
        source_channel = source_info.get("name", "Unknown")
        
        # --- 时间解析 ---
        published_at_str = raw_data.get("publishedAt")
        try:
            published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        except Exception:
            return None
        
        # --- 作者解析 ---
        authors = []
        author_raw = raw_data.get("author")
        if author_raw:
            authors = [a.strip() for a in author_raw.split(",") if a.strip()]
        
        # --- 附件处理 ---
        attachments = []
        image_url = raw_data.get("urlToImage")
        if image_url:
            attachments.append(
                Attachment(
                    type="image",
                    url=image_url,
                    description=None,
                )
            )

        # --- 构建 NewsItemRawSchema ---
        return NewsItemRawSchema(
            # 核心标识符
            unique_id=str(uuid.uuid4()),
            source_id='',

            # 溯源信息
            source_channel=source_channel,
            source_url=raw_data.get("url"),

            # 时间信息
            published_at=published_at,
            fetched_at=datetime.now(timezone.utc),

            # 内容主体
            title=raw_data.get("title"),
            abstract=raw_data.get("description"),
            body=raw_data.get("content") or '',

            # 元数据
            authors=authors,
            categories=[],

            # 附件与关联文件
            attachments=attachments,
            supportingDocument_id=[],

            # 去重&评估
            simhash=None,
            evaluation_score=None,

            # 扩展字段
            extra_data={
                "newsapi_raw": raw_data
            },
        )
    
    async def fetch_and_normalize(self) -> List[NewsItemRawSchema]:
        """
        完整的工作流：抓取原始数据并进行规范化。
        """
        raw_list = await self.fetch_raw_data()
        enriched_raw_list = await asyncio.gather(
            *[self.enrich_full_content(raw) for raw in raw_list]
        )


        normalized_list: List[NewsItemRawSchema] = []
        for raw_item in enriched_raw_list:
            normalized = self.normalize_data(raw_item)
            if normalized:
                normalized_list.append(normalized)

        return normalized_list  
    

    async def enrich_full_content(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 NewsAPI 以外的服务丰富新闻的完整内容。
        
        当前实现为占位符，直接返回原始数据。
        """
        if not raw_item.get("url"):
            return raw_item

        full_content_result = await fetch_full_article_by_url(raw_item["url"])
        if full_content_result.get("success"):
            raw_item["content"] = full_content_result.get("body") or raw_item.get("content")
            raw_item["title"] = full_content_result.get("title") or raw_item.get("title")
            raw_item["authors"] = full_content_result.get("authors") or raw_item.get("authors")
            raw_item["publishedAt"] = full_content_result.get("published_at") or raw_item.get("publishedAt")
        else:
            print(f"无法丰富内容，URL: {raw_item['url']}，错误: {full_content_result.get('error')}")
        return raw_item

