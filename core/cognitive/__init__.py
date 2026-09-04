"""Corvus Corax v1.1.1 - Cognitive Interface & Agent Layer Package.

Natural language understanding, multi-turn memory, persona synthesis,
and cognitive provider abstractions ("The Machine" intelligence layer).
"""

from .dialogue import CognitiveDialogueEngine
from .memory import ConversationMemory
from .persona import MachinePersona
from .intent import IntentExtractor, IntentResult

__all__ = [
    "CognitiveDialogueEngine",
    "ConversationMemory",
    "MachinePersona",
    "IntentExtractor",
    "IntentResult",
]
