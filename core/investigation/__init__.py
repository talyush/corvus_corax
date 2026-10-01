"""Corvus Corax v1.4 — Investigation Engine.

Araştırmanın canlı durumu (InvestigationState) ve karar motoru (InvestigationEngine).

v1.4 prensibi:
  - Investigation Engine  = state'in TEK yazarı (hedef çözümleme, hipotezler,
                            next-step, stop, rapor).
  - Agent                 = yalnızca icra (Engine kararı -> SafetyPolicy ->
                            ActionGuard -> Tool -> ToolResult).
  - Bu paket mevcut ContextManager / strategy.py / evidence sistemlerinin
    yerini ALMAZ; onların üstüne binen araştırmaya özel katmandır.
"""

from core.investigation.state import (
    InvestigationState,
    TargetResolution,
    TargetCandidate,
    ExecutedStep,
    StopConditions,
)
from core.investigation.engine import InvestigationEngine

__all__ = [
    "InvestigationState",
    "TargetResolution",
    "TargetCandidate",
    "ExecutedStep",
    "StopConditions",
    "InvestigationEngine",
]