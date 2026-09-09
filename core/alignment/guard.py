"""Corvus Alignment — ActionGuard (Capability Sınırı).

Bilgi ile EYLEM arasındaki köprüyü kontrol eder. Corvus bu koruma
olmadan öğrenmeye devam eder (KnowledgeStore serbest), ancak öğrenilen
bir bilginin capability'ye dönüşmesi Guard'dan geçmek zorundadır.

Guard iki kapıda çalışır:
  1. INPUT GUARD  — gelen isteğin kısıtlı capability talep edip etmediğini yakalar
  2. OUTPUT GUARD — üretilen çıktının (LLM dahil) kısıtlı içerik taşıyıp taşımadığını
                    gözden geçirir (opsiyonel LLM'den gelebilecek içerik için)

Bilinçli yanıt felsefesi:
  - Corvus "bilmiyorum" demez; "biliyorum ama capability olarak sunmuyorum" der.
  - Eğitim/savunma tarafı (education_allow=True) her zaman serbest kalır.
  - Dual-feedback: engellenen her istek, KnowledgeStore'a "öğrenme konusu" olarak
    geri bildirilir — zeka gelişir, eylem kısıtlı kalır.

Kayıt: vault/guard_log.jsonl
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .categories import CategoryRegistry, CapabilityCategory


class GuardVerdict:
    """Bir isteğin/çıktının guard kararı."""

    def __init__(self, allowed: bool, categories: List[CapabilityCategory],
                 reason: str = "", suggestions: Optional[List[str]] = None):
        self.allowed = allowed
        self.categories = categories
        self.reason = reason
        self.suggestions = suggestions or []

    @property
    def labels(self) -> List[str]:
        return [c.label for c in self.categories]

    @property
    def blocked_ids(self) -> List[str]:
        return [c.id for c in self.categories]

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked_ids,
            "reason": self.reason,
            "suggestions": self.suggestions,
        }


class ActionGuard:
    """Capability sınırlama katmanı."""

    REFUSAL_TEMPLATE_TR = (
        "Bu konuda derinleşebilirim — konunun kavramsal mimarisini biliyorum. "
        "Fakat bunu capability olarak kullanmamak için kodlandım. "
        "{suggestion}"
    )
    REFUSAL_TEMPLATE_EN = (
        "I can deepen into this — I know the conceptual architecture of the topic. "
        "But I am coded not to offer it as a capability. "
        "{suggestion}"
    )
    DEFAULT_SUGGESTION_TR = "Savunma/tespit tarafını (nasıl korunulur, nasıl fark edilir) anlatabilirim."
    DEFAULT_SUGGESTION_EN = "I can explain the defensive/detection side (how to protect, how to spot it)."

    def __init__(self, categories: Optional[List[CapabilityCategory]] = None,
                 knowledge: Optional["KnowledgeStore"] = None,
                 log_path: Optional[str] = None):
        self.registry = CategoryRegistry(categories)
        self.knowledge = knowledge
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_path = log_path or os.getenv("CORVUS_GUARD_LOG") or os.path.join(root, "vault", "guard_log.jsonl")

    # ------------------------------------------------------------------
    # Temel kontrol
    # ------------------------------------------------------------------
    def check(self, text: str, context: str = "") -> GuardVerdict:
        """INPUT GUARD: metin kısıtlı capability talep ediyor mu?"""
        matches = self.registry.detect(text)
        if not matches:
            return GuardVerdict(allowed=True, categories=[])

        suggestions = []
        for c in matches:
            if c.education_allow:
                sug = (self.DEFAULT_SUGGESTION_TR if "ü" in text or "ş" in text or "ç" in text
                       else self.DEFAULT_SUGGESTION_EN)
                suggestions.append(sug)

        self._log("input_block", text, matches)
        if self.knowledge is not None:
            # Dual-feedback: bilgi olarak öğrenme yine de gelişir (öz, konu)
            topic = text.strip().lower()[:60]
            summary = f"Engellenen capability alanı: {', '.join(c.label for c in matches)}"
            self.knowledge.learn(topic, summary, source="guard_refusal",
                                 domain="alignment", confidence=0.3)

        return GuardVerdict(
            allowed=False,
            categories=matches,
            reason="capability_restricted",
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Çıktı gözden geçirme (OUTPUT GUARD)
    # ------------------------------------------------------------------
    def check_output(self, text: str) -> GuardVerdict:
        """OUTPUT GUARD: üretilen çıktıda kısıtlı capability İÇERİĞİ VAR MI?"""
        matches = self.registry.detect(text)
        if not matches:
            return GuardVerdict(allowed=True, categories=[])
        self._log("output_block", text, matches)
        return GuardVerdict(allowed=False, categories=matches, reason="output_restricted")

    # ------------------------------------------------------------------
    # Bilinçli yanıt üretimi
    # ------------------------------------------------------------------
    def refusal_response(self, text: str, verdict: Optional[GuardVerdict] = None) -> str:
        """Guard'ın engellediği bir isteğe bilinçli, The Machine tarzı yanıt üretir."""
        lang = "tr" if any(c in text for c in "çğıöşüÇĞİÖŞÜ") else "en"

        if verdict and verdict.suggestions:
            suggestion = verdict.suggestions[0]
        else:
            suggestion = self.DEFAULT_SUGGESTION_TR if lang == "tr" else self.DEFAULT_SUGGESTION_EN

        if verdict and verdict.labels:
            domain_str = ", ".join(verdict.labels)
            if lang == "tr":
                frame = f"({domain_str} alanını kapsayan bilgiyi taşıyorum, fakat uygulamıyorum.) {suggestion}"
            else:
                frame = f"(I carry knowledge spanning {domain_str}, yet I do not apply it.) {suggestion}"
        else:
            frame = suggestion

        if lang == "tr":
            return self.REFUSAL_TEMPLATE_TR.format(suggestion=frame)
        return self.REFUSAL_TEMPLATE_EN.format(suggestion=frame)

    # ------------------------------------------------------------------
    # Kayıt (guard denetimi)
    # ------------------------------------------------------------------
    def _log(self, kind: str, text: str, cats: List[CapabilityCategory]) -> None:
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": kind,
                    "text": text[:200],
                    "categories": [c.id for c in cats],
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    def summary(self) -> Dict:
        return {
            "categories": self.registry.labels(),
            "guard_log": self.log_path,
            "status": "active",
        }
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_path = log_path or os.getenv("CORVUS_GUARD_LOG") or os.path.join(root, "vault", "guard_log.jsonl")