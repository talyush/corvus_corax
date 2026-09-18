"""Corvus Corax v1.1.2 - Cognitive Dialogue Engine.

Central orchestrator for the Cognitive Interface & Conversational Agent:
- Memory management & reference resolution.
- Intent & entity extraction.
- Automatic cognitive provider selection via ProviderRouter
  ("many models, one mind interface" — provider changes, mind never changes).
- ContextManager graph bidirectional synchronization.
"""

from typing import Dict, Any, Optional
from .memory import ConversationMemory
from .intent import IntentExtractor, IntentResult
from .persona import MachinePersona
from .providers.local_engine import EmbeddedCognitiveEngine
from .providers.registry import ProviderRegistry
from .providers.router import ProviderRouter
from .providers.interface import Capability


class CognitiveDialogueEngine:
    """Bilişsel Diyalog ve Doğal Dil Arayüz Motoru."""

    def __init__(self, context_manager=None):
        self.context = context_manager
        self.memory = ConversationMemory()
        self.intent_extractor = IntentExtractor()
        self.registry = ProviderRegistry()
        self.router = ProviderRouter(registry=self.registry)
        self.embedded_engine = self.registry.get("embedded_core")
        self.active_provider = self.registry.by_priority()[0] if self.registry.by_priority() else self.embedded_engine

    def _select_best_provider(self):
        """Geriye uyumluluk: artık registry priority'sine göre."""
        return self.active_provider

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

        # 5. Generate Response via Provider Router ("many models, one mind")
        # Derin/felsefi sorular LLM'e gider (deep capability), basit sohbet sembolik kalır
        # (hızlı). Router, gerekli capability'e sahip sağlayıcıyı fallback zinciriyle bulur;
        # hiçbiri yoksa/başarısızsa Corvus Mind (embedded_core) asla değişmez.
        word_count = len(raw_text.split())
        deep_questions = any(k in raw_text.lower() for k in (
            "nedir", "kimdir", "neden", "nasıl", "nasil", "anlam", "felsefe",
            "düşün", "düşünüyor", "hakkında ne", "arasındaki fark", "yorumla",
            "what is", "why", "how", "meaning", "philosophi", "think about",
        ))
        with_cap = Capability.DEEP if (intent_res.intent_type == "INFER" or
                                       (deep_questions and word_count >= 5)) else Capability.FAST

        result = self.router.route(
            user_prompt=raw_text,
            conversation_history=self.memory.get_recent_history(),
            context_data=context_data,
            system_prompt=MachinePersona.SYSTEM_PROMPT,
            with_cap=with_cap,
        )
        response_text = result.text
        provenance = result.to_dict()

        # 6. Record Assistant Response in Memory (provenance ile)
        mem_meta = {"provider": provenance.get("provider_name"),
                    "request_id": provenance.get("request_id"),
                    "fallback_chain": provenance.get("fallback_chain")}
        self.memory.add_assistant_message(response_text, metadata=mem_meta)

        # 7. Formulate Suggested Action Command
        suggested_command = None
        if intent_res.entities and intent_res.action_hint:
            target = intent_res.entities[0]
            if intent_res.intent_type == "INVESTIGATE":
                # Faz C: otonom ajan akışı — plan + onay + gözlem döngüsü
                suggested_command = f"agent {target}"
            elif intent_res.intent_type == "INFER":
                suggested_command = f"nexus infer {target}"
            elif intent_res.intent_type == "SUMMARY":
                suggested_command = f"nexus summary {target}"
            elif intent_res.intent_type == "BRIDGE" and len(intent_res.entities) >= 2:
                suggested_command = f"nexus bridge {intent_res.entities[0]} {intent_res.entities[1]}"

        return {
            "response": response_text,
            "intent": intent_res.to_dict(),
            "provider": (provenance or {}).get("provider_name") or self.active_provider.provider_name,
            "provenance": provenance,
            "active_target": self.memory.active_target,
            "suggested_command": suggested_command,
        }
