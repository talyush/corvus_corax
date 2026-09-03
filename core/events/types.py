"""Corvus Corax Typed Events and Metadata Models.
"""
import uuid
from datetime import datetime, timezone


class EventMetadata:
    """Olay Meta Verileri (Metadata)."""

    def __init__(self, source_module="system", correlation_id=None):
        self.event_id = f"evt-{uuid.uuid4().hex[:10]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.source_module = source_module
        self.correlation_id = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
            "correlation_id": self.correlation_id,
        }


class TypedEvent:
    """Temel Olay Sınıfı (Base Typed Event)."""

    def __init__(self, event_type, payload=None, metadata=None):
        self.event_type = event_type
        self.payload = payload or {}
        self.metadata = metadata or EventMetadata()

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "metadata": self.metadata.to_dict(),
            "payload": self.payload,
        }


class EntityDiscoveredEvent(TypedEvent):
    def __init__(self, entity_type, entity_value, provenance=None, metadata=None):
        payload = {"entity_type": entity_type, "entity_value": entity_value, "provenance": provenance or {}}
        super().__init__("EntityDiscovered", payload, metadata)


class RelationshipCreatedEvent(TypedEvent):
    def __init__(self, src_value, dst_value, relation_type, confidence=0.8, evidence_ids=None, metadata=None):
        payload = {
            "src": src_value,
            "dst": dst_value,
            "relation": relation_type,
            "confidence": confidence,
            "evidence_ids": evidence_ids or [],
        }
        super().__init__("RelationshipCreated", payload, metadata)


class EvidenceCorroboratedEvent(TypedEvent):
    def __init__(self, evidence_id, corroborating_sources, new_confidence=0.9, metadata=None):
        payload = {
            "evidence_id": evidence_id,
            "corroborating_sources": list(corroborating_sources),
            "new_confidence": new_confidence,
        }
        super().__init__("EvidenceCorroborated", payload, metadata)


class ConflictDetectedEvent(TypedEvent):
    def __init__(self, target, competing_values, resolution=None, metadata=None):
        payload = {
            "target": target,
            "competing_values": competing_values,
            "resolution": resolution,
        }
        super().__init__("ConflictDetected", payload, metadata)


class AssetBoundEvent(TypedEvent):
    def __init__(self, owner_entity, asset_type, asset_value, metadata=None):
        payload = {
            "owner": owner_entity,
            "asset_type": asset_type,
            "asset_value": asset_value,
        }
        super().__init__("AssetBound", payload, metadata)


# --- v1.1 INFERENCE ENGINE EVENTS ---

class HypothesisGeneratedEvent(TypedEvent):
    def __init__(self, hypothesis_id, claim, hypothesis_type, prior, metadata=None):
        payload = {
            "hypothesis_id": hypothesis_id,
            "claim": claim,
            "type": hypothesis_type,
            "prior": prior,
        }
        super().__init__("HypothesisGenerated", payload, metadata)


class HypothesisConfirmedEvent(TypedEvent):
    def __init__(self, hypothesis_id, claim, posterior, metadata=None):
        payload = {
            "hypothesis_id": hypothesis_id,
            "claim": claim,
            "posterior": posterior,
        }
        super().__init__("HypothesisConfirmed", payload, metadata)


class HypothesisRefutedEvent(TypedEvent):
    def __init__(self, hypothesis_id, claim, posterior, metadata=None):
        payload = {
            "hypothesis_id": hypothesis_id,
            "claim": claim,
            "posterior": posterior,
        }
        super().__init__("HypothesisRefuted", payload, metadata)


class BridgeHypothesisGeneratedEvent(TypedEvent):
    def __init__(self, src_entity, dst_entity, bridge_type, prior, intermediate_node=None, metadata=None):
        payload = {
            "src": src_entity,
            "dst": dst_entity,
            "bridge_type": bridge_type,
            "prior": prior,
            "intermediate": intermediate_node,
        }
        super().__init__("BridgeHypothesisGenerated", payload, metadata)


class BayesianUpdateAppliedEvent(TypedEvent):
    def __init__(self, hypothesis_id, evidence_id, prior_before, posterior_after, delta, metadata=None):
        payload = {
            "hypothesis_id": hypothesis_id,
            "evidence_id": evidence_id,
            "prior_before": prior_before,
            "posterior_after": posterior_after,
            "delta": delta,
        }
        super().__init__("BayesianUpdateApplied", payload, metadata)

