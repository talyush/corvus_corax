"""Corvus Corax v1.2 - Muninn Memory Core.

"Muninn remembers."
Tracks historical observations, entity lifecycle, attribute drift (what changed over time),
and integrates with Vault, Evidence Engine, and Nexus for unified deep recall.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os


@dataclass
class AttributeChange:
    """Tek bir öznitelik veya özellik değişimi kaydı (drift)."""
    attribute: str
    old_value: Any
    new_value: Any
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_module: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
        }


@dataclass
class EntitySnapshot:
    """Varlığın belirli bir zamandaki anlık durumu (state snapshot)."""
    entity_id: str
    entity_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_module: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "attributes": self.attributes,
            "relations": self.relations,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
        }


class EntityHistory:
    """Bir varlığın tüm tarihsel kayıtlarını ve değişim çizelgesini yönetir."""

    def __init__(self, entity_id: str, entity_type: str):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.first_seen: str = datetime.now(timezone.utc).isoformat()
        self.last_seen: str = self.first_seen
        self.observation_count: int = 0
        self.snapshots: List[EntitySnapshot] = []
        self.changes: List[AttributeChange] = []
        self.current_attributes: Dict[str, Any] = {}
        self.tags: List[str] = []

    def record_observation(self, attributes: Dict[str, Any], relations: Optional[List[str]] = None,
                           source_module: str = "unknown", confidence: float = 0.5) -> List[AttributeChange]:
        """Yeni bir gözlem kaydeder ve önceki duruma göre değişimleri (drift) hesaplar."""
        now = datetime.now(timezone.utc).isoformat()
        self.last_seen = now
        self.observation_count += 1
        relations = relations or []

        detected_changes: List[AttributeChange] = []

        # İlk gözlem değilse değişimleri tespit et
        if self.current_attributes:
            for k, new_v in attributes.items():
                if k in self.current_attributes:
                    old_v = self.current_attributes[k]
                    if old_v != new_v:
                        change = AttributeChange(
                            attribute=k,
                            old_value=old_v,
                            new_value=new_v,
                            timestamp=now,
                            source_module=source_module
                        )
                        detected_changes.append(change)
                        self.changes.append(change)
                else:
                    # Yeni eklenen öznitelik
                    change = AttributeChange(
                        attribute=k,
                        old_value=None,
                        new_value=new_v,
                        timestamp=now,
                        source_module=source_module
                    )
                    detected_changes.append(change)
                    self.changes.append(change)

        # Mevcut öznitelikleri güncelle
        self.current_attributes.update(attributes)

        # Snapshot oluştur ve sakla
        snapshot = EntitySnapshot(
            entity_id=self.entity_id,
            entity_type=self.entity_type,
            attributes=dict(self.current_attributes),
            relations=list(set(relations)),
            confidence=confidence,
            timestamp=now,
            source_module=source_module
        )
        self.snapshots.append(snapshot)
        return detected_changes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "observation_count": self.observation_count,
            "current_attributes": self.current_attributes,
            "tags": self.tags,
            "changes": [c.to_dict() for c in self.changes],
            "snapshots_count": len(self.snapshots),
        }
