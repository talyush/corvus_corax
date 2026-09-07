"""Corvus Corax v1.1.1 - Embedded Cognitive Engine (Offline / Deep Reasoning Core).

Generates dynamic, context-aware, analytical & philosophical responses with 'The Machine' persona.
Zero-dependency, offline-first.
Integrates:
- ConversationalReasoningEngine (Think -> Decompose -> Reflect -> Compose)
- EmotionalLayer (ANALYTICAL_DRIVE vs PHILOSOPHICAL_DRIVE, mood & tone adaptation)
- Knowledge Graph Context (entities, relations, Bayesian hypotheses)
- Multi-Turn Conversation Memory
"""
from typing import List, Dict, Any, Optional
from .interface import AbstractCognitiveProvider
from ..persona import MachinePersona
from ..intent import IntentExtractor
from ..reasoning_engine import ConversationalReasoningEngine, QuestionRegister
from ..emotional_layer import MotivationEngine


class EmbeddedCognitiveEngine(AbstractCognitiveProvider):
    """Dahili Bilisel ve Derin Akil Yurutme Yanit Uretim Motoru."""

    def __init__(self):
        self.intent_extractor = IntentExtractor()
        self.reasoning_engine = ConversationalReasoningEngine()
        self.motivation_engine = MotivationEngine()

    @property
    def provider_name(self) -> str:
        return "Embedded Cognitive Engine (The Machine Neural Core)"

    def is_available(self) -> bool:
        return True

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        context_data = context_data or {}
        raw_text = user_prompt.strip()

        # 1. Intent Extraction
        intent_res = self.intent_extractor.extract(raw_text)
        lang = intent_res.language
        intent = intent_res.intent_type
        entities = intent_res.entities

        # 2. Reasoning Engine Processing
        trace = self.reasoning_engine.build_thought_trace(raw_text, conversation_history, context_data)

        # 3. Update Emotional & Motivational State
        self.motivation_engine.evaluate_interaction(
            user_text=raw_text,
            register_val=trace.register.value,
            has_entities=bool(entities)
        )

        # 4. If intent is operational investigation / infer / bridge with targets or explicit command
        is_operational = (
            trace.register == QuestionRegister.OPERATIONAL
            or intent in ("INVESTIGATE", "INFER", "BRIDGE")
        ) and bool(entities)

        if is_operational:
            return self._compose_operational_response(intent, entities, lang, context_data)

        # 5. Otherwise generate conversational, philosophical, meta, identity, capability, or social response
        return self.reasoning_engine.compose(trace, raw_text, conversation_history, context_data)

    def _compose_operational_response(self, intent: str, entities: List[str], lang: str, context_data: Dict[str, Any]) -> str:
        """Operasyonel (kesif, cikarim, kopru) talepler icin akil yurutme ciktisi."""
        target = entities[0] if entities else "hedef"
        entities_count = len(context_data.get("entities", {}))
        relations_count = len(context_data.get("relations", []))

        if intent == "INVESTIGATE" or intent == "CHITCHAT":
            if lang == "tr":
                return (
                    f"'{target}' icin kesif ve korelasyon protokolunu baslatiyorum. "
                    f"DNS, WHOIS kayitlari, TLS sertifika seffafligi ve altyapi dugumleri taranarak kanit grafina islenecek. "
                    f"Tespit edilen her yeni dugum Bayesian hipotez motoruna beslenecektir."
                )
            else:
                return (
                    f"Initiating reconnaissance and correlation protocol against '{target}'. "
                    f"Scanning DNS topologies, authoritative registries, and TLS certificate transparency logs. "
                    f"All discovered nodes will feed the Bayesian hypothesis pipeline."
                )

        if intent == "INFER":
            if lang == "tr":
                return (
                    f"'{target}' uzerindeki kanitlar ve olasilik dagilimlari degerlendiriliyor. "
                    f"Bayesian inanc guncellemeleri, rakip hipotezler ve karsit olasiliklar hesaplaniyor. "
                    f"Detayli olasilik zincirini 'nexus infer {target}' komutuyla dogrudan inceleyebilirsin."
                )
            else:
                return (
                    f"Evaluating probabilistic models and evidence likelihoods for '{target}'. "
                    f"Bayesian belief states, competing hypotheses, and counterfactuals are actively calculated. "
                    f"Run 'nexus infer {target}' to inspect the exact belief update trail."
                )

        if intent == "BRIDGE":
            e1 = entities[0] if len(entities) > 0 else "Node A"
            e2 = entities[1] if len(entities) > 1 else "Node B"
            if lang == "tr":
                return (
                    f"'{e1}' ile '{e2}' arasindaki gizli yollari ve dinamik kopruleri (Dynamic Bridges) arastiriyorum. "
                    f"Ortak altyapi, zaman cizelgesi ortusmesi ve ara dugum hipotezleri taraniyor."
                )
            else:
                return (
                    f"Exploring dynamic bridges and hidden intermediary nodes between '{e1}' and '{e2}'. "
                    f"Scanning shared infrastructure, temporal overlap windows, and type-inferred pathways."
                )

        if lang == "tr":
            return f"'{target}' hedefi icin operasyonel surec devrede. Hafizadaki {entities_count} varlik ve {relations_count} iliskiyle capraz sorgulaniyor."
        return f"Operational protocol active for '{target}'. Cross-referencing against {entities_count} entities and {relations_count} relationships in memory."
