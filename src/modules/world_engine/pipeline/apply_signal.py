import json
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent / "storage"

def load_json(filename: str):
    path = BASE_PATH / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename: str, data):
    path = BASE_PATH / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_delta_history(delta: dict, date: str):
    history = load_json("delta_history.json")
    history_list = history if isinstance(history, list) else []
    history_list.append({"date": date, "delta": delta})
    save_json("delta_history.json", history_list)
