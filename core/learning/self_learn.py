"""Corvus Self-Learning — Failure Learner.

Bir aracın HATASI olduğunda; desenleri ve istatistikleri kullanarak
alternatif pivot araçları üretir ve kullanıcıya/planner'a önerir.

Bu, kullanıcının "instagram gizli ise ne yapabilirim" senaryosudur:
  social (privacy_wall) -> github? academic? diğer platformlar?

TAM OTONOM modda; öğrenilen alternatifler, ExperienceStore'a
alternatives olarak yazılır ve bir sonraki planda önerilir.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from .experience import ExperienceStore
from .patterns import PatternLearning


class FailureLearner:
    """Başarısızlıktan öğrenme ve pivot önerisi."""

    # Arac -> göreve göre alternatifler (ilkel bilgi temeli)
    KNOWLEDGE_BASE: Dict[str, List[str]] = {
        "social": ["github", "academic", "org", "pivot", "discover"],
        "whois": ["dns", "cert", "metadata", "tech", "footprint"],
        "dns": ["whois", "cert", "tech", "resolve", "subdomain"],
        "geoip": ["asn", "netscan", "resolve"],
        "crawl": ["wayback", "headers", "metadata"],
        "breach": ["email", "org", "social"],
        "github": ["social", "academic", "email"],
        "org": ["whois", "cert", "social"],
        "scan": ["netscan", "geoip"],
    }

    def __init__(self, store: ExperienceStore, patterns: Optional[PatternLearning] = None):
        self.store = store
        self.patterns = patterns or PatternLearning(store)

    # ------------------------------------------------------------------
    def suggest_alternatives(self, failed_tool: str, target_type: str = "",
                             context_keywords: Optional[List[str]] = None) -> List[str]:
        """Bir arac başarısız olduğunda önerilecek pivot araçlar."""
        suggestions = []
        seen = set()

        # 1. Öğrenilmiş desenlerden (deneyim)
        learned = self.patterns.alternatives_for(failed_tool, target_type)
        for alt in learned:
            if alt not in seen:
                suggestions.append(alt)
                seen.add(alt)

        # 2. Bilgi tabanından (ilkel domain bilgisi)
        for alt in self.KNOWLEDGE_BASE.get(failed_tool, []):
            if alt not in seen:
                suggestions.append(alt)
                seen.add(alt)

        return suggestions[:4]

    # ------------------------------------------------------------------
    def learn_from_failure(self, tool: str, target_type: str = "unknown",
                           error_type: str = "", summary: str = "",
                           context_keywords: Optional[List[str]] = None) -> Dict:
        """
        Bir başarısızlık anında çağrılır:
          1. Deneyim olarak kaydet
          2. Desen çıkarımını yenile
          3. Alternatif öner (öğrenme sonucu)
        """
        alts = self.suggest_alternatives(tool, target_type, context_keywords)

        exp = self.store.record(
            tool=tool, target_type=target_type,
            status="error", error_type=error_type,
            summary=summary, context_keywords=context_keywords or [],
            alternatives=alts,
        )

        learned = self.patterns.learn_from_recent()

        return {
            "failed_tool": tool,
            "error_type": error_type,
            "alternatives_suggested": alts,
            "pattern_count": len([p for p in learned if p.tool == tool]),
        }

    def learn_from_success(self, tool: str, target_type: str = "unknown",
                           new_entities: int = 0, summary: str = "") -> Dict:
        """Başarıyı da öğrenir (kalibrasyon için veri)."""
        exp = self.store.record(
            tool=tool, target_type=target_type, status="success",
            summary=summary, new_entities=new_entities,
        )
        return {"tool": tool, "new_entities": new_entities}