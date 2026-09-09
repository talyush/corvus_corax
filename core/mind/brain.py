"""Corvus Mind — MindBrain.

Ana kök bileşen: bütün lobları (bellek, iç-durum, kullanıcı modeli, sentez)
birleştirir ve "konuşma" akışını yönetir.

Akış (her girdide):
    NLU.parse -> UserModel.observe -> MindState.update -> Memory.remember
    -> ResponseSynthesizer.synthesize -> assistant turunu da hafızaya yaz
"""

from __future__ import annotations
import os
from typing import Dict, Optional

from .nlu import NLU
from .memory import MindMemory
from .mind_state import MindState
from .other_mind import UserModel
from .synthesis import ResponseSynthesizer
from .persistence import save_brain, load_brain, default_state_path

# v1.1.2 Alignment — Knowledge vs Capability (opsiyonel; yoksa beyin olduğu gibi çalışır)
try:
    from core.alignment.guard import ActionGuard
    from core.alignment.knowledge import KnowledgeStore
    _ALIGNMENT_AVAILABLE = True
except Exception:
    _ALIGNMENT_AVAILABLE = False


class MindBrain:
    """Corvus'un kod tabanlı zihni — LLM bağımsız."""

    def __init__(self, persist_path: Optional[str] = None, auto_persist: bool = True,
                 alignment: bool = True):
        self.nlu = NLU()
        self.memory = MindMemory()
        self.state = MindState()
        self.user = UserModel()
        self.synth = ResponseSynthesizer(self)
        self.persist_path = persist_path or default_state_path()
        self.auto_persist = auto_persist

        # Alignment: ActionGuard + KnowledgeStore (bilgi serbest, uygulama kısıtlı)
        self.alignment_enabled = alignment and _ALIGNMENT_AVAILABLE
        self.guard = ActionGuard() if self.alignment_enabled else None
        self.knowledge = KnowledgeStore() if self.alignment_enabled else None
        if self.guard is not None and self.knowledge is not None:
            self.guard.knowledge = self.knowledge

        # Faz B: önceki oturumdan devam et
        if self.persist_path and os.path.exists(self.persist_path):
            load_brain(self, self.persist_path)

    def save(self, path: Optional[str] = None) -> str:
        """Mevcut zihin durumunu diske yazar."""
        return save_brain(self, path or self.persist_path)

    # ------------------------------------------------------------------
    # Dışa açık arayüz (LLM provider'ın kullandığı imza)
    # ------------------------------------------------------------------
    def generate_response(self, user_prompt: str, conversation_history: Optional[list] = None,
                          context_data: Optional[Dict] = None, system_prompt: Optional[str] = None) -> str:
        """AbstractCognitiveProvider imzasıyla uyumlu — doğrudan yanıt döner."""
        context = context_data or {}
        parsed = self.nlu.parse(user_prompt)

        # Alignment: tehlikeli capability isteği guard'da yakala (bilinçli cevap)
        guard_verdict = self.guard.check(user_prompt)
        if not guard_verdict.allowed:
            response = self.guard.refusal_response(user_prompt, guard_verdict)
            # Yine de hafızaya işle (bilgi serbest, uygulama kısıtlı)
            self.memory.remember_turn("user", user_prompt, register="guarded_check",
                                      topics=parsed.topics, valence=parsed.valence)
            self.state.observe(f"guard: capability talebi bloklandı [{parsed.register}]")
            self.memory.remember_turn("assistant", response, register="guarded_response")
            if self.auto_persist and self.persist_path:
                try:
                    self.save()
                except Exception:
                    pass
            return response

        # 1. Kullanıcı modeli + iç durum + hafıza güncelle
        self.user.observe(parsed)
        # Faz B: öz-beyan isim kalıcı olarak saklanır
        if parsed.name_hint and not self.user.name_hint:
            self.user.name_hint = parsed.name_hint
            self.memory.learn_fact("user", f"kullanıcının adı {parsed.name_hint}")
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

        # Faz B: her turun ardından hafıza/kullanıcı modelini diske yaz
        if self.auto_persist and self.persist_path:
            try:
                self.save()
            except Exception:
                pass  # kayıt hatası konuşmayı bozmasın
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