'''
Author: WangQiushuo 185886867@qq.com
Date: 2025-12-24 22:52:04
LastEditors: WangQiushuo 185886867@qq.com
LastEditTime: 2025-12-24 23:19:36
FilePath: \NewsPilot\src\modules\world_engine\pipeline\daily_maintenance.py
Description: 

Copyright (c) 2025 by , All Rights Reserved. 
'''
from ..engine.engine_manager import EngineManager
from ..adapters import persistence

def daily_decay(state_file="state_core.json"):
    data = persistence.load_json(state_file)
    engine = EngineManager.from_dict(data)
    engine.decay_l0()
    persistence.save_json(state_file, engine.to_dict())
