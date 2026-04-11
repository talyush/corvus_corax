import os
import json
def load_config():
    path = "config/config.json"
    
    print("CONFIG PATH:", os.path.abspath(path))  # 👈 EKLE

    try:
        with open(path, "r") as f:
            content = f.read()
            print("CONFIG CONTENT:", repr(content))  # 👈 EKLE
            return json.loads(content)
    except Exception as e:
        print(f"[CONFIG ERROR] {e}")
        return {}