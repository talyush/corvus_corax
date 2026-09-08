"""Corvus Corax v1.2 - Embedded Cognitive Engine (Offline / Corvus Mind).

Generates dynamic, context-aware, analytical & philosophical responses with 'The Machine' persona.
Zero-dependency, offline-first.

v1.2: This engine now runs on Corvus Mind — our OWN symbolic brain
(core/mind/): NLU -> Memory -> MindState -> UserModel -> ResponseSynthesizer.
LLM is optional/support; this brain does not depend on any language model.

Integrates:
- MindBrain (own brain: memory, inner state, user model, synthesis)
- Knowledge Graph Context (entities, relations, Bayesian hypotheses)
- Multi-Turn Conversation Memory"
"""

from typing import List, Dict, Any, Optional
import os
from .interface import AbstractCognitiveProvider
from core.mind.brain import MindBrain
from core.mind.persistence import default_state_path
from ..persona import MachinePersona


class EmbeddedCognitiveEngine(AbstractCognitiveProvider):
    """Dahili Bilisel ve Derin Akil Yurutme Yanit Uretim Motoru."""

    def __init__(self, persist_path: Optional[str] = None, auto_persist: bool = True):
        self.mind = MindBrain(
            persist_path=persist_path or os.getenv("CORVUS_MIND_STATE") or default_state_path(),
            auto_persist=auto_persist,
        )

    @property
    def provider_name(self) -> str:
        return "Embedded Cognitive Engine (Corvus Mind Neural Core)"

    def is_available(self) -> bool:
        return True

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        """Corvus Mind arayuzunu AbstractCognitiveProvider imzasiyla surer."""
        return self.mind.generate_response(
            user_prompt=user_prompt,
            conversation_history=conversation_history or [],
            context_data=context_data or {},
            system_prompt=system_prompt,
        )
