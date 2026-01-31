#
# Author: WangQiushuo 185886867@qq.com
# Date: 2026-01-31 20:01:33
# LastEditors: WangQiushuo 185886867@qq.com
# LastEditTime: 2026-01-31 20:01:39
# FilePath: \NewsPilot\src\module\uuid_v7.py
# Description: 
# 
# Copyright (c) 2026 by , All Rights Reserved. 

# 生成时间有序 ID (UUIDv7 模拟) 以优化数据库写入性能
# 这里的实现模拟了 UUIDv7 格式：Timestamp(48bit) + Random(80bit)
import time
import random
import uuid
from typing import Optional
from urllib.parse import urlparse

def generate_uuid7() -> str:
    """生成时间有序的 UUIDv7"""
    u_int = (int(time.time() * 1000) << 80) | random.getrandbits(80)
    # Version 7 (0111) at bits 76-79
    u_int = (u_int & ~(0xF << 76)) | (0x7 << 76)
    # Variant 1 (10) at bits 62-63
    u_int = (u_int & ~(0xC << 62)) | (0x8 << 62)
    unique_id_v7 = str(uuid.UUID(int=u_int))

    return unique_id_v7

def extract_host(url: str) -> Optional[str]:
    """从 URL 中提取 host。

    - 支持标准 URL（带 scheme）
    - 兼容裸域名/不带 scheme 的情况（如 example.com/path）
    """

    if not url:
        return None

    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc.lower()

    # 兼容没有 scheme 的 URL：example.com/path
    parsed2 = urlparse(f"http://{url}")
    return parsed2.netloc.lower() if parsed2.netloc else None