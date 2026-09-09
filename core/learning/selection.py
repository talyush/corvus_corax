"""Corvus Self-Learning — Experience-Based Tool Selection.

CalibrationEngine'den gelen arac ağırlıklarını ve ExperienceStore'daki
başarı/başarısızlık geçmişini kullanarak, Planner'a "akıllı öncelik sırası"
önerir.

  - Yüksek ağırlıkli araçlar öne çekilir
  - Aynı hedef tipinde sürekli başarısız olan araçlar arkaya itilir
  - Kalibrasyon yeterli veriye dayanmadan (calls < K) nötr davranır
"""

from __future__ import annotations
from typing import Dict, List, Optional

from .experience import ExperienceStore
from .calibration import CalibrationEngine

# Bu kadar çağrıdan sonra istatistik "güvenilir" sayılır
MATURITY_CALLS = 3


class ExperienceBasedSelection:
    """Deneyim odaklı araç sıralama."""

    def __init__(self, store: ExperienceStore, calibration: Optional[CalibrationEngine] = None):
        self.store = store
        self.cal = calibration or CalibrationEngine(store)

    # ------------------------------------------------------------------
    def reorder(self, tools: List[str], target_type: str = "unknown") -> List[str]:
        """
        Planner'dan gelen araç listesini deneyime göre önceliklendirir.
        Otonom çalıştırır — arac sırası deneyimden öğrenilir.
        """
        if len(tools) <= 1:
            return tools

        scored = []
        for tool in tools:
            score = self._tool_score(tool, target_type)
            scored.append((score, tool))

        # önce yüksek skor, sonra original sıra (stabilite)
        scored.sort(key=lambda x: (-x[0], tools.index(x[1])))
        return [t for _, t in scored]

    def _tool_score(self, tool: str, target_type: str) -> float:
        """Deneysel skor: ağırlık + hedef tipi başarı ayarı."""
        stats = self.store.tool_stats.get(tool)

        if not stats or stats.calls < MATURITY_CALLS:
            # Yeterli veri yok -> nötr (weight olsa bile henüz güvenme)
            return 1.0

        weight = stats.weight
        # Aynı hedef tipindeki son başarısızlık ekstra ceza
        recent_fails = [
            e for e in self.store.recent_failures(tool=tool, limit=5)
            if e.target_type == target_type
        ]
        penalty = len(recent_fails) * 0.15
        return max(0.0, weight - penalty)

    def rank_report(self, tools: List[str]) -> List[Dict]:
        """Hangi arac neden öne/arkaya alındı — audit/önizleme için."""
        out = []
        for tool in tools:
            stats = self.store.tool_stats.get(tool)
            mature = bool(stats and stats.calls >= MATURITY_CALLS)
            out.append({
                "tool": tool,
                "weight": round(stats.weight, 2) if stats else 1.0,
                "mature": mature,
                "success_rate": round(stats.success_rate, 2) if stats else None,
                "calls": stats.calls if stats else 0,
            })
        return out