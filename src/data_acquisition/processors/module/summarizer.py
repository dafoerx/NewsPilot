from core.news_schemas import NewsItemRawSchema, Attachment , SupportingDocumentSchema, NewsItemRefinedSchema
from src.module.init_client import LLMClientFactory
from config.prompts import SUMMARY_PROMPT_CN
    
import asyncio

from typing import List

class Summarizer:
    def __init__(self, type: str = "llm", model_name: str = "deepseek"):
        self.type = type
        self.model_name = model_name

        if self.type == "llm":
            factory = LLMClientFactory()
            self._client = factory.get_client(model_name)

    async def close(self):
        if hasattr(self, '_client') and self._client:
            await self._client.close()

    async def llm_summarize_async(self, news_item: NewsItemRawSchema) -> NewsItemRefinedSchema:
        system_prompt = SUMMARY_PROMPT_CN["SYSTEM_PROMPT"]
        user_prompt = SUMMARY_PROMPT_CN["USER_PROMPT_TEMPLATE"].format(
            title=news_item.title,
            abstract=news_item.abstract,
            body=news_item.body
        )
        if self.model_name == 'deepseek':
            model_id = "deepseek-chat"
            abstract = await self.deepseek_summarize(system_prompt, user_prompt, model_id=model_id)

        refined_item = NewsItemRefinedSchema(
            unique_id=news_item.unique_id,
            source_id=news_item.source_id,
            source_channel=news_item.source_channel,
            source_url=news_item.source_url,
            NewsItemRaw_id=news_item.unique_id,
            published_at=news_item.published_at,
            title=news_item.title,
            abstract=abstract,
            attachments=news_item.attachments,
            extra_data=news_item.extra_data,
        )
        return refined_item

    async def summarize_batch(self, news_list: List[NewsItemRawSchema]) -> List[NewsItemRefinedSchema]:
        
        semaphore = asyncio.BoundedSemaphore(5)
        async def safe_summarize(item):
            async with semaphore:
                if self.type == "llm":
                    return await self.llm_summarize_async(item)
                

        tasks = [safe_summarize(item) for item in news_list]
        return await asyncio.gather(*tasks)

    async def deepseek_summarize(
        self,
        system_prompt: str,
        user_prompt: str,
        model_id: str = "deepseek-chat"
    ) -> str:
        response = await self._client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        summary = response.choices[0].message.content
        return summary