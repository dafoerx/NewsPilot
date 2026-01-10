# src/intelligence/news_analyzer.py
"""
新闻分析引擎 - 不管理用户画像，只专注分析
"""

from typing import List
from core.news_schemas import NewsItemRefinedSchema
from core.analysis_schemas import DailyDigest, TrendAnalysis
from src.module.init_client import LLMClientFactory
from config.prompts import DAILY_DIGEST_PROMPT, TREND_ANALYSIS_PROMPT

class NewsAnalyzer:
    """
    新闻分析引擎
    职责：
    1. 生成每日报告（客观分析，无个性化）
    2. 提取趋势
    3. 识别关键事件
    
    不负责：
    - 用户画像管理
    - 个性化推荐生成
    """
    
    def __init__(self, model_name: str = "deepseek"):
        factory = LLMClientFactory()
        self.llm = factory.get_client(model_name)
        self.model_name = model_name
    
    async def generate_daily_digest(
        self, 
        news_items: List[NewsItemRefinedSchema]
    ) -> DailyDigest:
        """
        生成每日新闻摘要（客观、无个性化）
        
        这个摘要：
        1. 供用户阅读
        2. 作为 World Engine 的输入
        """
        # 准备新闻列表文本
        news_text = self._format_news_for_prompt(news_items)
        
        # 调用 LLM
        system_prompt = DAILY_DIGEST_PROMPT["SYSTEM_PROMPT"]
        user_prompt = DAILY_DIGEST_PROMPT["USER_PROMPT_TEMPLATE"].format(
            count=len(news_items),
            news_list=news_text,
            date=news_items[0].published_at.strftime("%Y-%m-%d") if news_items else ""
        )
        
        response = await self.llm.chat.completions.create(
            model=self._get_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3  # 较低温度，保证客观性
        )
        
        digest_text = response.choices[0].message.content
        
        # 构建结果对象
        return DailyDigest(
            date=news_items[0].published_at.strftime("%Y-%m-%d"),
            total_news_count=len(news_items),
            digest_text=digest_text,
            news_ids=[item.unique_id for item in news_items]
        )
    
    async def extract_trends(
        self, 
        news_items: List[NewsItemRefinedSchema]
    ) -> TrendAnalysis:
        """
        提取关键趋势
        """
        # 类似实现...
        pass
    
    def _format_news_for_prompt(
        self, 
        news_items: List[NewsItemRefinedSchema]
    ) -> str:
        """格式化新闻为文本"""
        formatted = []
        for i, item in enumerate(news_items, 1):
            formatted.append(
                f"{i}. [{item.source_channel}] {item.title}\n"
                f"   摘要：{item.abstract[:200]}...\n"
                f"   链接：{item.source_url}"
            )
        return "\n\n".join(formatted)
    
    def _get_model_name(self) -> str:
        model_map = {
            "deepseek": "deepseek-chat",
            "gpt-4": "gpt-4"
        }
        return model_map.get(self.model_name, self.model_name)
    
    async def close(self):
        if self.llm:
            await self.llm.close()