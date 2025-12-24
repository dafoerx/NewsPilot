'''
Author: WangQiushuo 185886867@qq.com
Date: 2025-12-24 22:52:51
LastEditors: WangQiushuo 185886867@qq.com
LastEditTime: 2025-12-24 23:20:06
FilePath: \NewsPilot\src\modules\world_engine\ports\output_port.py
Description: 

Copyright (c) 2025 by , All Rights Reserved. 
'''
from ..adapters import persistence

def export_delta(date: str):
    history = persistence.load_json("delta_history.json")
    return [h for h in history if h["date"] == date]
