"""Corvus Corax v1.1 - Evidence Weighting & Reliability Model.

Her kanıtın Bayesian güncellemede ne kadar ağırlık taşıyacağını hesaplar.
Faktörler: source reliability (admiralty), corroboration bonus, temporal decay, conflict penalty.
"""
import math
from datetime import datetime, timezone


# Admiralty kodu -> temel source reliability skoru
ADMIRALTY_RELIABILITY = {
    "A1": 1.00, "A2": 0.95, "A3": 0.90,
    "B1": 0.90, "B2": 0.85, "B3": 0.80,
    "C1": 0.75, "C2": 0.70, "C3": 0.65,
    "D1": 0.55, "D2": 0.50, "D3": 0.45,
    "E1": 0.35, "E2": 0.30, "E3": 0.25,
    "F":  0.10,  # Güvenilirliği bilinmiyor
}

# Admiralty kodu -> Bayesian likelihood çifti (P_E_given_H, P_E_given_not_H)
ADMIRALTY_LIKELIHOOD = {
    "A1": (0.95, 0.05), "A2": (0.93, 0.07), "A3": (0.90, 0.10),
    "B1": (0.88, 0.12), "B2": (0.82, 0.18), "B3": (0.78, 0.22),
    "C1": (0.72, 0.28), "C2": (0.65, 0.35), "C3": (0.60, 0.40),
    "D1": (0.52, 0.48), "D2": (0.46, 0.54), "D3": (0.42, 0.58),
    "E1": (0.35, 0.65), "E2": (0.28, 0.72), "E3": (0.22, 0.78),
    "F":  (0.15, 0.85),
}

DEFAULT_LIKELIHOOD = (0.60, 0.40)


class EvidenceWeighter:
    """Kanıt Güvenilirlik Ağırlık Motoru.

    Her kanıtın Bayesian güncellemesine katkısını belirleyen ağırlık hesaplar.
    Ağırlık [0.0 - 2.0] aralığında, 1.0 = baseline.
    """

    CORROBORATION_BONUS_PER_SOURCE = 0.15
    MAX_CORROBORATION_MULTIPLIER = 2.0
    TEMPORAL_DECAY_6M = 0.85   # 6 aydan eski
    TEMPORAL_DECAY_1Y = 0.70   # 1 yıldan eski
    TEMPORAL_DECAY_2Y = 0.50   # 2 yıldan eski
    CONFLICT_PENALTY = 0.50

    def compute_weight(self, evidence) -> float:
        """Bir Evidence nesnesinin toplam ağırlığını hesaplar.

        Args:
            evidence: Evidence dataclass/nesnesi (admiralty_code, corroborating_sources,
                      status, timestamp alanlarını içermeli)
        Returns:
            float - ağırlık skoru [0.0 - 2.0]
        """
        # 1. Source reliability (admiralty kodu)
        code = getattr(evidence, "admiralty_code", "B2") or "B2"
        base_reliability = ADMIRALTY_RELIABILITY.get(code, 0.65)

        # 2. Corroboration bonus
        sources = getattr(evidence, "corroborating_sources", set())
        n_sources = len(sources) if sources else 1
        corroboration_mult = min(
            self.MAX_CORROBORATION_MULTIPLIER,
            1.0 + self.CORROBORATION_BONUS_PER_SOURCE * (n_sources - 1)
        )

        # 3. Temporal decay
        temporal_mult = self._compute_temporal_decay(getattr(evidence, "timestamp", None))

        # 4. Conflict penalty
        status = getattr(evidence, "status", "VALIDATED")
        conflict_mult = self.CONFLICT_PENALTY if status == "CONFLICT" else 1.0

        weight = base_reliability * corroboration_mult * temporal_mult * conflict_mult
        return round(min(2.0, max(0.01, weight)), 4)

    def compute_likelihood(self, evidence) -> tuple:
        """Admiralty kodundan P(E|H) ve P(E|¬H) değerlerini döner.

        Args:
            evidence: Evidence nesnesi
        Returns:
            tuple: (P_E_given_H: float, P_E_given_not_H: float)
        """
        code = getattr(evidence, "admiralty_code", "B2") or "B2"
        p_e_h, p_e_not_h = ADMIRALTY_LIKELIHOOD.get(code, DEFAULT_LIKELIHOOD)

        # Conflict kanıt likelihood'ı tersine çevir (zayıflatarak)
        status = getattr(evidence, "status", "VALIDATED")
        if status == "CONFLICT":
            # Çelişkili kanıt H'yi destekleme olasılığını düşürür
            p_e_h = max(0.10, p_e_h * 0.5)
            p_e_not_h = min(0.90, p_e_not_h + (p_e_h * 0.3))

        return (p_e_h, p_e_not_h)

    def _compute_temporal_decay(self, timestamp_str: str) -> float:
        """Kanıtın yaşına göre temporal decay çarpanı hesaplar."""
        if not timestamp_str:
            return 1.0
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            age_days = (now - ts).days
            if age_days >= 730:   # 2 yıl+
                return self.TEMPORAL_DECAY_2Y
            elif age_days >= 365: # 1 yıl+
                return self.TEMPORAL_DECAY_1Y
            elif age_days >= 180: # 6 ay+
                return self.TEMPORAL_DECAY_6M
            return 1.0
        except Exception:
            return 1.0
