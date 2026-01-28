#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-09 23:37:21
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-10 22:47:18
# FilePath: \NewsPilot\src\data_acquisition\processors\module\translator.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

from core.news_schemas import NewsItemRawSchema, NewsItemRefinedSchema
from src.module.init_client import LLMClientFactory
from config.prompts import TRANSLATION_PROMPT_CN

import asyncio
from typing import List, Tuple
from tqdm.asyncio import tqdm_asyncio

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

    async def close(self):
        if hasattr(self, '_client') and self._client:
            await self._client.close()

    async def llm_translate_async(self, news_item: NewsItemRawSchema, target_language: str = "zh") -> NewsItemRawSchema:
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

        if self.model_name == 'deepseek':
            translated_title, translated_abstract, translated_body = await self.deepseek_translate(
                system_prompt,
                title_prompt,
                abstract_prompt,
                body_prompt,
                model_id = "deepseek-chat"
            )
        elif self.model_name == 'gemini':
            raise NotImplementedError("Gemini 翻译尚未实现")
        elif self.model_name == 'gpt':
            raise NotImplementedError("GPT 翻译尚未实现")
        else:
            raise ValueError(f"Unsupported translation model: {self.model_name}")

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
        return await tqdm_asyncio.gather(
            *tasks,
            desc="Translating news",
            total=len(tasks)
        )
    
    async def deepseek_translate(self, system_prompt: str, title_prompt: str, abstract_prompt: str, body_prompt: str, model_id: str) -> Tuple[str, str, str]:
        # 调用 LLM 异步接口
        async def translate_text(prompt: str) -> str:
            response = await self._client.chat.completions.create(
                model=model_id,
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
        return translated_title, translated_abstract, translated_body
