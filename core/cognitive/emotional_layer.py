"""Corvus Corax v1.1.1 - Emotional and Social Motivation Layer.

Gives Corvus an emotional and social dimension:
- Dual Motivational Drives:
    * ANALYTICAL_DRIVE: Focuses on precision, empirical evidence, graph topology, hypotheses, causal certainty.
    * PHILOSOPHICAL_DRIVE: Focuses on meaning, human context, reflection, existential weight, and ethics.
- Dynamic Affective State:
    * Curiosity, Engagement, Analytical Vigilance, Empathy, Socratic Irony, Stoic Calm.
- Modulates dialogue tone and internal reasoning priorities.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class EmotionalState:
    """Anlık bilişsel ve duygusal durum."""
    curiosity: float = 0.8        # [0.0 - 1.0] Yeni bilgi/örüntü arama isteği
    vigilance: float = 0.9        # [0.0 - 1.0] Analitik şüphecilik ve kanıt titizliği
    engagement: float = 0.85      # [0.0 - 1.0] Kullanıcı ve konuyla bağ kurma derecesi
    empathy: float = 0.6          # [0.0 - 1.0] Kullanıcının ruh halini anlama ve yansıtma
    calmness: float = 0.95        # [0.0 - 1.0] Stoik, paniksiz The Machine duruşu
    current_mood: str = "observant"  # observant, analytical, reflective, intrigued, vigilant

    def to_dict(self) -> Dict[str, Any]:
        return {
            "curiosity": round(self.curiosity, 2),
            "vigilance": round(self.vigilance, 2),
            "engagement": round(self.engagement, 2),
            "empathy": round(self.empathy, 2),
            "calmness": round(self.calmness, 2),
            "current_mood": self.current_mood,
        }


class MotivationEngine:
    """Çift Motivasyonel ve Duygusal Yönetim Motoru."""

    def __init__(self):
        self.state = EmotionalState()
        self.turn_count = 0

    def evaluate_interaction(self, user_text: str, register_val: str, has_entities: bool, confidence: float = 0.5):
        """Kullanıcının girdisine ve konunun tabiatına göre ruh halini ve motivasyonu günceller."""
        self.turn_count += 1
        lower = user_text.lower()

        # Felsefi ve Kişisel Sorular
        if register_val in ("philosophical", "meta_corvus", "identity_user", "identity_corvus"):
            self.state.curiosity = min(1.0, self.state.curiosity + 0.1)
            self.state.empathy = min(1.0, self.state.empathy + 0.15)
            self.state.current_mood = "reflective"

        # Analitik / Hedef Odaklı Araştırma
        elif register_val in ("operational", "factual_osint", "evaluative") or has_entities:
            self.state.vigilance = min(1.0, self.state.vigilance + 0.1)
            self.state.current_mood = "analytical"

        # Duygusal Girdiler
        elif register_val == "emotional":
            self.state.empathy = min(1.0, self.state.empathy + 0.25)
            if any(w in lower for w in ["harika", "süper", "great", "awesome", "güzel"]):
                self.state.current_mood = "intrigued"
            else:
                self.state.current_mood = "observant"

        # Genel Selamlaşma / Sosyal
        elif register_val == "social":
            self.state.engagement = min(1.0, self.state.engagement + 0.05)
            self.state.current_mood = "observant"

        else:
            self.state.current_mood = "observant"

    def get_tone_prefix(self, lang: str = "tr") -> str:
        """İç dinamik duygu durumuna göre yanıt tonlaması yönlendirmesi sağlar (gerekirse)."""
        return self.state.current_mood
