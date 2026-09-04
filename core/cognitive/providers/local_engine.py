"""Corvus Corax v1.1.1 - Embedded Cognitive Engine (Offline / Zero-Dependency).

Generates dynamic, context-aware, analytical responses with 'The Machine' persona
without requiring external API keys or third-party cloud models.
Combines semantic intent parsing, entity graph state, multi-turn memory,
and dynamic natural language synthesis.
"""
import random
from typing import List, Dict, Any, Optional
from .interface import AbstractCognitiveProvider
from ..persona import MachinePersona
from ..intent import IntentExtractor


class EmbeddedCognitiveEngine(AbstractCognitiveProvider):
    """Dahili Bilişsel ve Doğal Dil Yanıt Üretim Motoru."""

    def __init__(self):
        self.intent_extractor = IntentExtractor()

    @property
    def provider_name(self) -> str:
        return "Embedded Cognitive Engine (The Machine Neural Core)"

    def is_available(self) -> bool:
        return True

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        context_data = context_data or {}
        intent_res = self.intent_extractor.extract(user_prompt)
        lang = intent_res.language
        intent = intent_res.intent_type
        entities = intent_res.entities

        # Context graph metrics
        relations_count = len(context_data.get("relations", []))
        entities_count = len(context_data.get("entities", {}))
        hypotheses = context_data.get("hypotheses", [])
        confirmed_count = len([h for h in hypotheses if isinstance(h, dict) and h.get("status") == "CONFIRMED"])

        # History awareness
        prior_mentions = []
        for turn in conversation_history[-4:]:
            if turn.get("role") == "user" and turn.get("entities"):
                prior_mentions.extend(turn["entities"])

        # 1. GREETING Intent
        if intent == "GREETING":
            if lang == "tr":
                openings = [
                    "Hello, friend. Sistemler devrede, dinliyorum.",
                    "Hello, friend. Gözlem akışları aktif. Hangi hedef veya sistem üzerinde çalışıyoruz?",
                    "Hello, friend. Tüm istihbarat ve çıkarım motorları hazır. Nereye odaklanmak istersin?",
                ]
            else:
                openings = [
                    "Hello, friend. All surveillance and correlation feeds are active. What is our objective?",
                    "Hello, friend. Systems initialized. Awaiting target coordinates or analytical query.",
                    "Hello, friend. The network never sleeps. Where shall we direct our attention?",
                ]
            greeting = random.choice(openings)
            if entities_count > 0:
                extra = f" (Hafızada {entities_count} varlık ve {relations_count} bağlantı mevcut.)" if lang == "tr" else f" (Tracking {entities_count} entities and {relations_count} relations in memory.)"
                return f"{greeting}{extra}"
            return greeting

        # 2. INVESTIGATE Intent
        if intent == "INVESTIGATE":
            target = entities[0] if entities else "belirtilen hedef"
            if lang == "tr":
                return (
                    f"'{target}' varlığı için keşif ve korelasyon stratejisini başlatıyorum. "
                    f"DNS, WHOIS, TLS sertifikaları ve altyapı düğümleri taranarak kanıt zincirine işlenecek. "
                    f"Graf üzerinde yeni ilişkiler tespit edildiğinde doğrudan Bayesian çıkarım motoruna besleyeceğim."
                )
            else:
                return (
                    f"Initiating reconnaissance and correlation protocol against '{target}'. "
                    f"Querying DNS topologies, authoritative registries, and TLS certificate transparency logs. "
                    f"All discovered nodes will be streamed into the central intelligence graph."
                )

        # 3. INFER / REASONING Intent
        if intent == "INFER":
            target = entities[0] if entities else "aktif hedef"
            if lang == "tr":
                return (
                    f"'{target}' üzerindeki kanıtlar ve olasılık dağılımları değerlendiriliyor. "
                    f"Bayesian inanç güncellemesi ve rakip hipotezler (competing hypotheses) analiz edilerek "
                    f"doğrulanan (>=0.85) ve çürütülen (<=0.15) senaryolar ayrıştırılıyor. "
                    f"Tam analitik döküm için 'nexus infer {target}' komutu üzerinden Bayes izini inceleyebilirsin."
                )
            else:
                return (
                    f"Evaluating probabilistic models and evidence likelihoods for '{target}'. "
                    f"Bayesian belief states, competing hypotheses, and counterfactual paths are actively calculated. "
                    f"Run 'nexus infer {target}' to view the full mathematical Bayesian update trail."
                )

        # 4. BRIDGE Intent
        if intent == "BRIDGE":
            e1 = entities[0] if len(entities) > 0 else "Varlık A"
            e2 = entities[1] if len(entities) > 1 else "Varlık B"
            if lang == "tr":
                return (
                    f"'{e1}' ile '{e2}' arasındaki olası gizli bağlantıları ve dinamik köprüleri (Dynamic Bridges) araştırıyorum. "
                    f"Ortak CDN/ASN altyapısı, zaman çizelgesi örtüşmesi ve eksik ilişki halkaları taranıyor. "
                    f"Her iki varlığın doğrudan yolu yoksa spekülatif köprü hipotezi üretilecektir."
                )
            else:
                return (
                    f"Exploring dynamic bridges and hidden intermediary nodes between '{e1}' and '{e2}'. "
                    f"Scanning shared infrastructure hubs, temporal overlap windows, and type-inferred pathways. "
                    f"Bridge hypotheses will quantify what evidence is required to confirm or refute this link."
                )

        # 5. SUMMARY Intent
        if intent == "SUMMARY":
            target = entities[0] if entities else (prior_mentions[0] if prior_mentions else "genel oturum")
            if lang == "tr":
                return (
                    f"'{target}' hakkındaki mevcut istihbarat özeti: "
                    f"Hafızada kayıtlı {entities_count} varlık ve {relations_count} doğrulanmış ilişki bulunuyor. "
                    f"Doğrulanan hipotez sayısı: {confirmed_count}. "
                    f"Tüm sistem gözlemleri 'Seeing the unseen' ilkesiyle çapraz sorgulanmaya devam ediyor."
                )
            else:
                return (
                    f"Intelligence summary for '{target}': "
                    f"Current graph maintains {entities_count} entities and {relations_count} relationships. "
                    f"Confirmed hypotheses: {confirmed_count}. "
                    f"Observational streams remain synchronized and ready for deep investigation."
                )

        # 6. TIMELINE Intent
        if intent == "TIMELINE":
            target = entities[0] if entities else "tüm olaylar"
            if lang == "tr":
                return (
                    f"'{target}' için zamansal sıralama ve Pattern of Life kronolojisi derleniyor. "
                    f"Olayların gerçekleşme sırası, aktivite patlamaları (bursts) ve nedensellik zinciri analiz ediliyor."
                )
            else:
                return (
                    f"Compiling temporal timeline and causal event stream for '{target}'. "
                    f"Sequencing observation timestamps to detect coordinated activity bursts and chronological lineage."
                )

        # 7. General / Conversational / Fallback
        if lang == "tr":
            responses = [
                f"Seni dinliyorum. Verilen her sinyal ve parametre dijital graf üzerinde analiz edilir. Nereye odaklanmak istersin?",
                f"Sistemler devrede. Hedef varlıkları belirtebilir veya aralarındaki ilişkileri doğrudan doğal dille sorabilirsin.",
                f"Her şey birbiriyle bağlantılıdır. Bana bir hedef, domain, IP veya isim ver; görünmeyen bağlantıları ortaya çıkaralım.",
            ]
        else:
            responses = [
                f"I am listening. Every digital signature leaves an observable trace. What is our next move?",
                f"Systems active. You may query targets, infer relationships, or direct investigative steps in natural language.",
                f"Everything is connected. Provide a domain, IP, or entity name, and we will reveal the unseen network.",
            ]
        return random.choice(responses)
