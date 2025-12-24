'''
Author: WangQiushuo 185886867@qq.com
Date: 2025-12-24 22:50:29
LastEditors: WangQiushuo 185886867@qq.com
LastEditTime: 2025-12-24 23:16:18
FilePath: \NewsPilot\src\modules\world_engine\engine\engine_manager.py
Description: 

Copyright (c) 2025 by , All Rights Reserved. 
'''
from ..domain.world_state import WorldState
from ..domain.signal import Signal
from ..domain import constants

class EngineManager:
    def __init__(self, state: WorldState = None):
        self.state = state or WorldState()

    def apply_signal(self, signal: Signal):
        """根据 Signal 更新四层状态"""
        # L0 背景 (慢速迭代)
        self.state.l0_background[signal.id] = {
            "content": signal.content,
            "importance": signal.importance
        }

        # L1 趋势 (中速)
        if signal.importance >= constants.L1_IMPORTANCE_THRESHOLD:
            self.state.L1_trends[signal.id] = signal.content

        # L2 行动窗口 (高价值)
        if signal.importance > 0.7:
            self.state.L2_windows[signal.id] = {
                "content": signal.content,
                "timestamp": signal.timestamp
            }

        # L3 即时触发 (稀有)
        if signal.importance > 0.9:
            self.state.L3_triggers.append({
                "id": signal.id,
                "content": signal.content,
                "timestamp": signal.timestamp
            })

    def decay_L0(self):
        """L0 衰减"""
        for k in list(self.state.L0_background.keys()):
            self.state.L0_background[k]["importance"] *= constants.L0_DECAY_RATE
            if self.state.L0_background[k]["importance"] < 0.01:
                del self.state.L0_background[k]

    def to_dict(self):
        return {
            "L0_background": self.state.L0_background,
            "L1_trends": self.state.L1_trends,
            "L2_windows": self.state.L2_windows,
            "L3_triggers": self.state.L3_triggers
        }

    @classmethod
    def from_dict(cls, data: dict):
        from ..domain.world_state import WorldState
        state = WorldState(
            L0_background=data.get("L0_background", {}),
            L1_trends=data.get("L1_trends", {}),
            L2_windows=data.get("L2_windows", {}),
            L3_triggers=data.get("L3_triggers", [])
        )
        return cls(state=state)
