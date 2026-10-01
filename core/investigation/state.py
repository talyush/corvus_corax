"""Corvus Corax v1.4 — Investigation State.

Bir araştırmanın canlı belgesı: hedef çözümleme (Target Resolution), hipotezler,
boşluklar, çalışılmış adımlar, karar izi (decision trace), durma koşulları.

v1.4 kuralı: Investigation State'ın TEK yazarı InvestigationEngine'dir.
Agent bu state'i MUTASYON yapamaz — yalnızca engine'in kararını uygular ve
sonucu Engine'e geri verir.

DİKKAT: Bu, mevcut ContextManager/strategy.py'nin yerini ALMAZ; araştırmaya
ÖZGÜ geçici durum belgesidir (session boyunca yaşar, rapora gömülür).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TargetCandidate:
    """Hedef çözümlemede bir aday.

    support_score: kimlik olasılığı DEĞİL; candidate'ı destekleyen kanıt/rank
    puanıdır (Similarity != Identity prensibi).
    """
    entity: str                # "person:Ahmet Yılmaz"
    support_score: float = 0.0
    ambiguity: str = "high"    # low | medium | high
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class TargetResolution:
    """Hedef çözümleme (v1.4 rule-based)."""
    candidates: List[TargetCandidate] = field(default_factory=list)
    primary: Optional[str] = None          # AMBIGUOUS/UNRESOLVED ise None
    status: str = "UNRESOLVED"             # RESOLVED | AMBIGUOUS | UNRESOLVED

    def to_dict(self) -> Dict:
        return {
            "candidates": [
                {"entity": c.entity, "support_score": c.support_score,
                 "ambiguity": c.ambiguity, "evidence_refs": c.evidence_refs}
                for c in self.candidates
            ],
            "primary": self.primary,
            "status": self.status,
        }


@dataclass
class ExecutedStep:
    """Çalıştırılmış adım kaydı."""
    tool: str
    target: str
    decision_ref: str = ""
    status: str = "skipped"                # success | error | denied | skipped
    observation_ref: str = ""


@dataclass
class DecisionTrace:
    """Döngünün gerekçe zinciri — rapor neden böyle oluştu sorusunun cevabı."""
    id: str
    next_step: str
    why: str = ""
    time: str = ""


@dataclass
class StopConditions:
    """Investigation Engine'in durma koşulları (kontrat 3.1)."""
    max_steps: int = 8
    confidence_threshold: float = 0.85
    coverage_required: List[str] = field(default_factory=list)   # "identity", "digital_footprint"
    max_network_calls: int = 6
    max_local_calls: int = 4
    max_pivots: int = 4


@dataclass
class InvestigationState:
    """Araştırma durumu — yalnızca Engine bu nesneyi değiştirebilir."""

    # ---- Request / genel ----
    request: Dict = field(default_factory=dict)        # {intent, referent, constraints}
    status: str = "CREATED"                             # CREATED|PLANNING|IN_PROGRESS|NEEDS_INPUT
                                                        # |AWAITING_EXTERNAL|FINALIZED|ARCHIVED
    # ---- Hedef çözümleme ----
    resolution: TargetResolution = field(default_factory=TargetResolution)

    # ---- Araştırma durumu ----
    hypotheses: List[Dict] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    steps: List[ExecutedStep] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    decisions: List[DecisionTrace] = field(default_factory=list)
    stop_conditions: StopConditions = field(default_factory=StopConditions)

    # ---- Döngü yürütme durumu ----
    iterations: int = 0
    net_used: int = 0
    local_used: int = 0
    pivots_used: int = 0
    seen: set = field(default_factory=set)              # (tool, target) tekrar koruması

    # ---- Kayıt dışı (rapor için) ----
    pivot_path: List[Dict] = field(default_factory=list)
    reflection_notes: List[str] = field(default_factory=list)

    # ---- Sonuç ----
    finalized_report: Optional[Dict] = None

    # ==================================================================
    # Yardımcılar (yalnızca Engine çağırır)
    # ==================================================================
    def add_decision(self, next_step: str, why: str = "", time: str = "") -> str:
        dec_id = f"dec-{len(self.decisions) + 1:04d}"
        self.decisions.append(DecisionTrace(id=dec_id, next_step=next_step, why=why, time=time))
        return dec_id

    def to_dict(self) -> Dict:
        return {
            "request": self.request,
            "status": self.status,
            "resolution": self.resolution.to_dict(),
            "hypotheses": self.hypotheses,
            "gaps": self.gaps,
            "steps": [
                {"tool": s.tool, "target": s.target, "decision_ref": s.decision_ref,
                 "status": s.status, "observation_ref": s.observation_ref}
                for s in self.steps
            ],
            "next_steps": self.next_steps,
            "stop_conditions": {
                "max_steps": self.stop_conditions.max_steps,
                "confidence_threshold": self.stop_conditions.confidence_threshold,
                "max_network_calls": self.stop_conditions.max_network_calls,
                "max_local_calls": self.stop_conditions.max_local_calls,
                "max_pivots": self.stop_conditions.max_pivots,
            },
            "iterations": self.iterations,
            "decisions": [d.__dict__ for d in self.decisions],
            "pivot_path": self.pivot_path,
        }