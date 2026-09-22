"""Corvus Corax v1.2 - Muninn Deep Recall Engine.

Aggregates historical data across:
- MuninnStore (Entity snapshots, timestamps, attribute changes/drift)
- ContextManager (Active RAM graph & relations)
- KnowledgeStore (Architect lessons & persistent knowledge)
- Evidence Engine (Historical verified evidence records)
"""
from typing import Dict, Any, Optional, List
from .store import MuninnStore
from .history import EntityHistory, AttributeChange


class MuninnRecallEngine:
    """Muninn Birleşik Hatırlama ve Tarihçe Motoru."""

    def __init__(self, store: Optional[MuninnStore] = None, context_manager=None, knowledge_store=None):
        self.store = store or MuninnStore()
        self.context = context_manager
        self.knowledge = knowledge_store

    def recall_entity(self, entity_id: str) -> Dict[str, Any]:
        """Bir varlık hakkında hatırlanan tüm tarihsel ve güncel bilgileri birleştirir."""
        eh = self.store.get_history(entity_id)
        
        # Muninn store kaydı
        history_data = eh.to_dict() if eh else {
            "entity_id": entity_id,
            "entity_type": "unknown",
            "first_seen": "never",
            "last_seen": "never",
            "observation_count": 0,
            "current_attributes": {},
            "changes": [],
            "snapshots_count": 0,
        }

        # KnowledgeStore'dan ilgili dersler ve notlar
        knowledge_matches = []
        if self.knowledge and hasattr(self.knowledge, "search"):
            knowledge_matches = self.knowledge.search(entity_id)

        # ContextManager'daki aktif ilişkiler
        active_relations = []
        if self.context and hasattr(self.context, "get_entity_relations"):
            try:
                active_relations = self.context.get_entity_relations(entity_id)
            except Exception:
                pass

        return {
            "entity_id": entity_id,
            "found_in_history": eh is not None,
            "first_seen": history_data["first_seen"],
            "last_seen": history_data["last_seen"],
            "observation_count": history_data["observation_count"],
            "attributes": history_data["current_attributes"],
            "changes": history_data["changes"],
            "recent_snapshots_count": history_data["snapshots_count"],
            "knowledge_notes": knowledge_matches,
            "active_relations": active_relations,
        }

    def detect_attribute_drift(self, entity_id: str) -> List[Dict[str, Any]]:
        """Zaman içindeki öznitelik değişimlerini (drift) listeler."""
        eh = self.store.get_history(entity_id)
        if not eh:
            return []
        return [c.to_dict() for c in eh.changes]

    def format_history_report(self, entity_id: str, lang: str = "tr") -> str:
        """Kullanıcıya veya LLM'e sunulacak insan tarafından okunabilir tarihçe raporu üretir."""
        data = self.recall_entity(entity_id)
        
        if not data["found_in_history"]:
            if lang == "tr":
                return f"[Muninn] '{entity_id}' varlığına ait geçmiş bir gözlem kaydı bulunamadı."
            return f"[Muninn] No historical observations found for entity '{entity_id}'."

        first = data['first_seen'][:19].replace("T", " ") if data['first_seen'] != "never" else "Bilinmiyor"
        last = data['last_seen'][:19].replace("T", " ") if data['last_seen'] != "never" else "Bilinmiyor"
        obs_count = data['observation_count']
        changes = data['changes']

        if lang == "tr":
            lines = [
                f"============================================================",
                f"  MUNINN HAFIZA KAYDI: '{entity_id}'",
                f"============================================================",
                f"  * Ilk Gorulme : {first}",
                f"  * Son Gorulme : {last}",
                f"  * Toplam Gozlem: {obs_count}",
            ]
            if data["attributes"]:
                lines.append(f"  * Bilinen Oznitelikler:")
                for k, v in data["attributes"].items():
                    lines.append(f"      - {k}: {v}")
            
            if changes:
                lines.append(f"  * Tespit Edilen Degisimler (Drift - {len(changes)} adet):")
                for c in changes:
                    t = c['timestamp'][:19].replace("T", " ")
                    lines.append(f"      [{t}] {c['attribute']}: '{c['old_value']}' -> '{c['new_value']}' (Modul: {c['source_module']})")
            else:
                lines.append(f"  * Oznitelik degisimi gozlemlenmedi (Stabil durum).")
            
            if data["knowledge_notes"]:
                lines.append(f"  * Mimar/Bilgi Notlari ({len(data['knowledge_notes'])} adet):")
                for note in data["knowledge_notes"][:3]:
                    lines.append(f"      - {note.get('fact', str(note))}")

            lines.append("============================================================")
            return "\n".join(lines)
        else:
            lines = [
                f"============================================================",
                f"  MUNINN MEMORY RECORD: '{entity_id}'",
                f"============================================================",
                f"  * First Seen   : {first}",
                f"  * Last Seen    : {last}",
                f"  * Observations : {obs_count}",
            ]
            if data["attributes"]:
                lines.append(f"  * Known Attributes:")
                for k, v in data["attributes"].items():
                    lines.append(f"      - {k}: {v}")
            
            if changes:
                lines.append(f"  * Detected Changes (Drift - {len(changes)} events):")
                for c in changes:
                    t = c['timestamp'][:19].replace("T", " ")
                    lines.append(f"      [{t}] {c['attribute']}: '{c['old_value']}' -> '{c['new_value']}' (Source: {c['source_module']})")
            else:
                lines.append(f"  * No attribute drift detected (Stable state).")

            if data["knowledge_notes"]:
                lines.append(f"  * Knowledge Notes ({len(data['knowledge_notes'])} items):")
                for note in data["knowledge_notes"][:3]:
                    lines.append(f"      - {note.get('fact', str(note))}")

            lines.append("============================================================")
            return "\n".join(lines)
