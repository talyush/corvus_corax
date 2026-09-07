"""Corvus Mind — İç Durum ve İkili Motivasyon Motoru.

Corvus'un "ruh hali"ni ve iki zihinsel eğilimini (drive) izler:
  ANALITICAL_DRIVE  : kesinlik, kanıt, örüntü, görev.
  PHILOSOPHICAL_DRIVE: anlam, insan, bağ, felsefe.

Duygusal boyutlar: merak, dikkat (vigilance), bağlanım (engagement),
empati, sakinlik. Her girdiyle hafifçe güncellenir — gerçek bir iç durum
değişimi, sabit "mood" değil. Bu state, yanıtın ton/uzunluk/seçimini belirler.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

_EMO_MAP = {
    "philosophical": {"curiosity": 0.06, "empathy": 0.05, "reflection": 0.06},
    "meta_corvus": {"curiosity": 0.05, "vigilance": 0.03},
    "identity_user": {"empathy": 0.08, "curiosity": 0.04},
    "identity_corvus": {"reflection": 0.05, "calmness": 0.02},
    "emotional_pos": {"empathy": 0.10, "engagement": 0.06},
    "emotional_neg": {"empathy": 0.12, "vigilance": 0.03, "calmness": -0.05},
    "investigate": {"vigilance": 0.08, "engagement": 0.04},
    "social": {"engagement": 0.04},
    "evaluative": {"vigilance": 0.03, "curiosity": 0.03},
}


@dataclass
class MindState:
    """Anlık iç durum — duygusal boyutlar ve drive ekseni."""

    curiosity: float = 0.70
    vigilance: float = 0.80
    engagement: float = 0.75
    empathy: float = 0.50
    calmness: float = 0.90
    # drive_axis: -1 (tamamen analitik) .. +1 (tamamen felsefi/insani)
    drive_axis: float = 0.0
    reflection: float = 0.30
    turn_count: int = 0
    mood: str = "observant"
    observations: List[str] = field(default_factory=list)

    def _clamp(self, v: float) -> float:
        return max(0.0, min(1.0, v))

    def observe(self, note: str) -> None:
        """İç monolog notu ekler."""
        self.observations.append(note)
        if len(self.observations) > 10:
            self.observations.pop(0)

    def update(self, register: str, valence: float, intensity: float, has_entities: bool) -> None:
        """Girdinin kaydı ve duygusal tonuna göre iç durumu günceller."""
        self.turn_count += 1

        # Duygu tonu
        if valence > 0.15:
            key = "emotional_pos"
        elif valence < -0.15:
            key = "emotional_neg"
        else:
            key = register

        delta = _EMO_MAP.get(key, {})
        for attr, amt in delta.items():
            if hasattr(self, attr):
                setattr(self, attr, self._clamp(getattr(self, attr) + amt * intensity))

        # Drive ekseni (analitik <-> felsefi)
        drive_target = 0.0
        if register in ("philosophical", "meta_corvus", "identity_user", "identity_corvus"):
            drive_target = 0.5
        elif register in ("investigate", "evaluative"):
            drive_target = -0.5
        self.drive_axis = self._clamp(self.drive_axis + (drive_target - self.drive_axis) * 0.2)

        # Mood türet
        self.mood = self._derive_mood(register, valence)

    def _derive_mood(self, register: str, valence: float) -> str:
        if valence < -0.15:
            return "vigilant" if register not in ("emotional",) else "compassionate"
        if register in ("philosophical", "meta_corvus"):
            return "reflective"
        if register == "social":
            return "engaged"
        if register == "investigate":
            return "analytical"
        if valence > 0.15:
            return "intrigued"
        return "observant"

    def emotional_blend(self) -> str:
        """Yanıt tonunu yönlendiren kısa etiket."""
        if self.drive_axis > 0.4:
            return "humane"
        if self.drive_axis < -0.4:
            return "analytical"
        return "balanced"

    def to_dict(self) -> Dict:
        return {
            "curiosity": round(self.curiosity, 2),
            "vigilance": round(self.vigilance, 2),
            "engagement": round(self.engagement, 2),
            "empathy": round(self.empathy, 2),
            "calmness": round(self.calmness, 2),
            "reflection": round(self.reflection, 2),
            "drive_axis": round(self.drive_axis, 2),
            "turn_count": self.turn_count,
            "mood": self.mood,
            "blend": self.emotional_blend(),
        }