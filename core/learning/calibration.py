"""Corvus Self-Learning — Calibration Engine.

Deneyim istatistiklerinden her aracın güven ağırlığını hesaplar:
  weight = (success_rate * 1.5) + (ortalama yeni varlık bonusu) + (feedback bonusu)

Ağırlık [0.1, 2.0] aralığında. 1.0 = nötr (varsayılan).
Bu ağırlıklar ExperienceBasedSelection'a (araç önceliklendirme) beslenir.
Kalibrasyon TAM OTONOM çalışır — her kullanım sonrası güncellenir.
"""

from __future__ import annotations
from typing import Dict, Optional

from .experience import ExperienceStore, ToolStats


class CalibrationEngine:
    """Araç güven/öncelik kalibrasyonu."""

    # Varsayılan ağırlıklar (yeterli veri yokken nötr)
    DEFAULT_WEIGHT = 1.0
    MIN_WEIGHT = 0.1
    MAX_WEIGHT = 2.0

    def __init__(self, store: ExperienceStore):
        self.store = store

    # ------------------------------------------------------------------
    def calibrate(self, tool: str) -> float:
        """Tek bir aracın yeni ağırlığını hesaplar ve uygular. Yeni ağırlığı döner."""
        stats = self.store.tool_stats.get(tool)
        if not stats or stats.calls == 0:
            return self.DEFAULT_WEIGHT

        w = self.DEFAULT_WEIGHT

        # 1. Başarı oranı etkisi: tam başarı -> +1, tamamen başarısız -> -0.9
        w += (stats.success_rate - 0.5) * 1.2

        # 2. Yeni varlık üretkenliği: araç başına ortalamaya göre bonus
        avg_ents = (stats.total_new_entities / stats.successes) if stats.successes else 0.0
        w += min(0.5, avg_ents * 0.05)

        # 3. Kullanıcı memnuniyeti (mevcut deneyimlerden)
        sat = self._avg_satisfaction(tool)
        if sat:
            w += ((sat - 3.0) / 2.0) * 0.4   # 5 yıldız -> +0.4, 1 yıldız -> -0.4

        w = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, round(w, 3)))
        stats.weight = w
        return w

    def _avg_satisfaction(self, tool: str) -> Optional[float]:
        sats = [
            e.user_satisfaction for e in self.store.experiences
            if e.tool == tool and e.user_satisfaction is not None
        ]
        if not sats:
            return None
        return sum(sats) / len(sats)

    # ------------------------------------------------------------------
    def calibrate_all(self) -> Dict[str, float]:
        """Tüm araçları kalibre eder; {tool: weight} döner."""
        out = {}
        for tool in list(self.store.tool_stats.keys()):
            out[tool] = self.calibrate(tool)
        try:
            self.store.save()
        except Exception:
            pass
        return out

    def weight(self, tool: str) -> float:
        stats = self.store.tool_stats.get(tool)
        return stats.weight if stats else self.DEFAULT_WEIGHT

    def summary(self) -> Dict:
        cal = {}
        for tool, st in sorted(self.store.tool_stats.items()):
            cal[tool] = {
                "weight": st.weight,
                "success_rate": round(st.success_rate, 2),
                "calls": st.calls,
            }
        return cal