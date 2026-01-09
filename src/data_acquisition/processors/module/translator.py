#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-09 23:37:21
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-10 00:55:10
# FilePath: \NewsPilot\src\data_acquisition\processors\module\translator.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

from core.news_schemas import NewsItemRawSchema, NewsItemRefinedSchema
from src.module.init_client import LLMClientFactory
from config.prompts import TRANSLATION_PROMPT_CN

import asyncio
from typing import List

class Translator:
    """
    新闻翻译模块：异步翻译标题、摘要、正文
    """

    def __init__(self, type: str = "llm", model_name: str = "deepseek"):
        self.type = type
        self.model_name = model_name

        if self.type == "llm":
            factory = LLMClientFactory()
            self._client = factory.get_client(model_name)

    async def llm_translate_async(self, news_item: NewsItemRawSchema, target_language: str = "zh") -> NewsItemRefinedSchema:
        """
        异步翻译单条新闻的标题、摘要、正文
        """
        system_prompt = TRANSLATION_PROMPT_CN["SYSTEM_PROMPT"]

        # 分别翻译标题、摘要、正文
        title_prompt = TRANSLATION_PROMPT_CN["USER_PROMPT_TEMPLATE"].format(
            text=news_item.title or "",
            target_language=target_language
        )
        abstract_prompt = TRANSLATION_PROMPT_CN["USER_PROMPT_TEMPLATE"].format(
            text=news_item.abstract or "",
            target_language=target_language
        )
        body_prompt = TRANSLATION_PROMPT_CN["USER_PROMPT_TEMPLATE"].format(
            text=news_item.body or "",
            target_language=target_language
        )

        # 调用 LLM 异步接口
        async def translate_text(prompt: str) -> str:
            response = await self._client.chat.completions.create(
                model=self._get_model_name(self.model_name),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            return response.choices[0].message.content

        translated_title, translated_abstract, translated_body = await asyncio.gather(
            translate_text(title_prompt),
            translate_text(abstract_prompt),
            translate_text(body_prompt),
        )
        print(type(news_item.published_at))
        # 构建返回结果
        refined_item = NewsItemRawSchema(
            unique_id=news_item.unique_id,
            source_id=news_item.source_id,
            source_channel=news_item.source_channel,
            source_url=news_item.source_url,
            published_at=news_item.published_at,
            title=translated_title,
            abstract=translated_abstract,
            body=translated_body,
            attachments=news_item.attachments,
            extra_data=news_item.extra_data,
        )

        return refined_item

    async def translate_batch(self, news_list: List[NewsItemRawSchema], target_language: str = "zh") -> List[NewsItemRawSchema]:
        """
        异步批量翻译，使用 asyncio.gather 并发处理
        """
        semaphore = asyncio.BoundedSemaphore(5)  # 控制并发数量

        async def safe_translate(item):
            async with semaphore:
                if self.type == "llm":
                    return await self.llm_translate_async(item, target_language)

        tasks = [safe_translate(item) for item in news_list]
        return await asyncio.gather(*tasks)

    def _get_model_name(self, model_name: str = "deepseek") -> str:
        """
        根据传入的模型名称，返回实际使用的模型名称
        """
        model_map = {
            "deepseek": "deepseek-chat",
            "gpt-4": "gpt-4",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
        }
        return model_map.get(model_name, model_name)
