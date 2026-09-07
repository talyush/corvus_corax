"""Corvus Mind — Hafıza (MindMemory).

Epizodik (episodic) + semantik (semantic) + çalışma (working) belleği.
LLM'siz; gerçek konuşma geçmişini yapısal saklar, çürüme (decay) ile
önem derecesine göre unutur/hatırlar, konu etiketleriyle ilişkilendirir.

Amaç: Corvus'un "az önce ne dedin", "bu konuda ne konuştuk" gibi
gerçek hafıza tabanlı yanıtlar verebilmesini sağlamak.
"""

from __future__ import annotations
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MemoryTurn:
    """Tek bir hafıza turu — gerçek içerik + anlamsal etiketler."""

    role: str                 # "user" | "assistant"
    content: str
    register: str = "conversational"
    topics: List[str] = field(default_factory=list)
    valence: float = 0.0
    salience: float = 1.0    # sonradan çürütülür
    turn_no: int = 0

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "register": self.register,
            "topics": self.topics,
            "valence": round(self.valence, 2),
            "salience": round(self.salience, 2),
            "turn_no": self.turn_no,
        }


class MindMemory:
    """Katmanlı hafıza: epizodik (turlar) + semantik (olgular)."""

    def __init__(self, memory_size: int = 40):
        self.turns: deque = deque(maxlen=memory_size)
        self.facts: Dict[str, List[str]] = {}   # konu -> öğrenilen ifadeler
        self.turn_no = 0
        self.observation_log: List[str] = []     # iç-gözlem notları (iç monolog)

    # ------------------------------------------------------------------
    # Kayıt
    # ------------------------------------------------------------------
    def remember_turn(self, role: str, content: str, register: str = "conversational",
                      topics: Optional[List[str]] = None, valence: float = 0.0) -> None:
        self.turn_no += 1
        self.turns.append(MemoryTurn(
            role=role, content=content, register=register,
            topics=topics or [], valence=valence, salience=1.0, turn_no=self.turn_no,
        ))

    def observe(self, note: str) -> None:
        """İç monolog / düşünce notu ekler (son 12 tutulur)."""
        self.observation_log.append(note)
        if len(self.observation_log) > 12:
            self.observation_log.pop(0)

    def learn_fact(self, topic: str, statement: str) -> None:
        """Semantik olgu öğrenir (örn. kullanıcı hakkında, konu hakkında)."""
        self.facts.setdefault(topic, [])
        if statement not in self.facts[topic]:
            self.facts[topic].append(statement)

    # ------------------------------------------------------------------
    # Geri Çağırma
    # ------------------------------------------------------------------
    def _decay(self) -> None:
        """Turlara zaman/önem çürümesi uygular."""
        for t in self.turns:
            t.salience *= 0.96

    def recall(self, tokens: Optional[List[str]] = None, limit: int = 4) -> List[MemoryTurn]:
        """Kullanıcı turlarını ilgili ontolojiye göre geri çağırır."""
        self._decay()
        if not tokens:
            relevant = [t for t in self.turns if t.role == "user"]
        else:
            tok_set = set(tokens)
            relevant = [
                t for t in self.turns if t.role == "user"
                and (set(t.topics) & tok_set or any(word in t.content for word in tokens))
            ]
        # önem: salience (güncellik) > turn_no (sıra)
        ranked = sorted(relevant, key=lambda t: (t.salience, t.turn_no), reverse=True)
        return ranked[:limit]

    def last_user_messages(self, n: int = 3) -> List[str]:
        return [t.content for t in list(self.turns)[-n:] if t.role == "user"]

    def fact_about(self, topic: str) -> List[str]:
        return list(self.facts.get(topic, []))

    def all_user_topics(self) -> List[str]:
        c: Counter = Counter()
        for t in self.turns:
            if t.role == "user":
                for top in t.topics:
                    c[top] += 1
        return [top for top, _ in c.most_common(5)]

    def recent_topic(self) -> Optional[str]:
        for t in reversed(self.turns):
            if t.topics:
                return t.topics[0]
        return None

    def summary(self) -> Dict:
        return {
            "turn_count": self.turn_no,
            "stored_turns": len(self.turns),
            "observation_notes": len(self.observation_log),
            "active_topics": self.all_user_topics(),
            "facts": list(self.facts.keys()),
        }

    def to_dict(self) -> Dict:
        return {
            "turns": [t.to_dict() for t in self.turns],
            "facts": self.facts,
            "observations": list(self.observation_log),
            "turn_no": self.turn_no,
        }