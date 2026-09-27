"""Corvus Perception — Data Models (v1.4).

Sözleşme: dış dünyadan gelen her kaynak (SourceAdapter) bu sözleşmeyle
kendini beyan eder, algı çağrısı yapılır, sonuç standartlaştırılır ve
provenance ile damgalanır. Daha sonra ELIGIBILITY GATE'ten geçer.

Bu modül YENİ EVIDENCE MODELİ DEĞİLDİR — mevcut core/evidence/model.py
üzerine kurulur. Sadece algı katmanının sözleşme tiplerini taşır.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.evidence.model import Evidence, Observation  # mevcut model (YENİ değil)


# ---------------------------------------------------------------------
# Kaynak Beyanı
# ---------------------------------------------------------------------

@dataclass
class SourceDeclaration:
    """Bir algı kanalının (kaynağın) dış dünyaya açılan kimliği."""
    source_id: str                 # "whois", "social", "github"...
    kind: str                      # "http", "dns", "registry", "api", "whois_socket"...
    auth_level: str                # "public" | "authorized" | "local"
    base_url: Optional[str] = None
    requires_key: bool = False
    rate_limit: float = 1.0        # saniye başına istek sınırı

    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "auth_level": self.auth_level,
            "base_url": self.base_url,
            "requires_key": self.requires_key,
            "rate_limit": self.rate_limit,
        }


# ---------------------------------------------------------------------
# Algı Çağrısı Sonucu
# ---------------------------------------------------------------------

@dataclass
class PerceptionResult:
    """Bir perceive() çağrısının standart sonucu.

    normalized: dünya modeline ADAY olan kanonik form.
    provenance: kaynağın köken zımbası.
    eligibility: bu çağrının context yazma kararı bilgisi.
    evidence: mevcut Evidence Engine'in ürettiği kanıt nesneleri (YENİ model değil).
    """
    ok: bool
    source: SourceDeclaration
    target: str
    target_type: str
    raw: Any
    normalized: Dict
    provenance: Dict
    eligibility: Dict = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    observation: Optional[Observation] = None
    error: Optional[str] = None
    written: List[Dict] = field(default_factory=list)   # context'e yazılanların izi
    rejected: List[Dict] = field(default_factory=list)  # eligibility'ce reddedilenler


# ---------------------------------------------------------------------
# World model alınabilirlik (ELIGIBILITY)
# ---------------------------------------------------------------------

@dataclass
class EligibilityState:
    eligible: bool
    gate: str            # "evidence" | "validation" | "provenance" | "seed"
    reason: str
    detail: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "eligible": self.eligible,
            "gate": self.gate,
            "reason": self.reason,
            "detail": self.detail,
        }


# ---------------------------------------------------------------------
# Provenance / hash yardımcıları — core/evidence/model.py:22 ile birebir
# ---------------------------------------------------------------------

def raw_hash_str(payload: Any) -> str:
    """Observation.raw_hash ile AYNI: sha256(str(payload))[:16].

    core/evidence/model.py:22 -> hashlib.sha256(str(payload).encode("utf-8")).hexdigest()[:16]
    """
    return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()[:16]


def stamp_provenance(source: SourceDeclaration, target: str, raw: Any,
                     method: Optional[str] = None) -> Dict:
    """Kaynak kaydına köken zımbası basar — tüm algı çağrıları buradan geçer."""
    return {
        "source": source.source_id,
        "source_url": source.base_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "method": method or f"{source.kind}_query",
        "auth": source.auth_level,
        "raw_hash": raw_hash_str(raw),
    }
