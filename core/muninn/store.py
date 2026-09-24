"""Corvus Corax v1.2 - Muninn Persistent Memory Store.

Saves and restores historical entity timelines, snapshots, and observation events.
Uses JSONL append-only logs and JSON indexes under vault/muninn/.
"""
import os
import json
from typing import Dict, Any, Optional, List
from .history import EntityHistory, EntitySnapshot, AttributeChange
from core import vault_path


class MuninnStore:
    """Muninn tarihsel bellek deposu."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(vault_path(), "muninn")
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_file = os.path.join(self.base_dir, "entities_index.json")
        self.log_file = os.path.join(self.base_dir, "observations.jsonl")
        self.histories: Dict[str, EntityHistory] = {}
        self._load()

    def _load(self):
        """Index dosyasından bilinen varlık geçmişlerini yükler."""
        if not os.path.exists(self.index_file):
            return
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            for eid, data in raw_data.items():
                eh = EntityHistory(entity_id=eid, entity_type=data.get("entity_type", "unknown"))
                eh.first_seen = data.get("first_seen", eh.first_seen)
                eh.last_seen = data.get("last_seen", eh.last_seen)
                eh.observation_count = data.get("observation_count", 0)
                eh.current_attributes = data.get("current_attributes", {})
                eh.tags = data.get("tags", [])
                for c in data.get("changes", []):
                    eh.changes.append(AttributeChange(
                        attribute=c.get("attribute", ""),
                        old_value=c.get("old_value"),
                        new_value=c.get("new_value"),
                        timestamp=c.get("timestamp", ""),
                        source_module=c.get("source_module", "")
                    ))
                # v1.3: snapshot'ları geri yükle (Semantic Drift için geçmiş metinler)
                for s in data.get("snapshots", []):
                    eh.snapshots.append(EntitySnapshot(
                        entity_id=eid,
                        entity_type=data.get("entity_type", "unknown"),
                        attributes=s.get("attributes", {}),
                        relations=s.get("relations", []),
                        confidence=s.get("confidence", 0.5),
                        timestamp=s.get("timestamp", ""),
                        source_module=s.get("source_module", "unknown"),
                    ))
                self.histories[eid] = eh
        except Exception:
            pass

    def save(self):
        """Index dosyasını disk üzerine kalıcı olarak kaydeder."""
        try:
            dump_data = {eid: h.to_dict() for eid, h in self.histories.items()}
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(dump_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_or_create(self, entity_id: str, entity_type: str = "unknown") -> EntityHistory:
        """Varlığa ait geçmiş kaydını döner veya yenisini oluşturur."""
        clean_id = entity_id.strip().lower()
        if clean_id not in self.histories:
            self.histories[clean_id] = EntityHistory(entity_id=entity_id, entity_type=entity_type)
        return self.histories[clean_id]

    def record_snapshot(self, entity_id: str, entity_type: str, attributes: Dict[str, Any],
                        relations: Optional[List[str]] = None, source_module: str = "unknown",
                        confidence: float = 0.5) -> List[AttributeChange]:
        """Yeni bir gözlemi kaydeder, değişimleri hesaplar ve log dosyasına ekler."""
        eh = self.get_or_create(entity_id, entity_type)
        changes = eh.record_observation(attributes, relations, source_module, confidence)
        self.save()

        # Append-only JSONL log
        try:
            log_entry = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "timestamp": eh.last_seen,
                "source_module": source_module,
                "attributes": attributes,
                "changes": [c.to_dict() for c in changes],
                "confidence": confidence,
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

        return changes

    def get_history(self, entity_id: str) -> Optional[EntityHistory]:
        """Belirtilen varlığın geçmişini getirir."""
        clean_id = entity_id.strip().lower()
        return self.histories.get(clean_id)

    def list_known_entities(self) -> List[str]:
        """Muninn tarafından hatırlanan tüm varlıkların kimliklerini listeler."""
        return list(self.histories.keys())
