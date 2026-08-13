"""Corvus Corax v0.9 — Kalıcı Depolama (The Machine Hafızası).

ContextManager'ın tüm data dict'ini JSON olarak diske kaydeder ve geri yükler.
Oturumlar arası veri kalıcılığı sağlar — istihbarat oturum kapatılsa bile kaybolmaz.
"""
import os
import json
from datetime import datetime, timezone


def save_state(context_manager, filepath="logs/state.json"):
    """
    ContextManager'ın tüm verisini JSON dosyasına kaydeder.
    Returns: (bool, message)
    """
    try:
        # Dizin oluştur
        dir_name = os.path.dirname(filepath) if filepath else ""
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        # Context data + meta
        state = {
            "version": "0.9",
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "context": context_manager.get_clean_data() if hasattr(context_manager, "get_clean_data") else context_manager.data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)

        return True, f"State saved to {filepath}"
    except Exception as e:
        return False, f"Failed to save state: {e}"


def load_state(context_manager, filepath="logs/state.json"):
    """
    Kaydedilmiş durumu ContextManager'a geri yükler.
    Returns: (bool, message)
    """
    try:
        if not os.path.exists(filepath):
            return False, f"State file not found: {filepath}"

        with open(filepath, "r", encoding="utf-8") as f:
            state = json.loads(f.read())

        if "context" not in state:
            return False, "Invalid state file: missing 'context' key"

        context_data = state["context"]

        # ContextManager.data'yı doğrudan doldur (get_clean_data çıktısı korunur)
        if hasattr(context_manager, "data"):
            context_manager.data = context_data

        # Eğer eski format (ips/domains vb.) varsa, entity registry'yi senkronize et
        _sync_legacy_to_entities(context_manager)

        saved_at = state.get("saved_at", "unknown")
        return True, f"State loaded from {filepath} (saved: {saved_at})"
    except Exception as e:
        return False, f"Failed to load state: {e}"


def save_geoint(context_manager, filepath="logs/geoint.geojson"):
    """
    GEOINT verisini GeoJSON formatında dışa aktarır.
    Returns: (bool, message, geojson_data)
    """
    features = []

    # Location entity'lerini topla
    entities = context_manager.data.get("entities", {})
    ip_data = context_manager.data.get("ips", {})
    relations = context_manager.data.get("relations", [])

    # IP'lerin geo bilgilerini topla
    for ip, ipd in ip_data.items():
        geo = ipd.get("geo", {})
        lat = geo.get("latitude") or geo.get("lat")
        lon = geo.get("longitude") or geo.get("lon")
        if lat is not None and lon is not None:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": {
                    "entity": ip,
                    "type": "ip",
                    "label": f"{geo.get('city', '')}, {geo.get('country', '')}".strip(", "),
                    "isp": geo.get("isp") or geo.get("org") or "",
                    "hostname": ipd.get("hostname") or "",
                    "ports": [p.get("port") for p in ipd.get("ports", [])],
                }
            })

    # Location entity'lerini ekle (geo verisi olanlar)
    for key, ent in entities.items():
        ent_type = ent.get("type")
        ent_val = ent.get("value")
        props = ent.get("properties", {})
        if ent_type == "location":
            lat = props.get("latitude") or props.get("lat")
            lon = props.get("longitude") or props.get("lon")
            if lat is not None and lon is not None:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                    "properties": {
                        "entity": ent_val,
                        "type": "location",
                        "label": ent_val,
                        "isp": props.get("ip", ""),
                        "country": props.get("country", ""),
                        "city": props.get("city", ""),
                    }
                })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    try:
        dir_name = os.path.dirname(filepath) if filepath else ""
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=4, ensure_ascii=False)
        return True, f"GeoJSON exported to {filepath}", geojson
    except Exception as e:
        return False, f"Failed to export GeoJSON: {e}", geojson


