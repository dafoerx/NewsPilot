from dataclasses import dataclass, field
from typing import Any, Dict, List

class WorldState:
    l0_background: Dict[str, Any] = field(default_factory=dict)
    l1_trends: Dict[str, Any] = field(default_factory=dict)
    l2_windows: Dict[str, Any] = field(default_factory=dict)
    l3_triggers: List[Dict[str, Any]] = field(default_factory=list)