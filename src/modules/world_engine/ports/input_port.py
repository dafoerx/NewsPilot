'''
Author: WangQiushuo 185886867@qq.com
Date: 2025-12-24 22:52:34
LastEditors: WangQiushuo 185886867@qq.com
LastEditTime: 2025-12-24 23:19:46
FilePath: \NewsPilot\src\modules\world_engine\ports\input_port.py
Description: 

Copyright (c) 2025 by , All Rights Reserved. 
'''
from ..domain.signal import Signal
from ..pipeline.apply_signal import process_signal

def receive_signal(signal_data: dict):
    signal = Signal(**signal_data)
    updated_state = process_signal(signal)
    return updated_state
