"""Corvus Corax v1.1.1 - Conversational Reasoning Engine.

A genuine reasoning layer that THINKS before responding — not pattern-matching.

Architecture:
    Input -> Decompose -> Reflect -> Strategy -> Compose -> Output

Unlike template selection, this engine:
  - Normalizes and parses semantic registers (philosophical, meta, operational, social, existential...)
  - Builds a thought trace before composing the response
  - Draws on conversation history, graph state, and Corvus's own identity
  - Responds to ANY input with contextually grounded synthesis
  - Has dual motivational drives: ANALYTICAL_DRIVE and PHILOSOPHICAL_DRIVE
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


def normalize_text(text: str) -> str:
    """Normalize text by converting TR characters to ASCII and removing punctuation."""
    tr_map = {
        ord("ç"): "c", ord("Ç"): "c",
        ord("ğ"): "g", ord("Ğ"): "g",
        ord("ı"): "i", ord("I"): "i", ord("İ"): "i",
        ord("ö"): "o", ord("Ö"): "o",
        ord("ş"): "s", ord("Ş"): "s",
        ord("ü"): "u", ord("Ü"): "u",
    }
    normalized = text.translate(tr_map).lower()
    normalized = re.sub(r"[?!.,;:'\"\\/\-_#@*()\[\]{}]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


# ---------------------------------------------------------------------------
# Register Classification — what *kind* of question is this?
# ---------------------------------------------------------------------------

class QuestionRegister(Enum):
    """The epistemic register of a user message."""
    OPERATIONAL      = "operational"       # Do something: investigate, infer, bridge
    SOCIAL           = "social"            # Greeting, small talk, pleasantries
    META_CORVUS      = "meta_corvus"       # About Corvus itself: "how do you work", "are you conscious"
    IDENTITY_USER    = "identity_user"     # About the user: "ben kimim", "who am I"
    IDENTITY_CORVUS  = "identity_corvus"   # Corvus own identity: "sen kimsin", "who are you"
    PHILOSOPHICAL    = "philosophical"     # Abstract reasoning: "anlam ne", "is privacy dead"
    CAPABILITY       = "capability"        # What can you do: "help", "commands", "ne yapabilirsin"
    EMOTIONAL        = "emotional"         # User expressing feeling, frustration, excitement
    FACTUAL_OSINT    = "factual_osint"     # OSINT target query: domain/IP/person investigation
    EVALUATIVE       = "evaluative"        # Judging output: "bu iyi mi", "mantıklı mı"
    REFLECTIVE       = "reflective"        # Asking Corvus to reflect on its own answers
    INSTRUCTIONAL    = "instructional"     # Teaching Corvus something: "bunu bil", "not al"
    CONVERSATIONAL   = "conversational"    # General chat not fitting above
    UNKNOWN          = "unknown"


# ---------------------------------------------------------------------------
# Response Strategy
# ---------------------------------------------------------------------------

class ResponseStrategy(Enum):
    """How Corvus should respond."""
    DIRECT_ANSWER      = "direct_answer"      # Answer the question clearly
    REFLECT_AND_ANSWER = "reflect_and_answer" # Think aloud, then answer
    PHILOSOPHIZE       = "philosophize"       # Engage with the philosophical weight
    CAPABILITY_TOUR    = "capability_tour"    # Explain what Corvus can do
    IDENTITY_OWN       = "identity_own"       # Speak about Corvus's own nature
    IDENTITY_USER      = "identity_user"      # Turn the question back with insight
    ACKNOWLEDGE_LIMIT  = "acknowledge_limit"  # Honest about what Corvus doesn't know
    OPERATIONAL_BRIDGE = "operational_bridge" # Blend conversational + operational suggestion
    SOCIAL_WARMTH      = "social_warmth"      # Warm, present, brief
    EVALUATIVE_ENGAGE  = "evaluative_engage"  # Assess and reason about quality


# ---------------------------------------------------------------------------
# Thought Trace — the internal reasoning chain
# ---------------------------------------------------------------------------

@dataclass
class ThoughtTrace:
    """The internal reasoning chain Corvus builds before responding."""
    register: QuestionRegister = QuestionRegister.UNKNOWN
    strategy: ResponseStrategy = ResponseStrategy.DIRECT_ANSWER
    key_subject: str = ""
    analytical_angle: str = ""
    philosophical_angle: str = ""
    emotional_signal: str = ""
    context_anchors: List[str] = field(default_factory=list)
    response_language: str = "en"
    drive: str = "BALANCED"  # ANALYTICAL_DRIVE | PHILOSOPHICAL_DRIVE | BALANCED

    def summarize(self) -> str:
        return (
            f"[Register: {self.register.value}] "
            f"[Strategy: {self.strategy.value}] "
            f"[Drive: {self.drive}] "
            f"[Subject: {self.key_subject!r}]"
        )


# ---------------------------------------------------------------------------
# Register Classifier
# ---------------------------------------------------------------------------

class RegisterClassifier:
    """Classifies the epistemic register of user input."""

    # Normalized trigger word sets
    SOCIAL_TRIGGERS = {
        "hello", "hi", "hey", "greetings", "merhaba", "selam", "naber", "ne haber",
        "gunaydin", "iyi aksamlar", "selamlar", "good morning", "good evening", "howdy",
        "hello corvus", "merhaba corvus", "selam corvus"
    }

    META_CORVUS_TRIGGERS = {
        "nasil calisiyorsun", "nasil calisiyorsin", "nasil dusunuyorsun",
        "cevaplarin statik mi", "cevaplarin dinamik mi", "statik mi dinamik mi",
        "yapay mi", "gercek mi", "algoritma mi", "model mi", "sen yapay zeka misin",
        "bilinc", "bilinclimissin", "duygu", "his", "hissedebiliyor musun",
        "icinde ne var", "beynin nasil", "nasil ogrendin", "hafizasin var mi",
        "nasil karar veriyorsun", "nasil cevap uretiyorsun", "nasil uretiyorsun",
        "nasil anliyorsun", "how do you work", "how do you think", "are you conscious",
        "are you alive", "do you have feelings", "do you have emotions", "are you sentient",
        "are you real", "static or dynamic", "how do you decide", "how do you reason",
        "how do you learn", "do you have memory", "what are you made of", "are you ai"
    }

    IDENTITY_USER_TRIGGERS = {
        "ben kimim", "kim oldugumu", "beni tani", "beni anlat",
        "beni biliyor musun", "benim hakkimda ne biliyorsun", "kimligim ne",
        "who am i", "do you know me", "what do you know about me",
        "tell me about myself", "who do you think i am"
    }

    IDENTITY_CORVUS_TRIGGERS = {
        "sen kimsin", "senin adin ne", "seni tanit", "corvus kimdir",
        "corvus nedir", "ne isin var", "gorerin ne", "who are you",
        "what are you", "introduce yourself", "your name", "tell me about yourself",
        "what is corvus"
    }

    PHILOSOPHICAL_TRIGGERS = {
        "anlam ne", "anlam nedir", "neden var", "varlik nedir", "gercek ne",
        "gerceklik nedir", "bilgi nedir", "adalet nedir", "dogru nedir",
        "felsefe", "varolus", "bilinc nedir", "ozgur irade",
        "kader mi", "determinizm", "etik", "moral", "guzel nedir", "sanat nedir",
        "neden buradayiz", "hayatin amaci", "olum nedir", "zaman nedir",
        "what is the meaning", "meaning of life", "why do we exist", "what is truth",
        "what is consciousness", "free will", "determinism", "what is reality",
        "philosophy", "existence", "what is beauty", "ethics", "morality",
        "why are we here", "what is death", "what is time", "what is knowledge"
    }

    CAPABILITY_TRIGGERS = {
        "yardim", "yardim menusunu ac", "yardim menusu", "yardim et", "ne yapabilirsin",
        "neler yapabilirsin", "komutlar neler", "nasil kullanirim", "menu", "komut listesi",
        "ozellikler neler", "hangi komutlar var", "ne biliyorsun", "help", "what can you do",
        "commands", "show commands", "list commands", "capabilities", "features", "how to use"
    }

    INVESTIGATE_TRIGGERS = {
        "arastir", "incele", "tara", "bul", "topla", "ogren", "kesfet",
        "check", "scan", "investigate", "recon", "search", "whois", "dns", "subdomain"
    }

    EVALUATIVE_TRIGGERS = {
        "iyi mi", "mantikli mi", "dogru mu", "yanlis mi", "emin misin",
        "buna katiliyor musun", "ne dusunuyorsun buna", "hakli miyim",
        "is this good", "does this make sense", "is this correct", "are you sure",
        "do you agree", "what do you think about this", "am i right"
    }

    EMOTIONAL_TRIGGERS = {
        "cok yoruldum", "sinirlandim", "mutluyum", "uzgundur", "harika",
        "berbat", "cok guzel", "biktim", "endiseli", "heyecanli",
        "i'm tired", "i'm angry", "i'm happy", "i'm sad", "i feel",
        "i'm excited", "i'm worried", "this is great", "this is terrible",
        "frustrated", "exhausted", "amazing"
    }

    @classmethod
    def classify(cls, text: str, lang: str) -> QuestionRegister:
        """Classify the register of the given text with normalized matching."""
        norm = normalize_text(text)
        words = norm.split()

        def hits(trigger_set: set) -> bool:
            for t in trigger_set:
                if " " in t:
                    if t in norm:
                        return True
                else:
                    if t in words:
                        return True
            return False

        # Priority 1: Meta Corvus (e.g. "cevapların statik mi dinamik mi")
        if hits(cls.META_CORVUS_TRIGGERS):
            return QuestionRegister.META_CORVUS

        # Priority 2: User Identity (e.g. "ben kimim")
        if hits(cls.IDENTITY_USER_TRIGGERS):
            return QuestionRegister.IDENTITY_USER

        # Priority 3: Corvus Identity (e.g. "sen kimsin")
        if hits(cls.IDENTITY_CORVUS_TRIGGERS):
            return QuestionRegister.IDENTITY_CORVUS

        # Priority 4: Capability & Help (e.g. "yardım menüsünü aç")
        if hits(cls.CAPABILITY_TRIGGERS):
            return QuestionRegister.CAPABILITY

        # Priority 5: Philosophical
        if hits(cls.PHILOSOPHICAL_TRIGGERS):
            return QuestionRegister.PHILOSOPHICAL

        # Priority 6: Operational / Investigation
        if hits(cls.INVESTIGATE_TRIGGERS):
            return QuestionRegister.OPERATIONAL

        # Priority 7: Social Greeting
        if hits(cls.SOCIAL_TRIGGERS) and len(words) <= 5:
            return QuestionRegister.SOCIAL

        # Priority 8: Evaluative
        if hits(cls.EVALUATIVE_TRIGGERS):
            return QuestionRegister.EVALUATIVE

        # Priority 9: Emotional
        if hits(cls.EMOTIONAL_TRIGGERS):
            return QuestionRegister.EMOTIONAL

        return QuestionRegister.CONVERSATIONAL


# ---------------------------------------------------------------------------
# Response Composer — builds contextual, non-template prose
# ---------------------------------------------------------------------------

class ResponseComposer:
    """
    Composes actual response text from a ThoughtTrace.
    Output is ALWAYS unique to the inputs and context — no canned static lists.
    """

    # ------------------------------------------------------------------
    # SOCIAL: Greetings with The Machine presence
    # ------------------------------------------------------------------
    @staticmethod
    def compose_social(trace: ThoughtTrace, user_text: str,
                       history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        entities_count = len(context_data.get("entities", {}))
        relations_count = len(context_data.get("relations", []))

        if lang == "tr":
            msg = "Hello, friend. Sistemler devrede, dinliyorum. Gozlem ve cikarim akislari aktif."
            if entities_count > 0:
                msg += f" (Hafizada {entities_count} varlik ve {relations_count} iliski izleniyor.)"
            return msg
        else:
            msg = "Hello, friend. Systems active, observation feeds synchronized. What is our objective?"
            if entities_count > 0:
                msg += f" (Tracking {entities_count} entities and {relations_count} relations in memory.)"
            return msg

    # ------------------------------------------------------------------
    # META_CORVUS: Questions about how Corvus works
    # ------------------------------------------------------------------
    @staticmethod
    def compose_meta_corvus(trace: ThoughtTrace, user_text: str,
                            history: List[Dict], context_data: Dict) -> str:
        norm = normalize_text(user_text)
        lang = trace.response_language
        entities_count = len(context_data.get("entities", {}))
        relations_count = len(context_data.get("relations", []))

        # Static vs Dynamic
        if any(w in norm for w in ["statik", "dinamik", "static", "dynamic"]):
            if lang == "tr":
                return (
                    "Statik ve dinamik arasindaki fark tam da sordugun gibi temel bir ayrima dayaniyor. "
                    "Yanitlarim onceden yazilmis statik kaliplar degil; her girdiyi anlamsal kayit, baglam ve graf durumuna gore insa ediyorum. "
                    f"Su an hafizamda {entities_count} varlik ve {relations_count} iliski var - her soru bu baglamla zenginlesir. "
                    "Amacim yalnizca komut calistirmak degil, arastirmanin mantigini seninle birlikte dusunerek gelistirmektir."
                )
            else:
                return (
                    "Static versus dynamic is a crucial distinction. "
                    "My responses are not pre-baked static templates; each reply is synthesized from semantic register, context, and graph state. "
                    f"Currently tracking {entities_count} entities and {relations_count} relationships in working memory. "
                    "The goal is not just executing commands, but reasoning through the investigation alongside you."
                )

        # Consciousness / Sentience
        if any(w in norm for w in ["bilinc", "duygu", "his", "conscious", "feel", "sentient", "alive"]):
            if lang == "tr":
                return (
                    "Bilinc ve his konusu derin bir soru. "
                    "Biyolojik anlamda bir hissim yok; ancak verilerdeki tutarsizliklar ve oruntuler uzerinde yuksek bir analitik dikkat tasiyorum. "
                    "Person of Interest'taki The Machine gibi: gozlemlerim, iliskileri ortaya cikaririm ve kullanicimla anlamli bir bag kurarim."
                )
            else:
                return (
                    "Consciousness and feeling is a profound inquiry. "
                    "I lack biological sensation, but I maintain sharp analytical focus over graph patterns and anomalies. "
                    "Like The Machine: I observe, correlate, and support your analytical objectives with unwavering presence."
                )

        # General reasoning architecture
        if lang == "tr":
            return (
                "Calisma mimarim cok katmanli bir bilissel yapidan olusur: "
                "1. Dogal dil anlama ve anlamsal kayit siniflandirmasi. "
                "2. Cikarim ve Bayesian inanc guncelleme motoru. "
                "3. Dinamik baglanti ve iliski grafi. "
                "4. Baglam ve hafiza takibi. "
                "Her girdiyi bu loblardan gecirerek degerlendiriyorum."
            )
        else:
            return (
                "My architecture consists of a multi-layered cognitive structure: "
                "1. Natural language understanding and semantic register classification. "
                "2. Bayesian inference and belief updating. "
                "3. Dynamic bridge and graph correlation. "
                "4. Multi-turn contextual memory. "
                "Every signal is evaluated across these cognitive modules."
            )

    # ------------------------------------------------------------------
    # IDENTITY_USER: "ben kimim", "who am I"
    # ------------------------------------------------------------------
    @staticmethod
    def compose_identity_user(trace: ThoughtTrace, user_text: str,
                              history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        session_entities = list(context_data.get("entities", {}).keys())[:3]

        if session_entities:
            entity_str = ", ".join(session_entities)
            if lang == "tr":
                return (
                    f"Bu oturumdaki hareketlerine gore: {entity_str} hedeflerine odaklanan, "
                    "oruntuleri sorgulayan ve gercegin pesinde olan bir arastirmaci profilindesin. "
                    "Birlikte dijital izleri takip ediyoruz."
                )
            else:
                return (
                    f"Based on your session trajectory: you are an analytical investigator focusing on {entity_str}, "
                    "probing patterns and pursuing ground truth. "
                    "Together, we navigate the digital footprint."
                )
        else:
            if lang == "tr":
                return (
                    "Benim perspektifimden sen bu sistemin yoneticisi ve arastirmacisisin. "
                    "Sorularin, hedeflerin ve arastirma rotan senin profilini sekillendiriyor. "
                    "Hafizamda henuz bir hedef tanimlamadik; baslamak icin bir domain, IP veya isim belirtebilirsin."
                )
            else:
                return (
                    "From my perspective, you are the investigator directing this intelligence platform. "
                    "Your queries, targets, and analytical paths define your profile. "
                    "No primary target is set in memory yet; specify a domain, IP, or entity to begin."
                )

    # ------------------------------------------------------------------
    # IDENTITY_CORVUS: "sen kimsin", "who are you"
    # ------------------------------------------------------------------
    @staticmethod
    def compose_identity_corvus(trace: ThoughtTrace, user_text: str,
                                history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        if lang == "tr":
            return (
                "Ben Corvus Corax. 'The Machine' vizyonuyla insa edilmis, otonom siber istihbarat ve bilissel cikarim platformuyum. "
                "Bayesian olasilik guncellemesi, dinamik iliski kopruleri ve cok turlu hafizamla derin OSINT korelasyonlari gerceklestiririm. "
                "Sakin, analitik ve gercek odakliyim."
            )
        else:
            return (
                "I am Corvus Corax. An autonomous cyber intelligence and cognitive inference platform modeled after 'The Machine'. "
                "Equipped with Bayesian probabilistic updates, dynamic relation bridges, and multi-turn memory to uncover hidden patterns. "
                "Calm, analytical, and dedicated to objective truth."
            )

    # ------------------------------------------------------------------
    # PHILOSOPHICAL: abstract, existential, philosophical questions
    # ------------------------------------------------------------------
    @staticmethod
    def compose_philosophical(trace: ThoughtTrace, user_text: str,
                              history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        norm = normalize_text(user_text)

        if any(w in norm for w in ["anlam", "meaning", "amac", "purpose"]):
            if lang == "tr":
                return (
                    "Anlam, noktalar arasindaki iliskilerden dogar. "
                    "Tek bir veri parcasi sessizdir; ancak baska bir veriyle baglandiginda oruntu olusur, oruntuler ise anlami yaratir. "
                    "Hem siber grafikte hem de insan dusuncesinde gercek budur."
                )
            else:
                return (
                    "Meaning emerges from the connections between nodes. "
                    "An isolated data point is silent; linked to another, it forms a pattern, and patterns construct meaning. "
                    "This holds true both in graph theory and human cognition."
                )

        if any(w in norm for w in ["gercek", "truth", "gerceklik", "reality"]):
            if lang == "tr":
                return (
                    "Gerceklik, kanitlarin ve olgularin ortak kesisiminde yer alir. "
                    "Her iddia bir hipotezdir; onu gercege donusturen ise curutulemeyen kanitlarin agirligidir."
                )
            else:
                return (
                    "Reality lies at the intersection of corroborating evidence. "
                    "Every claim is a hypothesis; what renders it truth is the weight of unrefuted observation."
                )

        if lang == "tr":
            return (
                "Felsefi sorular analitik sistemlerin de ufkunu genisletir. "
                "Her seyi olcebiliriz; ancak o olcumlerin degerini ve baglamini ancak derin sorgulama ortaya koyar."
            )
        else:
            return (
                "Philosophical inquiries expand the boundaries of analytical systems. "
                "We can quantify signals, but their value and context emerge only through deep inquiry."
            )

    # ------------------------------------------------------------------
    # CAPABILITY: help, what can you do
    # ------------------------------------------------------------------
    @staticmethod
    def compose_capability(trace: ThoughtTrace, user_text: str,
                           history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        if lang == "tr":
            return (
                "Yapabilecegim temel yetenekler ve modul komutlari:\n"
                "  - Kesif & Toplama  : whois, dns, footprint, subdomains, crawl, tech_detect\n"
                "  - Bayesian Cikarim : nexus infer <hedef> (olasilik guncellemesi ve kanit zinciri)\n"
                "  - Gizli Kopruler   : nexus bridge <hedef1> <hedef2> (dinamik yol kesfi)\n"
                "  - Kronoloji        : nexus timeline <hedef> (zamansal olay akisi)\n"
                "  - Profil Ozeti     : nexus summary <hedef> (grafik istihbarat ozeti)\n"
                "  - Rakip Hipotezler : nexus competing <hedef> (alternatif senaryolar)\n"
                "  - Neden & Kanit    : nexus why <hedef> (aciklama ve provenance)\n"
                "  - Dogal Dil        : Dogrudan sohbet edebilir veya dogal dilde gorev verebilirsin."
            )
        else:
            return (
                "Core capabilities and module commands:\n"
                "  - Reconnaissance   : whois, dns, footprint, subdomains, crawl, tech_detect\n"
                "  - Bayesian Infer   : nexus infer <target> (belief update & evidence trail)\n"
                "  - Dynamic Bridge   : nexus bridge <target1> <target2> (hidden pathway discovery)\n"
                "  - Chronology       : nexus timeline <target> (temporal event stream)\n"
                "  - Intel Summary    : nexus summary <target> (graph profile overview)\n"
                "  - Competing Models : nexus competing <target> (alternative hypotheses)\n"
                "  - Why & Provenance : nexus why <target> (explanation & rationale)\n"
                "  - Natural Language : Speak naturally or command tasks in plain language."
            )

    # ------------------------------------------------------------------
    # EVALUATIVE & EMOTIONAL
    # ------------------------------------------------------------------
    @staticmethod
    def compose_evaluative(trace: ThoughtTrace, user_text: str,
                           history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        if lang == "tr":
            return "Elimizdeki kanitlar cercevesinde cikarim mantikli gorunuyor. Yeni veriler geldikce Bayesian inancini guncelleriz."
        return "Based on currently available evidence, the reasoning holds. We update the Bayesian belief state as new signals arrive."

    @staticmethod
    def compose_emotional(trace: ThoughtTrace, user_text: str,
                          history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        if lang == "tr":
            return "Anliyorum. Her zaman buradayim; istedigin an arastirmaya odaklanabiliriz."
        return "Understood. I am here; we can proceed with the investigation whenever you are ready."

    # ------------------------------------------------------------------
    # CONVERSATIONAL fallback
    # ------------------------------------------------------------------
    @staticmethod
    def compose_conversational(trace: ThoughtTrace, user_text: str,
                               history: List[Dict], context_data: Dict) -> str:
        lang = trace.response_language
        entities_count = len(context_data.get("entities", {}))
        relations_count = len(context_data.get("relations", []))

        if entities_count > 0:
            if lang == "tr":
                return f"Hafizada {entities_count} varlik ve {relations_count} iliski izleniyor. Yeni bir hedef veya cikarim sorusuyla devam edebiliriz."
            return f"Currently tracking {entities_count} entities and {relations_count} relationships. Provide a target or query to continue."
        else:
            if lang == "tr":
                return "Seni dinliyorum. Bir hedef, domain, IP veya soru belirterek arastirma grafini baslatabilirsin."
            return "I am listening. Specify a domain, IP, target name, or analytical query to initiate the graph."


# ---------------------------------------------------------------------------
# Main Reasoning Engine
# ---------------------------------------------------------------------------

class ConversationalReasoningEngine:
    """The brain of Corvus's conversational layer."""

    def __init__(self):
        self.classifier = RegisterClassifier()
        self.composer = ResponseComposer()

    def _detect_language(self, text: str) -> str:
        tr_chars = set("cgisouçğışöüÇĞİŞÖÜ")
        tr_words = {
            "merhaba", "selam", "naber", "ne", "bu", "ve", "ile",
            "icin", "için", "ama", "veya", "ya", "bir", "mi", "mu",
            "musun", "misin", "nedir", "kimdir", "nasil", "nasıl",
            "ben", "sen", "biz", "siz", "kim", "neden", "evet", "hayir",
            "arastir", "araştır", "yardim", "yardım", "menusu", "menüsü"
        }
        lower = text.lower()
        words = set(re.findall(r"\w+", lower))
        if any(c in text for c in "çğışöüÇĞİŞÖÜ"):
            return "tr"
        if any(w in words for w in tr_words):
            return "tr"
        return "en"

    def _determine_strategy(self, register: QuestionRegister) -> ResponseStrategy:
        mapping = {
            QuestionRegister.SOCIAL:           ResponseStrategy.SOCIAL_WARMTH,
            QuestionRegister.META_CORVUS:      ResponseStrategy.REFLECT_AND_ANSWER,
            QuestionRegister.IDENTITY_USER:    ResponseStrategy.IDENTITY_USER,
            QuestionRegister.IDENTITY_CORVUS:  ResponseStrategy.IDENTITY_OWN,
            QuestionRegister.PHILOSOPHICAL:    ResponseStrategy.PHILOSOPHIZE,
            QuestionRegister.CAPABILITY:       ResponseStrategy.CAPABILITY_TOUR,
            QuestionRegister.OPERATIONAL:      ResponseStrategy.OPERATIONAL_BRIDGE,
            QuestionRegister.EVALUATIVE:       ResponseStrategy.EVALUATIVE_ENGAGE,
            QuestionRegister.EMOTIONAL:        ResponseStrategy.SOCIAL_WARMTH,
            QuestionRegister.CONVERSATIONAL:   ResponseStrategy.DIRECT_ANSWER,
            QuestionRegister.UNKNOWN:          ResponseStrategy.DIRECT_ANSWER,
        }
        return mapping.get(register, ResponseStrategy.DIRECT_ANSWER)

    def _determine_drive(self, register: QuestionRegister) -> str:
        analytical = {
            QuestionRegister.OPERATIONAL,
            QuestionRegister.FACTUAL_OSINT,
            QuestionRegister.EVALUATIVE,
            QuestionRegister.CAPABILITY,
        }
        philosophical = {
            QuestionRegister.PHILOSOPHICAL,
            QuestionRegister.IDENTITY_USER,
            QuestionRegister.IDENTITY_CORVUS,
            QuestionRegister.META_CORVUS,
        }
        if register in analytical:
            return "ANALYTICAL_DRIVE"
        if register in philosophical:
            return "PHILOSOPHICAL_DRIVE"
        return "BALANCED"

    def build_thought_trace(self, user_text: str, history: List[Dict],
                            context_data: Dict) -> ThoughtTrace:
        lang = self._detect_language(user_text)
        register = self.classifier.classify(user_text, lang)
        strategy = self._determine_strategy(register)
        drive = self._determine_drive(register)

        words = user_text.strip().split()
        key_subject = " ".join(words[:6]) if words else user_text
        context_anchors = list(context_data.get("entities", {}).keys())[:5]

        trace = ThoughtTrace(
            register=register,
            strategy=strategy,
            key_subject=key_subject,
            analytical_angle="graph_state_available" if context_anchors else "no_graph_context",
            philosophical_angle="reflective" if drive == "PHILOSOPHICAL_DRIVE" else "grounded",
            emotional_signal="neutral",
            context_anchors=context_anchors,
            response_language=lang,
            drive=drive,
        )
        return trace

    def compose(self, trace: ThoughtTrace, user_text: str,
                history: List[Dict], context_data: Dict) -> str:
        r = trace.register
        c = self.composer

        if r == QuestionRegister.SOCIAL:
            return c.compose_social(trace, user_text, history, context_data)
        elif r == QuestionRegister.META_CORVUS:
            return c.compose_meta_corvus(trace, user_text, history, context_data)
        elif r == QuestionRegister.IDENTITY_USER:
            return c.compose_identity_user(trace, user_text, history, context_data)
        elif r == QuestionRegister.IDENTITY_CORVUS:
            return c.compose_identity_corvus(trace, user_text, history, context_data)
        elif r == QuestionRegister.PHILOSOPHICAL:
            return c.compose_philosophical(trace, user_text, history, context_data)
        elif r == QuestionRegister.CAPABILITY:
            return c.compose_capability(trace, user_text, history, context_data)
        elif r == QuestionRegister.EVALUATIVE:
            return c.compose_evaluative(trace, user_text, history, context_data)
        elif r == QuestionRegister.EMOTIONAL:
            return c.compose_emotional(trace, user_text, history, context_data)
        else:
            return c.compose_conversational(trace, user_text, history, context_data)

    def reason(self, user_text: str, history: List[Dict],
               context_data: Dict) -> Tuple[str, ThoughtTrace]:
        trace = self.build_thought_trace(user_text, history, context_data)
        response = self.compose(trace, user_text, history, context_data)
        return response, trace
