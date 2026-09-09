"""Corvus Alignment — KnowledgeStore.

Corvus'un "bildikleri"ni tutar — capability sınırından bağımsız, sınırsız
öğrenme tarafı. Felsefe, edebiyat, OSINT, davranış analizi, savunma ve
(tehlikeli olabilecek) konuların KAVRAMSAL bilgisi de burada yaşar.

ÖNEMLİ AYRIM:
  - KnowledgeStore NEYİ BİLDİĞİNİ tutar (epistemic).
  - ActionGuard NEYİ YAPABİLECEĞİNİ sınırlar (behavioral).
  - Bir konu KnowledgeStore'a girebilir, ancak ActionGuard o bilgiyi
    capability'ye dönüştürmez — "derinleşebilirim ama yapmamak için kodlandım".

Kalıcılık: vault/knowledge.json  (CORVUS_KNOWLEDGE_STATE env ile değiştirilebilir)
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


class KnowledgeStore:
    """Kalıcı bilgi dağarcığı — bilgi kazanımı ve taşıma katmanı."""

    def __init__(self, path: Optional[str] = None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = path or os.getenv("CORVUS_KNOWLEDGE_STATE") or os.path.join(root, "vault", "knowledge.json")
        self.facts: Dict[str, dict] = {}      # konu -> {summary, source, added_at, ...}
        self.domains: Dict[str, int] = {}     # alan -> görülme sayısı (ilgi)
        self._load()

    # ------------------------------------------------------------------
    # Kalıcılık
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.facts = data.get("facts", {})
            self.domains = data.get("domains", {})
        except Exception:
            self.facts = {}
            self.domains = {}

    def save(self) -> str:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"facts": self.facts, "domains": self.domains},
                          f, ensure_ascii=False, indent=2)
            return self.path
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Öğrenme (bilgi kazanımı)
    # ------------------------------------------------------------------
    def learn(self, topic: str, summary: str, source: str = "observation",
              domain: str = "general", confidence: float = 0.5) -> None:
        """Bilgi edinir — kalıcı kaydeder. Capability sınırıyla ilgisizdir."""
        topic = topic.strip().lower()
        if not topic or not summary:
            return
        now = datetime.now(timezone.utc).isoformat()

        if topic in self.facts:
            entry = self.facts[topic]
            entry["summary"] = summary
            entry["confidence"] = confidence
            entry["updated_at"] = now
            if source not in entry["sources"]:
                entry["sources"].append(source)
        else:
            self.facts[topic] = {
                "summary": summary,
                "source": source,
                "sources": [source],
                "domain": domain,
                "confidence": confidence,
                "added_at": now,
                "updated_at": now,
            }
        self.domains[domain] = self.domains.get(domain, 0) + 1
        try:
            self.save()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Sorgu / hatırlama
    # ------------------------------------------------------------------
    def has(self, topic: str) -> bool:
        return topic.strip().lower() in self.facts

    def get(self, topic: str) -> Optional[dict]:
        return self.facts.get(topic.strip().lower())

    def recall(self, keyword: str, limit: int = 5) -> List[dict]:
        """Anahtar kelimeyle en ilgili bilgi kayıtlarını hatırlar."""
        kw = keyword.lower()
        scored = []
        for t, entry in self.facts.items():
            score = 0
            if kw in t:
                score += 3
            if kw in entry.get("summary", "").lower():
                score += 1
            if kw in entry.get("domain", "").lower():
                score += 1
            scored.append((score, t, entry))
        scored.sort(key=lambda x: -x[0])
        return [{"topic": t, **e} for s, t, e in scored[:limit] if s > 0]

    def top_domains(self) -> List[str]:
        return [d for d, _ in sorted(self.domains.items(), key=lambda x: -x[1])]

    def summary(self) -> Dict:
        return {
            "fact_count": len(self.facts),
            "domains": self.domains,
            "topics": list(self.facts.keys())[:20],
        }