from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Signal:
    id: str
    timestamp: str
    category: str # ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    importance: float # 0.0 ~ 1.0 
    content: Dict[str, Any]