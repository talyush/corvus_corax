"""Corvus Corax Evidence Engine Data Models.
"""
import hashlib
import uuid
from datetime import datetime, timezone


class Observation:
    """Modüllerden gelen ham gözlem kaydı (Raw Observation)."""

    _sequence_counter = 0

    def __init__(self, target, source_module, payload, timestamp=None):
        Observation._sequence_counter += 1
        self.obs_num = Observation._sequence_counter
        self.obs_id = f"observation #{self.obs_num}"
        self.guid = f"obs-{uuid.uuid4().hex[:8]}"
        self.target = target
        self.source_module = source_module
        self.payload = payload or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.raw_hash = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()[:16]

    def to_dict(self):
        return {
            "obs_id": self.obs_id,
            "guid": self.guid,
            "target": self.target,
            "source_module": self.source_module,
            "timestamp": self.timestamp,
            "raw_hash": self.raw_hash,
            "payload": self.payload,
        }


class Evidence:
    """Atomik İşlenmiş Kanıt Kaydı."""

    def __init__(self, evidence_type, observed_value, target, source_module, admiralty_code="B2",
                 confidence=0.8, status="VALIDATED", raw_observation_id=None, parent_ids=None):
        self.id = f"ev-{uuid.uuid4().hex[:8]}"
        self.evidence_type = evidence_type
        self.observed_value = observed_value
        self.target = target
        self.source_module = source_module
        self.admiralty_code = admiralty_code
        self.confidence = float(confidence)
        self.status = status  # VALIDATED, UNVERIFIABLE, MALFORMED, EXPIRED, CONFLICT
        self.raw_observation_id = raw_observation_id
        self.parent_ids = parent_ids or []
        self.children_ids = []
        self.corroborating_sources = {source_module}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.evidence_type,
            "value": self.observed_value,
            "target": self.target,
            "source": self.source_module,
            "admiralty_code": self.admiralty_code,
            "confidence": self.confidence,
            "status": self.status,
            "raw_observation_id": self.raw_observation_id,
            "parent_ids": self.parent_ids,
            "children_ids": self.children_ids,
            "corroboration_count": len(self.corroborating_sources),
            "sources": list(self.corroborating_sources),
            "timestamp": self.timestamp,
        }


class KeyFinding:
    """Yapılandırılmış Ana Bulgular Kartı (Structured Key Finding Card)."""

    def __init__(self, relationship_str, status="CANDIDATE", confidence=0.75,
                 supporting_sources=None, corroboration_count=1, observation_ids=None):
        self.relationship_str = relationship_str
        self.status = status  # CANDIDATE, VERIFIED, DERIVED, CONFLICT
        self.confidence = float(confidence)
        self.supporting_sources = supporting_sources or []
        self.corroboration_count = corroboration_count
        self.observation_ids = observation_ids or []

    def to_dict(self):
        return {
            "relationship": self.relationship_str,
            "status": self.status,
            "confidence": self.confidence,
            "supporting_sources": self.supporting_sources,
            "corroboration_count": self.corroboration_count,
            "derived_from_observations": self.observation_ids,
        }


class IntelligenceGaps:
    """WHAT CORVUS DOES NOT KNOW — İstihbarat Boşlukları Raporu."""

    def __init__(self, target):
        self.target = target
        self.gaps = []
        self.unverified_identities = []
        self.single_source_dependencies = []
        self.unresolved_hypotheses = []

    def add_gap(self, statement):
        if statement and statement not in self.gaps:
            self.gaps.append(statement)

    def to_dict(self):
        return {
            "target": self.target,
            "gaps": self.gaps,
            "unverified_identities": self.unverified_identities,
            "single_source_dependencies": self.single_source_dependencies,
            "unresolved_hypotheses": self.unresolved_hypotheses,
        }
