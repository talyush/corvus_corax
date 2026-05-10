import os
import json
def load_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "config", "config.json")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content)
    except Exception as e:
        print(f"[CONFIG ERROR] {e}")
        return {}