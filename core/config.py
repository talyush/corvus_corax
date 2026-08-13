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

def load_rules():
    """
    v0.9 — Merkezi kural/konfigürasyon dosyalarını (config/rules.json) yükler.
    Admiralty kanıt ağırlıkları, kaynak güvenilirlikleri, ilişki politikaları,
    operatör prefix'leri ve sosyal platformlar buradan okunur.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "config", "rules.json")

    default_rules = {
        "evidence_weights": {},
        "source_reliability": {},
        "relationship_policies": {},
        "operator_prefixes": {},
        "social_platforms": {}
    }

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            if isinstance(data, dict):
                return data
            return default_rules
    except Exception as e:
        print(f"[RULES ERROR] {e}")
        return default_rules