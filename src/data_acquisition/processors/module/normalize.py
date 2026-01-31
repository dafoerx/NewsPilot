#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-31
# FilePath: \NewsPilot\src\data_acquisition\processors\module\normalize.py
# Description: 负责对齐 Raw News 和 Refined News 列表
# 
# Copyright (c) 2026 by , All Rights Reserved. 

from typing import List, Tuple, Dict, Optional
from core.news_schemas import NewsItemRawSchema, NewsItemRefinedSchema

def align_news_lists(
    raw_news_list: List[NewsItemRawSchema],
    refined_news_list: List[NewsItemRefinedSchema]
) -> Tuple[List[NewsItemRawSchema], List[NewsItemRefinedSchema]]:
    """
    根据 NewsItemRefinedSchema.NewsItemRaw_id 将原始新闻和精炼新闻进行对齐。
    

    Args:
        raw_news_list: 原始新闻列表
        refined_news_list: 精炼新闻列表

    Returns:
        Tuple[List[NewsItemRawSchema], List[NewsItemRefinedSchema]]: 
        返回两个列表 (aligned_raw, aligned_refined)。
        这两个列表长度相同，且 aligned_raw[i] 对应 aligned_refined[i]。
    """
    aligned_raw: List[NewsItemRawSchema] = []
    aligned_refined: List[NewsItemRefinedSchema] = []

    for raw_item in raw_news_list:
        uuid7_id = raw_item.unique_id

        refined_item = next(
            (ref_item for ref_item in refined_news_list if ref_item.NewsItemRaw_id == uuid7_id),
            None
        )
        if refined_item:
            raw_item.categories = refined_item.categories
            raw_item.evaluation_score = refined_item.evaluation_score

            aligned_raw.append(raw_item)
            aligned_refined.append(refined_item)



    return aligned_raw, aligned_refined
