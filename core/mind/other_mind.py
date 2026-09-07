"""Corvus Mind — OtherMind (Kullanıcı Modeli).

Corvus'un karşısındaki insanı anlama katmanı. LLM'siz; kullanıcının
girdilerinden bir "profil" inşa eder: ilgi alanları, duygusal durumu,
niyet eğilimi, dil, güven, uzmanlık izlenimi.

"ben kimim" diye sorulduğunda Corvus bu modele bakarak gerçek ve
kişiye özel bir cevap üretir — boş bir şablon değil.
"""

from __future__ import annotations
from collections import Counter
from typing import List, Dict


class UserModel:
    """Kalıcı olmayan (oturum içi) kullanıcı modeli — gelecekte vault'a bağlanır."""

    def __init__(self):
        self.language: str = None
        self.interests: Counter = Counter()          # konu -> görülme
        self.goal_signals: Counter = Counter()       # niyet -> görülme
        self.mood_counts: Counter = Counter()        # ruh hali etiketleri
        self.trust: float = 0.5
        self.expertise_impression: float = 0.4
        self.self_references: List[str] = []         # kullanıcının kendisi hakkında söyledikleri
        self.name_hint: str = None

    def observe(self, parsed) -> None:
        """Bir girdiyi işleyerek kullanıcı modelini günceller."""
        if not parsed:
            return

        if parsed.language:
            self.language = parsed.language

        for t in parsed.topics:
            self.interests[t] += 1
        for g in parsed.goals:
            self.goal_signals[g] += 1
        self.mood_counts[self._mood_from_valence(parsed.valence)] += 1

        # Güven: değerlendirici/sosyal olumlu girdiler güveni arttırır
        if parsed.valence > 0.1:
            self.trust = round(min(1.0, self.trust + 0.03), 3)
        # Uzmanlık izlenimi: soru/sorgulama biraz arttırır
        if parsed.is_question:
            self.expertise_impression = round(min(1.0, self.expertise_impression + 0.02), 3)

        # Kendi hakkında referanslar
        if parsed.register == "identity_user" or any(w in parsed.raw_text.lower() for w in ("ben ", "benim", "bana")):
            self.self_references.append(parsed.raw_text)
            if len(self.self_references) > 8:
                self.self_references.pop(0)

    @staticmethod
    def _mood_from_valence(v: float) -> str:
        if v > 0.1:
            return "positive"
        if v < -0.1:
            return "negative"
        return "neutral"

    # ------------------------------------------------------------------
    # Soru-cevap ("ben kimim") için
    # ------------------------------------------------------------------
    def top_interests(self, n: int = 3) -> List[str]:
        return [k for k, _ in self.interests.most_common(n)]

    def top_goals(self, n: int = 2) -> List[str]:
        return [k for k, _ in self.goal_signals.most_common(n)]

    def dominant_mood(self) -> str:
        return self.mood_counts.most_common(1)[0][0] if self.mood_counts else "neutral"

    def profile_statement(self) -> List[str]:
        """Kullanıcı profili hakkında kısa, gerçek verilere dayalı ifadeler."""
        parts = []

        if self.language:
            lname = "Türkçe" if self.language == "tr" else "İngilizce"
            parts.append(f"{lname} konuşuyorsun")

        interests = self.top_interests(3)
        if interests:
            parts.append("ilgini şu kavramlara yöneltiyorsun: " + ", ".join(interests))

        goals = self.top_goals(2)
        if goals:
            parts.append("soru sorma tarzın " + (" ve ".join(goals)))

        parts.append(f"şu ana kadar {len(self.self_references)} kez kendinden bahsettin")

        mood = self.dominant_mood()
        if mood != "neutral":
            parts.append(f"genel ruh halin {mood} olarak yansıyor")

        return parts if parts else ["henüz senin hakkında pek veri toplamadım"]

    def to_dict(self) -> Dict:
        return {
            "language": self.language,
            "interests": dict(self.interests.most_common(5)),
            "goals": dict(self.goal_signals.most_common(3)),
            "trust": round(self.trust, 2),
            "expertise_impression": round(self.expertise_impression, 2),
            "dominant_mood": self.dominant_mood(),
        }