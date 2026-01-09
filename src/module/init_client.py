#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-09 22:52:52
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-10 00:39:58
# FilePath: \NewsPilot\src\module\init_client.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

from openai import AsyncOpenAI
from config import keys

class LLMClientFactory:
    """
    单独封装 LLM 客户端初始化
    """

    def __init__(self):
        self.client_init = {
            "gpt-4": self._init_gpt4,
            "gpt-3.5-turbo": self._init_gpt35,
            "deepseek": self._init_deepseek,
        }

    def get_client(self, model_name: str) ->AsyncOpenAI:
        """
        返回初始化好的 client
        """
        if model_name not in self.client_init:
            raise ValueError(f"Unsupported model: {model_name}")
        return self.client_init[model_name]()

    # ----------------- 初始化不同模型 -----------------
    def _init_gpt4(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=keys.openai_api, model="gpt-4")
    def _init_gpt35(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=keys.openai_api, model="gpt-3.5-turbo")      
    def _init_deepseek(self) ->AsyncOpenAI:
        return AsyncOpenAI(api_key=keys.deepseek_api, base_url="https://api.deepseek.com")