def save_timeline(context_manager, entity, filepath="logs/timeline.json"):
    """
    Belirli bir varlığın temporal olaylarından zaman çizelgesi üretir.
    Format Pattern of Life (POL) motoruna hazır.
    Returns: (bool, message, timeline_data)
    """
    events = context_manager.data.get("events", [])
    timeline = []
    entity_str = str(entity)

    for ev in events:
        ev_entity = ev.get("entity", "")
        if entity_str not in ev_entity:
            continue
        meta = ev.get("metadata", {})
        entry = {
            "time": ev.get("timestamp"),
            "action": ev.get("action"),
            "source": ev.get("source"),
        }
        # Konum bilgisi metadata'da varsa ekle
        if "lat" in meta and "lon" in meta:
            entry["lat"] = meta["lat"]
            entry["lon"] = meta["lon"]
        if "location" in ev:
            entry["location"] = ev["location"]
        # location geçmişi: located_in olayındaki metadata'dan
        if ev.get("action") == "located_in" and ev.get("location"):
            entry["lat"] = None  # location string'i var ama koordinat yok — ayrı işlenir
        timeline.append(entry)

    result = {
        "entity": entity_str,
        "timeline": timeline,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        dir_name = os.path.dirname(filepath) if filepath else ""
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        return True, f"Timeline exported to {filepath}", result
    except Exception as e:
        return False, f"Failed to export timeline: {e}", result


def _sync_legacy_to_entities(context_manager):
    """Eski format (ips/domains) yüklendiyse entity registry'yi senkronize eder."""
    data = context_manager.data
    if not hasattr(context_manager, "data") or not isinstance(data, dict):
        return

    # entities kontrol
    if "entities" not in data:
        data["entities"] = {}
    if "events" not in data:
        data["events"] = []

    # ip entity'leri
    for ip, ipd in data.get("ips", {}).items():
        key = f"ip:{ip}"
        if key not in data["entities"]:
            data["entities"][key] = {
                "type": "ip",
                "value": ip,
                "properties": {"ports": ipd.get("ports", []), "geo": ipd.get("geo", {}), "hostname": ipd.get("hostname")},
                "created_at": None,
                "updated_at": None,
            }

    # domain entity'leri
    for dom, domd in data.get("domains", {}).items():
        key = f"domain:{dom}"
        if key not in data["entities"]:
            data["entities"][key] = {
                "type": "domain",
                "value": dom,
                "properties": {"ips": domd.get("ips", [])},
                "created_at": None,
                "updated_at": None,
            }


# ============================================================
# v0.9 — INTELLIGENCE VAULT (The Machine Uzun Süreli Hafızası)
# ============================================================

class IntelligenceVault:
    """
    Kalıcı istihbarat kasası — oturumlar arası hafıza.

    Üç katmanlı mimari:
      1. Session Context (RAM) — geçici, oturum sonunda kaybolur
      2. Intelligence Vault (Disk) — kalıcı, onaylanmış kanıt
      3. POL Engine (Analiz) — vault'tan okur, davranış deseni çıkarır

    Veri modeli:
      vault/events.log       — Append-only JSONL (her satır bir event)
      vault/index.json       — {entity: [line_numbers], action: [line_numbers]}
      vault/state.json       — Varlık envanteri (entities, relations, notes)
      vault/evidence/        — Onaylanmış kanıt zincirleri
      vault/stats.json       — Vault istatistikleri
    """

    def __init__(self, vault_dir="vault"):
        self.vault_dir = vault_dir
        self.events_log = os.path.join(vault_dir, "events.log")
        self.index_file = os.path.join(vault_dir, "index.json")
        self.state_file = os.path.join(vault_dir, "state.json")
        self.evidence_dir = os.path.join(vault_dir, "evidence")
        self.stats_file = os.path.join(vault_dir, "stats.json")
        self._init_dirs()

    def _init_dirs(self):
        """Vault dizin yapısını oluşturur."""
        for d in [self.vault_dir, self.evidence_dir]:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
        if not os.path.exists(self.events_log):
            with open(self.events_log, "w", encoding="utf-8") as f:
                f.write("")
        if not os.path.exists(self.index_file):
            self._save_index({})

    def _load_index(self):
        """index.json'u yükler."""
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.loads(f.read())
        except Exception:
            return {}

    def _save_index(self, index):
        """index.json'u kaydeder."""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def should_persist(self, event):
        """
        Kanıt filtresi — hangi event'ler vault'a kalıcı yazılır.
        Session ↔ Evidence ayrımının kalbi.
        """
        if not isinstance(event, dict):
            return False
        # Test/keşif aşamasındaki olayları kalıcılaştırma
        source = event.get("source", "")
        if source in ("help", "version", "test"):
            return False
        # Düşük güvenilirlikteki candidate/possible ilişkileri kalıcılaştırma
        confidence = event.get("confidence", 0)
        action = str(event.get("action", ""))
        if confidence < 0.5 and any(k in action for k in ("candidate", "possible", "conflict")):
            return False
        return True

    def append_event(self, event):
        """
        Event'i append-only JSONL log'a yazar.
        Returns: (bool, line_number)
        """
        if not self.should_persist(event):
            return False, -1

        # Event'e vault metadata ekle
        event = dict(event)
        event["_vault"] = {
            "persisted_at": datetime.now(timezone.utc).isoformat(),
            "confirmed": True,
        }

        line = json.dumps(event, ensure_ascii=False)
        with open(self.events_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        # Satır numarasını bul (dosya sonundan)
        with open(self.events_log, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        # Index güncelle
        index = self._load_index()
        entity = event.get("entity", "")
        action = event.get("action", "")
        if entity:
            index.setdefault("entities", {}).setdefault(entity, []).append(line_count - 1)
        if action:
            index.setdefault("actions", {}).setdefault(action, []).append(line_count - 1)
        self._save_index(index)

        return True, line_count - 1

    def query_events(self, entity=None, action=None, date_range=None, limit=200):
        """
        Vault'tan event sorgular — index.json üzerinden filtreleme.
        Returns: list of events
        """
        results = []
        index = self._load_index()

        # Index'ten aday satırları bul
        candidate_lines = set()
        if entity:
            for line_no in index.get("entities", {}).get(entity, []):
                candidate_lines.add(line_no)
        if action:
            for line_no in index.get("actions", {}).get(action, []):
                candidate_lines.add(line_no)
        if not entity and not action:
            # Tüm dosyayı tara
            with open(self.events_log, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    candidate_lines.add(i)

        # Aday satırları oku ve filtrele
        with open(self.events_log, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i not in candidate_lines:
                    continue
                try:
                    ev = json.loads(line.strip())
                except Exception:
                    continue
                if entity and ev.get("entity") != entity:
                    continue
                if action and ev.get("action") != action:
                    continue
                if date_range:
                    ts = ev.get("timestamp", "")
                    if date_range[0] and ts < date_range[0]:
                        continue
                    if date_range[1] and ts > date_range[1]:
                        continue
                results.append(ev)
                if limit and len(results) >= limit:
                    break

        return results

    def confirm_event(self, event):
        """
        Session'daki bir event'i kalıcı kanıta dönüştürür (elle onay).
        """
        return self.append_event(event)

    def save_state(self, context_manager):
        """
        Tüm varlık envanterini state.json'a yazar.
        """
        try:
            state = {
                "version": "0.9",
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "context": context_manager.get_clean_data() if hasattr(context_manager, "get_clean_data") else context_manager.data,
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            return True, f"Vault state saved to {self.state_file}"
        except Exception as e:
            return False, f"Failed to save vault state: {e}"

    def load_state(self, context_manager):
        """
        Kalıcı envanteri session'a geri yükler.
        """
        try:
            if not os.path.exists(self.state_file):
                return False, f"Vault state not found: {self.state_file}"
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.loads(f.read())
            if "context" not in state:
                return False, "Invalid vault state: missing 'context'"
            context_manager.data = state["context"]
            _sync_legacy_to_entities(context_manager)
            return True, f"Vault state loaded from {self.state_file}"
        except Exception as e:
            return False, f"Failed to load vault state: {e}"

    def get_casefile(self, entity):
        """
        Bir varlığın tüm kanıt zincirini toplar.
        Returns: casefile dict
        """
        events = self.query_events(entity=entity, limit=500)
        return {
            "entity": entity,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(events),
            "events": events,
        }

    def save_casefile(self, entity, filepath=None):
        """
        Case file'ı diske yazar.
        """
        if not filepath:
            filepath = os.path.join(self.evidence_dir, f"case_{entity.replace(':', '_')}.json")
        casefile = self.get_casefile(entity)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(casefile, f, indent=4, ensure_ascii=False)
            return True, f"Case file saved to {filepath}", casefile
        except Exception as e:
            return False, f"Failed to save case file: {e}", casefile

    def stats(self):
        """
        Vault istatistikleri.
        """
        # Event sayısı
        event_count = 0
        if os.path.exists(self.events_log):
            with open(self.events_log, "r", encoding="utf-8") as f:
                event_count = sum(1 for _ in f)

        # Entity sayısı (index'ten)
        index = self._load_index()
        entity_count = len(index.get("entities", {}))

        # State var mı
        state_exists = os.path.exists(self.state_file)

        return {
            "vault_dir": self.vault_dir,
            "event_count": event_count,
            "entity_count": entity_count,
            "state_exists": state_exists,
            "evidence_files": len(os.listdir(self.evidence_dir)) if os.path.exists(self.evidence_dir) else 0,
        }
