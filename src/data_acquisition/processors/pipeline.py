#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-09 21:38:09
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-11 22:53:24
# FilePath: \NewsPilot\src\data_acquisition\processors\pipeline.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

# src/processors/pipeline.py
import asyncio
from typing import List

from core.news_schemas import NewsItemRawSchema, NewsItemRefinedSchema
from src.data_acquisition.processors.module.summarizer import Summarizer
from src.data_acquisition.processors.module.translator import Translator


class NewsProcessingPipeline:
    """
    新闻处理流水线：
    - 摘要生成
    - 翻译
    - 可扩展：后续可以加入去重、embedding、分类等步骤
    """

    def __init__(
        self,
        translotor_flag: bool = True,
        summarizer_flag: bool = True,
        translator_model: str = "deepseek",
        target_language: str = "zh",
        summarizer_model: str = "deepseek",
    ):
        self.translator = Translator(model_name=translator_model)
        self.summarizer = Summarizer(model_name=summarizer_model)
        self.target_language = target_language
        self.translotor_flag = translotor_flag
        self.summarizer_flag = summarizer_flag

    async def process_async(
        self, news_list: List[NewsItemRawSchema]
    ) -> dict:
        """
        异步批量处理新闻：
        1. 生成摘要
        2. 翻译标题、摘要、正文
        """
        translated_items, summarized_items = None, None
        try:
            if self.translotor_flag == True:
                # 异步翻译
                translated_items = await self.translator.translate_batch(
                    news_list,
                    target_language=self.target_language
                )
            if self.summarizer_flag == True:
                # 异步生成摘要
                summarized_items = await self.summarizer.summarize_batch(translated_items)
        
            pipeline_result = {
                "translated_items": translated_items,
                "summarized_items": summarized_items
            }
            return pipeline_result
        finally:
            await self.translator.close()
            await self.summarizer.close()

    def run(self, news_list: List[NewsItemRawSchema]) -> dict:
        """
        同步接口（外部调用），内部使用 asyncio.run
        """
        return asyncio.run(self.process_async(news_list))
    
if __name__ == "__main__":
    from pathlib import Path
    import json
    from dateutil.parser import parse

    news_path = r'E:\code\NewsPilot\data\temp\news\news_items.json'
    save_path = r'E:\code\NewsPilot\data\temp\news\refined_news_items.json'
    
    with open(Path(news_path), "r", encoding="utf-8") as f:
        news_data = json.load(f)
    from core.news_schemas import NewsItemRawSchema
    def normalize_news_item(item: dict) -> dict:
        # 将 published_at 转为 datetime
        if "published_at" in item and isinstance(item["published_at"], str):
            item["published_at"] = parse(item["published_at"])
        if "fetched_at" in item and isinstance(item["fetched_at"], str):
            item["fetched_at"] = parse(item["fetched_at"])
        return item

    news_items = [NewsItemRawSchema(**normalize_news_item(item)) for item in news_data]
    pipeline = NewsProcessingPipeline()
    result = pipeline.run(news_items[:10])  # 仅处理前10条以加快测试速度
    refined_items = result["summarized_items"]
    print(f"Processed total {len(refined_items)} news items.")
    print(refined_items[0])
    with open(Path(save_path), "w", encoding="utf-8") as f:
        json.dump(
            [item.model_dump() for item in refined_items],
            f,
            ensure_ascii=False,
            indent=4,
            default=str  # 自动把 datetime 转成字符串
        )

