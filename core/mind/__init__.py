"""Corvus Corax v1.2 — Corvus Mind.

Kendi beyni: sembolik/kod tabanl\u0131 zihin. LLM'e ba\u011f\u0131ml\u0131 de\u011fil;
LLM yaln\u0131zca opsiyonel destek olarak durabilir.

Yap\u0131:
    NLU (anlama) -> MindState (i\u00e7 durum) -> OtherMind (kullan\u0131c\u0131 modeli)
                 -> MindMemory (haf\u0131za) -> Synthesis (yan\u0131t sentezi)

Temel fikir: \u015fablon se\u00e7ici DE\u011e\u0130L. Her yan\u0131t; ger\u00e7ek haf\u0131za, kullan\u0131c\u0131
modeli, i\u00e7 g\u00f6zlemler ve grafik ba\u011flam\u0131ndan beslenerek KOMPOZE edilir.
"""

from .brain import MindBrain
from .nlu import NLU, ParsedInput
from .mind_state import MindState
from .memory import MindMemory
from .other_mind import UserModel
from .synthesis import ResponseSynthesizer

__all__ = [
    "MindBrain",
    "NLU",
    "ParsedInput",
    "MindState",
    "MindMemory",
    "UserModel",
    "ResponseSynthesizer",
]