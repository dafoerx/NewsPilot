# src/intelligence/new_analyzer.py
"""
新闻分析引擎 - 不管理用户画像，只专注分析
职责：
1. (Function A) 入口：协调获取新闻、分类、调用生成、保存文件
2. (Function B) 生成：针对单分类准备 Prompt 并调用 LLM
3. LLM 适配：兼容 OpenAI 格式 (DeepSeek, GPT, Qwen) 和 Gemini
"""

import os
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, ThinkingConfig, Tool

from core.news_schemas import NewsItemRefinedSchema
from src.module.init_client import LLMClientFactory
from config.prompts import CATEGORY_DAILY_REPORT_PROMPT
from src.storage.repository import StorageRepository
from src.storage.models import RefinedNews

class NewsAnalyzer:
    def __init__(self, model_name: str = "gemini"):
        self.factory = LLMClientFactory()
        self.repo = StorageRepository()
        self.model_name = model_name
        self.client = self.factory.get_client(model_name)
        
        self.category_map = {
            "policy_regulation": "政策与法规",
            "macro_economy": "宏观经济",
            "markets": "金融市场",
            "company_business": "公司与商业",
            "technology": "科技前沿",
            "energy_commodities": "能源与大宗商品",
            "geopolitics": "地缘政治",
            "society_public_safety": "社会与公共安全",
            "environment_climate": "环境与气候",
            "health_medicine": "医疗健康"
        }

    async def generate_all_daily_reports(
        self, 
        target_date: Optional[datetime.date] = None, 
        save_path: Optional[str] = None,
        time_range: Optional[tuple[datetime, datetime]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        核心入口
        :param target_date: 报告归属日期（用于文件名和默认的时间范围 00:00-23:59）
        :param save_path: 保存路径
        :param time_range: (start_time, end_time) 自定义抓取时间范围。如果提供，将忽略 target_date 的默认范围。
        """
        if not target_date and not time_range:
             target_date = datetime.now().date()
             
        display_date = target_date if target_date else time_range[1].date()
        
        print(f"[*] 开始生成 {display_date} 日报，使用模型: {self.model_name}")
        
        # 1. 准备数据
        news_items = self._fetch_news(target_date, time_range)
        if not news_items:
            print(f"[!] {display_date} (范围: {time_range}) 无新闻数据")
            return {}
            
        categorized_news = self._classify_news(news_items)
        print(f"[*] 新闻分类完成，覆盖 {len([k for k,v in categorized_news.items() if v])} 个领域")
        
        results = {}
        tasks = []
        
        # 2. 创建并执行生成任务
        for category, items in categorized_news.items():
            if not items:
                continue
            
            # task 直接使用 self.client，无需传递 model_name
            task = self._generate_single_category_content(category, items, display_date)
            tasks.append((category, task))
            
        if not tasks:
            return {}
            
        # 并行等待
        cat_keys = [t[0] for t in tasks]
        awaitables = [t[1] for t in tasks]
        
        print(f"[*] 正在调用 LLM 生成 {len(tasks)} 个领域的报告...")
        analysis_contents = await asyncio.gather(*awaitables)
        
        # 3. 处理结果
        for category, content in zip(cat_keys, analysis_contents):
            md_content = self._construct_md_report(category, content, display_date)
            results[category] = {
                "llm_output": content,
                "md_content": md_content
            }
            if save_path:
                self._save_md_file(save_path, display_date, category, md_content)
                
        print(f"[*] 所有报告生成完毕。")
        return results

    # ... _fetch_news 和 _classify_news 保持不变 ...
    def _fetch_news(self, target_date: Optional[datetime.date], time_range: Optional[tuple[datetime, datetime]] = None) -> List[RefinedNews]:
        """辅助：从数据库拉取 RefinedNews"""
        if time_range:
            date_from, date_to = time_range
        elif target_date:
            date_from = datetime.combine(target_date, datetime.min.time())
            date_to = datetime.combine(target_date, datetime.max.time())
        else:
             return []

        print(f"   [-] Fetching news from {date_from} to {date_to}")
        return self.repo.list_refined_news(
            date_from=date_from, 
            date_to=date_to, 
            date_field="published_at"
        )

    def _classify_news(self, news_items: List[RefinedNews]) -> Dict[str, List[RefinedNews]]:
        """辅助：按 Label 分类"""
        categorized = {cat: [] for cat in self.category_map.keys()}
        for news in news_items:
            if not news.categories:
                continue
            tags = news.categories if isinstance(news.categories, list) else []
            for tag in tags:
                if tag in categorized:
                    categorized[tag].append(news)
        return categorized

    async def _generate_single_category_content(
        self, 
        category: str, 
        news_items: List[RefinedNews], 
        date: datetime.date
    ) -> str:
        """
        单个领域的分析逻辑
        """
        # 1. 提取指令
        instruction = CATEGORY_DAILY_REPORT_PROMPT["CATEGORY_INSTRUCTIONS"].get(category, "综合分析行业动态。")
        
        # 2. 格式化新闻
        news_text_list = []
        for item in news_items:
            time_str = item.published_at.strftime('%H:%M')
            abstract = item.abstract[:150] + "..." if item.abstract and len(item.abstract) > 150 else item.abstract
            news_text_list.append(f"- [{time_str}] {item.title}: {abstract}")
        news_text = "\n".join(news_text_list)
        
        # 3. 填充 Prompt
        system_prompt = CATEGORY_DAILY_REPORT_PROMPT["SYSTEM_PROMPT"].format(
            category=self.category_map.get(category, category),
            instruction=instruction
        )
        
        user_prompt = CATEGORY_DAILY_REPORT_PROMPT["USER_PROMPT_TEMPLATE"].format(
            date=date.strftime("%Y-%m-%d"),
            category=self.category_map.get(category, category),
            count=len(news_items),
            news_list=news_text
        )
        
        # 4. 调用 LLM 并获取 JSON 字符串 (含重试逻辑)
        max_retries = 3
        raw_output = ""
        
        for attempt in range(max_retries):
            raw_output = await self._call_llm(system_prompt, user_prompt)
            
            # 简单验证 JSON 完整性
            # 清洗
            check_text = re.sub(r"^```json\s*", "", raw_output.strip(), flags=re.MULTILINE)
            check_text = re.sub(r"\s*```$", "", check_text, flags=re.MULTILINE)
            
            try:
                json.loads(check_text)
                # 校验成功，跳出循环
                break
            except json.JSONDecodeError:
                print(f"[!] JSON 校验失败 ({attempt+1}/{max_retries})，正在重试: {category}")
                continue
        
        # 5. 解析 JSON 并渲染为 Markdown
        return self._render_json_to_md(raw_output)

    def _render_json_to_md(self, json_text: str) -> str:
        """
        [V2] 将 LLM 返回的 JSON 字符串解析并渲染为标准化 Markdown
        核心逻辑：严格区分事实、反应与研判
        """
        # 1. 清洗 JSON 字符串
        cleaned_text = re.sub(r"^```json\s*", "", json_text.strip(), flags=re.MULTILINE)
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text, flags=re.MULTILINE)
        
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            return f"> ⚠️ 格式解析失败，显示原始输出：\n\n{json_text}"
            
        # 2. 渲染 Markdown
        md_lines = []
        meta = data.get("meta", {})
        
        # 头部
        md_lines.append("")
        md_lines.append(f"> 📊 **情报综述** | 覆盖新闻数: {meta.get('news_coverage_count', 'N/A')} | 生成时间: {datetime.now().strftime('%H:%M')}")
        md_lines.append("")
        
        # 每日综述 (Overall Commentary) - New
        overall = data.get("overall_commentary", "")
        if overall:
            md_lines.append("## 📝 重点综述")
            md_lines.append(f"{overall}\n")
            md_lines.append("---")

        # A. 核心情报 (Core Events)
        core_events = data.get("core_events", [])
        if core_events:
            md_lines.append("## 🔥 核心情报")
            for i, event in enumerate(core_events, 1):
                title = event.get("title", "未命名情报")
                facts = event.get("facts", {})
                what_happened = facts.get("what_happened", "")
                data_points = facts.get("data_points", [])
                reactions = event.get("reactions", "未观察到显著反应")
                analysis = event.get("system_analysis", "")
                sources = event.get("sources", [])
                
                # 标题
                md_lines.append(f"### {i}. {title}")
                
                # 事实层
                md_lines.append(f"{what_happened}")
                if data_points:
                    points_str = "、".join([f"`{dp}`" for dp in data_points])
                    md_lines.append(f"*   **关键数据**: {points_str}")
                
                # 来源标注
                if sources:
                    md_lines.append(f"*   <small style='color:grey'>来源: {', '.join(sources)}</small>")

                # 反应层
                md_lines.append("")
                if reactions and reactions != "未观察到显著反应":
                     md_lines.append(f"> 📢 **各方反应**: {reactions}")
                
                # 研判层 (专家模型研判)
                outlook = event.get("expert_outlook", {})
                # 兼容旧字段 system_analysis
                sys_analysis = event.get("system_analysis", "")
                
                if outlook or sys_analysis:
                     md_lines.append(f"> 🧠 **专家模型研判**")
                     
                     if sys_analysis: # Fallback for old data
                         md_lines.append(f"> *   **分析**: {sys_analysis}")
                     
                     if outlook:
                         eval_text = outlook.get("evaluation", "")
                         pred_text = outlook.get("prediction", "")
                         counter_text = outlook.get("counterfactual_analysis", "")
                         
                         if eval_text:
                            md_lines.append(f"> *   **评价**: {eval_text}")
                         if pred_text:
                            md_lines.append(f"> *   **预测**: {pred_text}")
                         if counter_text:
                            md_lines.append(f"> *   **反向推演**: {counter_text}")

                md_lines.append("---")
        
        # B. 行业扫描 (Industry Scan)
        industry_scan = data.get("industry_scan", [])
        if industry_scan:
            md_lines.append("## 📰 行业扫描")
            for item in industry_scan:
                sub_topic = item.get("sub_topic", "通用")
                briefs = item.get("briefs", [])
                
                md_lines.append(f"**🔹 {sub_topic}**")
                if isinstance(briefs, list):
                    for brief in briefs:
                        md_lines.append(f"- {brief}")
                else:
                    md_lines.append(f"- {briefs}")
                md_lines.append("")
        
        # C. 市场监测 (Market Monitor)
        monitor = data.get("market_monitor", {})
        if monitor:
            md_lines.append("## 📉 市场监测")
            observed = monitor.get("observed_changes", "未录得显著波动")
            signal = monitor.get("trend_signal", "观望")
            
            md_lines.append(f"- **市场变动**: {observed}")
            md_lines.append(f"- **系统信号**: `{signal}`")
            md_lines.append("")

        return "\n".join(md_lines)

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """底层 LLM 调用路由"""
        # 策略 1: Gemini
        if self.model_name == "gemini":
            try:
                MODEL_ID = "gemini-3-pro-preview"
                combined_prompt = f"{system_prompt}\n\nTasks:\n{user_prompt}"
                
                # 使用 self.client (genai.Client)
                response = await self.client.aio.models.generate_content(
                    model=MODEL_ID,
                    contents=combined_prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_level="high"),
                        tools=[
                            # {"url_context": {}}, 
                            {"google_search": {}}
                        ],
                        temperature=0.3,
                        max_output_tokens=10000000
                    )
                )
                return response.text
            except Exception as e:
                return f"Gemini Error: {str(e)}"

        # 策略 2: OpenAI Compatible
        else:
            api_model_map = {
                "deepseek": "deepseek-chat",
                "gpt": "gpt-4o",
                "qwen": "qwen-max", 
            }
            actual_model = api_model_map.get(self.model_name, self.model_name)
            
            try:
                # 使用 self.client (AsyncOpenAI)
                response = await self.client.chat.completions.create(
                    model=actual_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"LLM Error ({self.model_name}): {str(e)}"

    def _construct_md_report(self, category: str, body_content: str, date: datetime.date) -> str:
        """[Function MD] 构造 Markdown"""
        cn_name = self.category_map.get(category, category)
        header = f"# 📅 {cn_name} 行业深度日报\n"
        meta = f"> 日期: {date.strftime('%Y-%m-%d')} | 来源: NewsPilot Intelligence\n\n"
        return f"{header}{meta}{body_content}"

    def _save_md_file(self, base_path: str, date: datetime.date, category: str, content: str):
        """保存文件"""
        date_subfolder = date.strftime("%Y-%m-%d")
        folder = os.path.join(base_path, date_subfolder)
        os.makedirs(folder, exist_ok=True)
        filename = f"{category}.md"
        full_path = os.path.join(folder, filename)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   [+] 已保存: {full_path}")
        except Exception as e:
            print(f"   [!] 保存失败: {e}")

if __name__ == "__main__":
    async def main():
        MODEL = "gemini"
        SAVE_DIR = r"E:\code\NewsPilot\data\daily_reports"
        analyzer = NewsAnalyzer(model_name=MODEL)

        # 模式1: 聚合分析 (生成一份包含 1月1日-1月30日 信息的综合报告)
        start_time = datetime(2026, 1, 28, 0, 0, 0)
        end_time = datetime(2026, 1, 30, 23, 59, 59)
        
        print(f"--- 模式1: 启动长周期聚合分析 ({start_time.date()} ~ {end_time.date()}) ---")
        await analyzer.generate_all_daily_reports(
            time_range=(start_time, end_time),
            save_path=SAVE_DIR
        )

        # 模式2 (可选): 逐日回溯 (每天生成一份日报)
        # print(f"\n--- 模式2: 启动逐日历史回溯 ---")
        # current = start_time
        # while current <= end_time:
        #     print(f">>> 生成日报: {current.date()}")
        #     await analyzer.generate_all_daily_reports(
        #         target_date=current.date(),
        #         save_path=SAVE_DIR
        #     )
        #     current += timedelta(days=1)
        #     await asyncio.sleep(2) # 避免限流

        print("\n--- 任务完成 ---")

    asyncio.run(main())
