"""Corvus Mind — MindBrain.

Ana kök bileşen: bütün lobları (bellek, iç-durum, kullanıcı modeli, sentez)
birleştirir ve "konuşma" akışını yönetir.

Akış (her girdide):
    NLU.parse -> UserModel.observe -> MindState.update -> Memory.remember
    -> ResponseSynthesizer.synthesize -> assistant turunu da hafızaya yaz
"""

from __future__ import annotations
from typing import Dict, Optional

from .nlu import NLU
from .memory import MindMemory
from .mind_state import MindState
from .other_mind import UserModel
from .synthesis import ResponseSynthesizer


class MindBrain:
    """Corvus'un kod tabanlı zihni — LLM bağımsız."""

    def __init__(self):
        self.nlu = NLU()
        self.memory = MindMemory()
        self.state = MindState()
        self.user = UserModel()
        self.synth = ResponseSynthesizer(self)

    # ------------------------------------------------------------------
    # Dışa açık arayüz (LLM provider'ın kullandığı imza)
    # ------------------------------------------------------------------
    def generate_response(self, user_prompt: str, conversation_history: Optional[list] = None,
                          context_data: Optional[Dict] = None, system_prompt: Optional[str] = None) -> str:
        """AbstractCognitiveProvider imzasıyla uyumlu — doğrudan yanıt döner."""
        context = context_data or {}
        parsed = self.nlu.parse(user_prompt)

        # 1. Kullanıcı modeli + iç durum + hafıza güncelle
        self.user.observe(parsed)
        self.state.update(parsed.register, parsed.valence, parsed.intensity, bool(parsed.entities))
        self.memory.remember_turn("user", user_prompt, register=parsed.register,
                                  topics=parsed.topics, valence=parsed.valence)
        self.state.observe(f"girdi: '{user_prompt[:50]}' [{parsed.register}]")

        # 2. Yanıtı sentezle
        response = self.synth.synthesize(parsed, context)

        # 3. Yanıtı da hafızaya yaz (yardımcı tur)
        self.memory.remember_turn("assistant", response, register=parsed.register,
                                  topics=parsed.topics)

        self.state.observe(f"yanıt verildi [{parsed.register}]")
        return response

    # ------------------------------------------------------------------
    # İç inceleme / test
    # ------------------------------------------------------------------
    def debug_state(self) -> Dict:
        return {
            "nlu": self.nlu,
            "memory": self.memory.summary(),
            "state": self.state.to_dict(),
            "user": self.user.to_dict(),
        }