"""Corvus Corax v1.4 — Perception Subsystem.

Dış dünyadan (public/authorized kaynaklardan) veri toplar, normalize eder,
provenance zımbasını basar ve mevcut Evidence Engine'e aktarır. World model'e
(ContextManager) yazım yalnızca PerceptionPipeline üzerinden, eligibility
gate'ini geçen veriyle yapılır.

Konsolidasyon: YENİ Evidence/Memory/Graph sistemi KURULMAZ — mevcut
core/evidence/*, core/context.py üzerine bindirilir.
"""

from core.perception.model import (
    SourceDeclaration,
    PerceptionResult,
    EligibilityState,
    raw_hash_str,
    stamp_provenance,
)
from core.perception.adapter import SourceAdapter, ModuleSourceAdapter, _NoWriteContext
from core.perception.pipeline import PerceptionPipeline

__all__ = [
    "SourceDeclaration",
    "PerceptionResult",
    "EligibilityState",
    "raw_hash_str",
    "stamp_provenance",
    "SourceAdapter",
    "ModuleSourceAdapter",
    "_NoWriteContext",
    "PerceptionPipeline",
]