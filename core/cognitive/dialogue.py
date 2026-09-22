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

    def _system_answer(self, raw_text: str) -> str:
        """Provider/sağlık sorusuna doğal dil cevabı (LLM'siz, anında)."""
        lower = raw_text.lower()
        registry_meta = self.registry.metadata()
        available = [m for m in registry_meta if m["available"]]
        offline = [m for m in registry_meta if not m["available"]]

        tr = any(c in raw_text for c in "çğıöşü") or any(k in lower for k in ("hangi", "sağlık", "durum"))

        # Hangi modelle konuşuyorum?
        if any(k in lower for k in ("hangi modelle", "hangi model", "hangi ai", "which model",
                                     "what model", "modelle konuşuyorum", "sesin ne", "hangi zekayla", "powered by")):
            if not available:
                return ("Şu an serbest bir LLM sesim yok; konuşma motorum Corvus Mind "
                        "(gömülü beyin).") if tr else \
                    ("I currently have no external voice; my speech engine is Corvus Mind "
                     "(embedded brain).")
            voices = ", ".join(f"{m['provider_name']}" for m in available)
            if tr:
                return f"Şu an sesim: {voices}. Kimliğim (Corvus Mind) bundan bağımsız — beyin her zaman benim."
            return f"My current voice: {voices}. My identity (Corvus Mind) is independent of it — the mind is always mine."

        # Sağlık / durum
        if tr:
            lines = ["Ses sağlığı durumu:"]
            for m in registry_meta:
                mark = "✔" if m["available"] else "✘"
                lines.append(f"  {mark} {m['provider_name']} — {m['health']}")
            if offline:
                offline_names = ", ".join(m["provider_id"] for m in offline)
                lines.append(f"(kullanılamayanlar: {offline_names} — API key/bağlantı gerekli)")
            return "\n".join(lines)
        lines = ["Voice health status:"]
        for m in registry_meta:
            mark = "OK" if m["available"] else "X"
            lines.append(f"  [{mark}] {m['provider_name']} — {m['health']}")
        return "\n".join(lines)

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

        # 2b. SISTEM SORGUSU — "hangi modelle konuşuyorum / ai sağlığı nasıl / provider" 
        # gibi doğal dil soruları doğrudan provider bilgisiyle cevaplanır (LLM gerektirmez).
        sys_lower = raw_text.lower()
        ask_provider = any(k in sys_lower for k in (
            "hangi modelle", "hangi model", "hangi ai", "modelle konuşuyorum",
            "provider", "sağlayıcı", "sağlı", "saglik", "sagl", "sesin ne", "hangi zekayla",
            "who are you powered by", "what model", "which model", "durum nasıl",
            "health", "status",
        ))
        if ask_provider and ("?" in raw_text or raw_text.endswith((".", "?")) or True):
            system_answer = self._system_answer(raw_text)
            self.memory.add_assistant_message(system_answer, metadata={"category": "system_query"})
            return {
                "response": system_answer,
                "intent": intent_res.to_dict(),
                "provider": self.active_provider.provider_name,
                "provenance": {"provider": "system_status", "request_id": "sys",
                               "fallback_chain": [], "fallback_reason": ""},
                "active_target": self.memory.active_target,
                "suggested_command": None,
            }

        # 2c. HUGINN & MUNINN DUAL-RAVEN SORGULARI (v1.2)
        # "X hakkında geçmişte ne hatırlıyorsun / neden böyle düşündün / akıl yürütme / ne değişti"
        is_muninn_query = any(k in sys_lower for k in ("muninn", "hatırlıyorsun", "hatirliyorsun", "geçmişte", "gecmiste", "ne değişti", "ne degisti", "değişim", "degisim", "drift", "tarihçe", "tarihce"))
        is_huginn_query = any(k in sys_lower for k in ("huginn", "neden böyle düşündün", "neden boyle dusundun", "akıl yürütme", "akil yurutme", "neden bu karar", "açıkla", "acikla", "gerekçe", "gerekce", "why", "explain"))
        
        if (is_muninn_query or is_huginn_query) and (intent_res.entities or fallback_target):
            focal = intent_res.entities[0] if intent_res.entities else fallback_target
            from core.decision.corvus_mind import CorvusDecisionCore
            decision_core = CorvusDecisionCore(context_manager=self.context)
            
            if is_muninn_query and not is_huginn_query:
                # Muninn hafıza / değişim raporu
                if any(k in sys_lower for k in ("ne değişti", "ne degisti", "drift", "değişim", "degisim")):
                    raven_answer = decision_core.why_conclusion_changed(focal)
                    suggested = f"muninn changes {focal}"
                else:
                    raven_answer = decision_core.muninn.format_history_report(focal)
                    suggested = f"muninn history {focal}"
            elif is_huginn_query and not is_muninn_query:
                # Huginn muhakeme / gerekçelendirme raporu
                if any(k in sys_lower for k in ("neden", "why", "gerekçe", "gerekce")):
                    raven_answer = decision_core.huginn.why(focal)
                    suggested = f"huginn why {focal}"
                else:
                    raven_answer = decision_core.huginn.explain(focal)
                    suggested = f"huginn explain {focal}"
            else:
                # İkisi birlikte: Huginn & Muninn sinerjisi
                raven_answer = decision_core.explain_with_history(focal)
                suggested = f"huginn synergy {focal}"

            self.memory.add_assistant_message(raven_answer, metadata={"category": "dual_raven_query"})
            return {
                "response": raven_answer,
                "intent": intent_res.to_dict(),
                "provider": "Corvus Decision Core (Huginn & Muninn)",
                "provenance": {"provider": "dual_raven_core", "request_id": "raven",
                               "fallback_chain": [], "fallback_reason": ""},
                "active_target": focal,
                "suggested_command": suggested,
            }

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
        # CORVUS = BEYİN, ses = ALWAYS bir LLM. Sembolik sentez kapanıyor.
        # GÖREV BAZLI SEÇİM: araştırıyorum -> güçlü model (deep/code); sohbet -> uygun/general.
        # Router, task'a uygun capability'yi seçip LLM seslerini priority sırasıyla dener,
        # hepsi başarısız olursa Corvus Mind (embedded_core) son güvence olarak devralır.
        intent_to_task = {
            "INVESTIGATE": "investigate",
            "INFER": "infer",
            "BRIDGE": "infer",
            "TIMELINE": "investigate",
            "SUMMARY": "deep",
            "CHITCHAT": "general",
            "GREETING": "general",
            "HELP": "general",
        }
        task = intent_to_task.get(intent_res.intent_type, "general")

        result = self.router.route(
            user_prompt=raw_text,
            conversation_history=self.memory.get_recent_history(),
            context_data=context_data,
            system_prompt=MachinePersona.SYSTEM_PROMPT,
            task=task,
        )
        response_text = result.text
        provenance = result.to_dict()

        # 6. Record Assistant Response in Memory (provenance ile)
        mem_meta = {"provider": provenance.get("provider_name"),
                    "request_id": provenance.get("request_id"),
                    "fallback_chain": provenance.get("fallback_chain"),
                    "task": task}
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
