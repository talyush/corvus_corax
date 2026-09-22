"""Corvus Corax v1.2 - Huginn Provenance & Lineage Tracker.

Maintains strict provenance for every inference:
- Source module & raw timestamp
- NATO Admiralty Reliability rating (A-F, 1-6)
- Dependency chain of deductions
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProvenanceRecord:
    """Tek bir çıkarım veya gözlemin köken kaydı."""
    item_id: str
    item_type: str  # evidence, hypothesis, deduction, decision
    source_module: str
    admiralty_code: str = "B2"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dependencies: List[str] = field(default_factory=list)
    raw_payload_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "source_module": self.source_module,
            "admiralty_code": self.admiralty_code,
            "timestamp": self.timestamp,
            "dependencies": self.dependencies,
            "raw_payload_hash": self.raw_payload_hash,
        }


class ProvenanceTracker:
    """Köken ve izlenebilirlik takipçisi."""

    def __init__(self):
        self.records: Dict[str, ProvenanceRecord] = {}

    def register(self, item_id: str, item_type: str, source_module: str,
                 admiralty_code: str = "B2", dependencies: Optional[List[str]] = None) -> ProvenanceRecord:
        rec = ProvenanceRecord(
            item_id=item_id,
            item_type=item_type,
            source_module=source_module,
            admiralty_code=admiralty_code,
            dependencies=dependencies or []
        )
        self.records[item_id] = rec
        return rec

    def get_lineage(self, item_id: str) -> List[ProvenanceRecord]:
        """Bir öğenin bağlı olduğu tüm öncül köken kayıtlarını döner."""
        result = []
        visited = set()
        queue = [item_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            rec = self.records.get(curr)
            if rec:
                result.append(rec)
                queue.extend(rec.dependencies)

        return result
