"""Corvus Corax v1.2 - Huginn Reasoning Trace Model.

"Huginn thinks."
Structured reasoning trace:
Observation -> Interpretation -> Hypothesis -> Decision
Provides explainable, provenance-backed justification for any conclusion without raw chain-of-thought dump.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class StepType(Enum):
    OBSERVATION = "OBSERVATION"        # Toplanan ham veri veya kanıt
    INTERPRETATION = "INTERPRETATION"  # Verinin ne anlama geldiğinin analizi
    HYPOTHESIS = "HYPOTHESIS"          # Oluşturulan veya test edilen senaryo
    DECISION = "DECISION"              # Varılan nihai istihbarat kararı veya aksiyon


@dataclass
class ReasoningStep:
    """Akıl yürütme zincirindeki tek bir adım."""
    step_type: StepType
    title: str
    description: str
    evidence_ids: List[str] = field(default_factory=list)
    confidence: float = 0.5
    source_module: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_type": self.step_type.value,
            "title": self.title,
            "description": self.description,
            "evidence_ids": self.evidence_ids,
            "confidence": self.confidence,
            "source_module": self.source_module,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class ReasoningTraceModel:
    """Bir hedef veya sorgu için üretilen tam akıl yürütme izi (Reasoning Trace)."""

    def __init__(self, target: str, objective: str = "Analysis"):
        self.target = target
        self.objective = objective
        self.steps: List[ReasoningStep] = []
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self.final_decision: Optional[str] = None
        self.final_confidence: float = 0.5

    def add_observation(self, title: str, description: str, evidence_ids: Optional[List[str]] = None,
                        source_module: str = "unknown", confidence: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> ReasoningStep:
        step = ReasoningStep(
            step_type=StepType.OBSERVATION,
            title=title,
            description=description,
            evidence_ids=evidence_ids or [],
            confidence=confidence,
            source_module=source_module,
            metadata=metadata or {}
        )
        self.steps.append(step)
        return step

    def add_interpretation(self, title: str, description: str, based_on_evidence: Optional[List[str]] = None,
                           confidence: float = 0.5, metadata: Optional[Dict[str, Any]] = None) -> ReasoningStep:
        step = ReasoningStep(
            step_type=StepType.INTERPRETATION,
            title=title,
            description=description,
            evidence_ids=based_on_evidence or [],
            confidence=confidence,
            source_module="huginn_analyst",
            metadata=metadata or {}
        )
        self.steps.append(step)
        return step

    def add_hypothesis(self, title: str, description: str, prior: float = 0.4,
                       posterior: float = 0.5, status: str = "ACTIVE", metadata: Optional[Dict[str, Any]] = None) -> ReasoningStep:
        meta = metadata or {}
        meta.update({"prior": prior, "posterior": posterior, "status": status})
        step = ReasoningStep(
            step_type=StepType.HYPOTHESIS,
            title=title,
            description=description,
            confidence=posterior,
            source_module="bayesian_nexus",
            metadata=meta
        )
        self.steps.append(step)
        return step

    def add_decision(self, title: str, description: str, confidence: float = 0.5,
                     next_action: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ReasoningStep:
        meta = metadata or {}
        if next_action:
            meta["next_action"] = next_action
        step = ReasoningStep(
            step_type=StepType.DECISION,
            title=title,
            description=description,
            confidence=confidence,
            source_module="corvus_core",
            metadata=meta
        )
        self.steps.append(step)
        self.final_decision = description
        self.final_confidence = confidence
        self.completed_at = datetime.now(timezone.utc).isoformat()
        return step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "objective": self.objective,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "final_decision": self.final_decision,
            "final_confidence": self.final_confidence,
            "steps": [s.to_dict() for s in self.steps],
        }
