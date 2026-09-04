"""Corvus Corax v1.1.1 - Cognitive Dialogue Engine.

Central orchestrator for the Cognitive Interface & Conversational Agent:
- Memory management & reference resolution.
- Intent & entity extraction.
- Automatic cognitive provider selection (Ollama -> Cloud -> Embedded).
- ContextManager graph bidirectional synchronization.
"""
from typing import Dict, Any, Optional
from .memory import ConversationMemory
from .intent import IntentExtractor, IntentResult
from .persona import MachinePersona
from .providers.local_engine import EmbeddedCognitiveEngine
from .providers.api_providers import OllamaProvider, OpenAIProvider
from .providers.interface import AbstractCognitiveProvider


class CognitiveDialogueEngine:
    """Bilişsel Diyalog ve Doğal Dil Arayüz Motoru."""

    def __init__(self, context_manager=None):
        self.context = context_manager
        self.memory = ConversationMemory()
        self.intent_extractor = IntentExtractor()
        self.embedded_engine = EmbeddedCognitiveEngine()
        self.ollama_provider = OllamaProvider()
        self.openai_provider = OpenAIProvider()
        self.active_provider: AbstractCognitiveProvider = self._select_best_provider()

    def _select_best_provider(self) -> AbstractCognitiveProvider:
        """Kullanılabilir en yetkin bilişsel sağlayıcıyı seçer."""
        if self.ollama_provider.is_available():
            return self.ollama_provider
        if self.openai_provider.is_available():
            return self.openai_provider
        return self.embedded_engine

    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Kullanıcı mesajını işler, hafızayı günceller ve dinamik yanıt üretir.
        
        Returns:
            dict with:
                - response: str
                - intent: IntentResult dict
                - provider: str
                - active_target: str
                - suggested_command: Optional[str]
        """
        raw_text = user_message.strip()
        if not raw_text:
            return {
                "response": "...",
                "intent": {},
                "provider": self.active_provider.provider_name,
                "active_target": self.memory.active_target,
            }

        # 1. Resolve references if user uses pronouns ("o", "this target")
        fallback_target = self.memory.resolve_reference(raw_text) or self.memory.active_target

        # 2. Extract Intent and Entities
        intent_res = self.intent_extractor.extract(raw_text, fallback_target=fallback_target)

        # 3. Update Conversation Memory
        self.memory.add_user_message(raw_text, intent=intent_res.intent_type, entities=intent_res.entities)
        if intent_res.entities:
            target = intent_res.entities[0]
            target_type = intent_res.entity_types.get(target, "unknown")
            self.memory.update_focal_target(target, target_type)

            # Sync entity into central ContextManager if available
            if self.context and hasattr(self.context, "add_entity"):
                self.context.add_entity(target_type, target)

        # 4. Gather Context Graph Data for Provider
        context_data = {}
        if self.context and hasattr(self.context, "data"):
            context_data = self.context.data

        # 5. Generate Response via Active Provider
        # Re-check provider availability if not embedded
        if self.active_provider != self.embedded_engine and not self.active_provider.is_available():
            self.active_provider = self.embedded_engine

        try:
            response_text = self.active_provider.generate_response(
                user_prompt=raw_text,
                conversation_history=self.memory.get_recent_history(),
                context_data=context_data,
                system_prompt=MachinePersona.SYSTEM_PROMPT
            )
            if response_text.startswith("[") and "Error" in response_text:
                # Fallback to embedded cognitive engine on API errors
                self.active_provider = self.embedded_engine
                response_text = self.embedded_engine.generate_response(
                    user_prompt=raw_text,
                    conversation_history=self.memory.get_recent_history(),
                    context_data=context_data,
                    system_prompt=MachinePersona.SYSTEM_PROMPT
                )
        except Exception:
            self.active_provider = self.embedded_engine
            response_text = self.embedded_engine.generate_response(
                user_prompt=raw_text,
                conversation_history=self.memory.get_recent_history(),
                context_data=context_data,
                system_prompt=MachinePersona.SYSTEM_PROMPT
            )

        # 6. Record Assistant Response in Memory
        self.memory.add_assistant_message(response_text, metadata={"provider": self.active_provider.provider_name})

        # 7. Formulate Suggested Action Command
        suggested_command = None
        if intent_res.entities and intent_res.action_hint:
            target = intent_res.entities[0]
            if intent_res.intent_type == "INVESTIGATE":
                suggested_command = f"whois {target}" if "." in target else f"footprint {target}"
            elif intent_res.intent_type == "INFER":
                suggested_command = f"nexus infer {target}"
            elif intent_res.intent_type == "SUMMARY":
                suggested_command = f"nexus summary {target}"
            elif intent_res.intent_type == "BRIDGE" and len(intent_res.entities) >= 2:
                suggested_command = f"nexus bridge {intent_res.entities[0]} {intent_res.entities[1]}"

        return {
            "response": response_text,
            "intent": intent_res.to_dict(),
            "provider": self.active_provider.provider_name,
            "active_target": self.memory.active_target,
            "suggested_command": suggested_command,
        }
