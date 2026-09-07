"""Corvus Corax v1.1.1 - Cognitive Interface & Agent Layer Package.

Natural language understanding, multi-turn memory, persona synthesis,
conversational reasoning, emotional & motivation layer,
and cognitive provider abstractions ("The Machine" intelligence layer).
"""

from .dialogue import CognitiveDialogueEngine
from .memory import ConversationMemory
from .persona import MachinePersona
from .intent import IntentExtractor, IntentResult
from .reasoning_engine import ConversationalReasoningEngine, QuestionRegister, ThoughtTrace
from .emotional_layer import MotivationEngine, EmotionalState

__all__ = [
    "CognitiveDialogueEngine",
    "ConversationMemory",
    "MachinePersona",
    "IntentExtractor",
    "IntentResult",
    "ConversationalReasoningEngine",
    "QuestionRegister",
    "ThoughtTrace",
    "MotivationEngine",
    "EmotionalState",
]
