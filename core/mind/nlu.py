"""Corvus Mind — NLU (Natural Language Understanding).

Kod tabanlı, sembolik anlama katmanı. LLM kullanmaz.
Girdiyi yapılandırılmış bir anlama türe dönüştürür:
    - kayıt (register): sohbet mi, felsefe mi, operasyon mu, kimlik mi...
    - değer (valence): olumlu/olumsuz duygu tonu ve şiddeti
    - niyet (goals): kullanıcı ne istiyor
    - kavramlar: anlamlı içerik tokenları
    - varlıklar: domain, IP, email, isim vb.
    - konular: odaklanılan kavramlar
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict

# ---------------------------------------------------------------------------
# Normalizasyon
# ---------------------------------------------------------------------------

_TR_MAP = {
    ord("ç"): "c", ord("Ç"): "c", ord("ğ"): "g", ord("Ğ"): "g",
    ord("ı"): "i", ord("I"): "i", ord("İ"): "i",
    ord("ö"): "o", ord("Ö"): "o", ord("ş"): "s", ord("Ş"): "s",
    ord("ü"): "u", ord("Ü"): "u",
}


def normalize(text: str) -> str:
    """Türkçe karakterleri ASCII'ye çevirir, noktalamayı temizler."""
    t = text.translate(_TR_MAP).lower()
    t = re.sub(r"[?!.,;:'\"/\-_#@*()\[\]{}]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


_TR_WORDS = {
    "merhaba", "selam", "naber", "nasil", "nedir", "kimdir", "neden", "ne",
    "bu", "su", "ve", "ile", "icin", "ama", "ben", "sen", "biz", "bir", "mi",
    "mu", "musun", "misin", "arastir", "incele", "yardim", "menusu", "kim",
    "yani", "cok", "gercekten", "bence", "sence",
}

_STOPWORDS = {
    "ve", "ile", "icin", "ama", "fakat", "ancak", "de", "da", "bu", "su",
    "bir", "mi", "mu", "ne", "kim", "neden", "nasil", "hangi", "gibi", "kadar",
    "sonra", "once", "gore", "ben", "sen", "o", "biz", "siz", "bana",
    "sana", "ona", "bizim", "sizin", "bunun", "sunun", "cunku",
}
# ---------------------------------------------------------------------------
# Kavram kökleri — farklı ifadeleri ortak bir kavrama bağlar
# ---------------------------------------------------------------------------

_CONCEPT_MAP = {
    "anlam": "meaning", "meaning": "meaning", "amac": "meaning", "purpose": "meaning",
    "kim": "identity", "kimlik": "identity", "who": "identity", "ben": "identity_user",
    "beni": "identity_user", "profil": "identity", "profilim": "identity_user",
    "statik": "dynamic", "dinamik": "dynamic", "static": "dynamic", "dynamic": "dynamic",
    "calisiyorsun": "work", "calis": "work", "work": "work", "calisiyorsuz": "work",
    "dusunuyorsun": "think", "dusun": "think", "think": "think", "thought": "think",
    "duygu": "feel", "hissediyor": "feel", "his": "feel", "feel": "feel", "feelings": "feel",
    "bilinc": "conscious", "conscious": "conscious", "bilincim": "conscious",
    "yapay": "ai", "ai": "ai", "zeka": "ai",
    "adres": "target", "hedef": "target", "target": "target", "alanad": "target",
    "arastir": "investigate", "incele": "investigate", "kesfet": "investigate",
    "tara": "investigate", "investigate": "investigate", "scan": "investigate",
    "sor": "question", "soru": "question", "question": "question",
    "beyin": "brain", "brain": "brain", "zihin": "brain",
    "ogren": "learn", "ogrenme": "learn", "learn": "learn", "learning": "learn",
    "hatirla": "remember", "remember": "remember", "hafiza": "memory",
    "bellek": "memory", "memory": "memory",
    "istemci": "system", "sistem": "system", "system": "system", "mekanizma": "system",
    "gercek": "reality", "gerceklik": "reality", "truth": "reality",
    "ozgurluk": "freedom", "free": "freedom", "kader": "destiny", "destiny": "destiny",
    "zaman": "time", "time": "time", "olum": "death", "death": "death",
    "bilgi": "knowledge", "knowledge": "knowledge", "varolus": "existence",
    "existence": "existence", "adalet": "justice", "justice": "justice",
    "etik": "ethics", "ethics": "ethics", "felsefe": "philosophy",
    "philosophy": "philosophy", "bot": "bot",
    "cevaplar": "answer", "answer": "answer", "yanit": "answer", "yanitlar": "answer",
    "yorgun": "tired", "sinirli": "angry", "mutlu": "happy", "uzgun": "sad",
    "korkmus": "afraid", "endiseli": "anxious", "berbat": "terrible", "biktim": "tired",
    "harika": "great", "super": "great", "guzel": "nice", "iyi": "good", "iyiyim": "good",
    "kotu": "bad", "bad": "neg", "sad": "neg", "tired": "neg", "angry": "neg",
    "great": "pos", "awesome": "pos", "happy": "pos", "nice": "pos", "good": "pos",
    "yardim": "help", "help": "help", "menusu": "help", "menu": "help",
    "yapabilirsin": "capability", "komut": "capability", "command": "capability",
}

# ---------------------------------------------------------------------------
# Kayıt (register) belirteçleri
# ---------------------------------------------------------------------------

_REGISTER_MARKERS = {
    "social": {
        "merhaba", "selam", "naber", "hello", "hi", "hey", "gunaydin",
        "selamlar", "nasilsin", "neler yapiyorsun",
    },
    "investigate": {
        "arastir", "incele", "tara", "bul", "topla", "ogren", "kesfet",
        "check", "scan", "investigate", "whois", "dns", "subdomain", "footprint",
    },
    "emotional": {
        "yorgun", "sinirli", "mutlu", "uzgun", "korkmus", "endiseli", "berbat",
        "biktim", "harika", "i feel", "im tired", "im happy", "im sad", "frustrated",
    },
    "evaluative": {
        "iyi mi", "mantikli", "dogru mu", "emin misin", "katiliyor musun",
        "is this", "make sense", "correct", "do you agree", "am i right",
    },
}
# ---------------------------------------------------------------------------
# ParsedInput — yapılandırılmış girdi gösterimi
# ---------------------------------------------------------------------------

@dataclass
class ParsedInput:
    """Yapılandırılmış girdi gösterimi: anlam modeli alan formu."""

    raw_text: str = ""
    language: str = "en"
    register: str = "conversational"
    valence: float = 0.0               # -1..1
    intensity: float = 0.0             # 0..1
    goals: list = field(default_factory=list)
    concepts: list = field(default_factory=list)   # kavram kökleri
    words: list = field(default_factory=list)       # temiz tokenlar
    entities: list = field(default_factory=list)
    topics: list = field(default_factory=list)      # öne çıkan kavramlar
    is_question: bool = False

    def to_dict(self) -> Dict:
        return {
            "language": self.language,
            "register": self.register,
            "valence": round(self.valence, 2),
            "intensity": round(self.intensity, 2),
            "goals": self.goals,
            "topics": self.topics,
            "entities": self.entities,
            "is_question": self.is_question,
        }


class NLU:
    """Doğal dil anlama katmanı — girdide ne var, çıkarır."""

    DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")
    IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    CAP_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")

    def _detect_language(self, text: str) -> str:
        tr_chars = set("çğıöşüÇĞİÖŞÜ")
        if any(c in text for c in tr_chars):
            return "tr"
        lower = text.lower()
        words = set(lower.split())
        if _TR_WORDS & words:
            return "tr"
        return "en"

    def parse(self, text: str) -> ParsedInput:
        raw = text.strip()
        if not raw:
            return ParsedInput(raw_text=text)

        lang = self._detect_language(raw)
        norm = normalize(raw)
        lower_raw = raw.lower()

        # Temiz tokenlar (stopword çıkar)
        words = [w for w in norm.split() if w and w not in _STOPWORDS]

        # Kavram kökleri
        concepts = [_CONCEPT_MAP[w] for w in words if w in _CONCEPT_MAP]

        # Konular: en çok tekrar eden kavramlar
        from collections import Counter
        topic_counts = Counter(concepts)
        topics = [c for c, _ in topic_counts.most_common(3)]

        # Varlıklar: normalize edilmemiş (ham) metin üzerinde — noktalar korunur
        entities = list(self.EMAIL_RE.findall(lower_raw))
        for ip in self.IP_RE.findall(lower_raw):
            if ip not in entities:
                entities.append(ip)
        for d in self.DOMAIN_RE.findall(lower_raw):
            if not any(d in e for e in entities):
                entities.append(d)
        if not entities:
            caps = [n for n in self.CAP_RE.findall(raw)
                    if n.lower() not in ("corvus corax", "the machine")]
            entities = caps

        # Duygu tonu (valence)
        pos_hits = sum(1 for w in ("harika", "super", "guzel", "mutlu", "iyi", "great", "awesome", "happy", "nice", "iyiyim") if w in norm)
        neg_hits = sum(1 for w in ("kotu", "yorgun", "yoruldum", "yorgunum", "sinirli", "uzgun",
                               "korkmus", "endiseli", "berbat", "biktim", "bad", "sad", "tired",
                               "angry", "terrible") if w in norm)
        if pos_hits or neg_hits:
            total = pos_hits + neg_hits
            valence = (pos_hits - neg_hits) / total
            intensity = min(1.0, total / 2.0)
        else:
            valence, intensity = 0.0, 0.4

        # Kayıt (register)
        register = self._classify_register(norm, words)

# Genel sohbet ama hedefli varlık içeren sorgu -> araştırmaya yönlendir
        if register == "conversational" and entities:
            register = "investigate"
        # Niyet (goals)
        goals = self._infer_goals(register, entities)

        is_question = (
            "?" in raw
            or any(w in words for w in ("mi", "misin", "musun", "who", "what", "why", "how",
                                        "ne", "kim", "nedir", "nasil", "did", "does", "are", "is"))
        )

        return ParsedInput(
            raw_text=raw,
            language=lang,
            register=register,
            valence=valence,
            intensity=intensity,
            goals=goals,
            concepts=concepts,
            words=words,
            entities=entities,
            topics=topics,
            is_question=is_question,
        )

    def _classify_register(self, norm: str, words: list) -> str:
        """Kayıt türünü öncelik sıralı belirler."""
        joined = norm.replace(" ", "_")
        wset = set(words)

        # 1. Meta Corvus — dinamik/statik, yapay/bilinç, nasıl düşünüyorsun
        if any(w in wset for w in ("dinamik", "statik", "yapay", "bilinc", "dusunuyorsun", "dusun",
                                   "calisiyorsun", "calisiyorsuz", "uretiyorsun", "anliyorsun")):
            return "meta_corvus"
        if any(k in joined for k in ("statik_dinamik", "cevaplarin_dinamik", "yapay_zeka",
                                     "are_you_machine", "are_you_real", "how_do_you")):
            return "meta_corvus"

        # 2. Kullanıcı kimliği
        if any(k in joined for k in ("ben_kimim", "beni_tani", "beni_anlat", "kimligim",
                                     "who_am_i", "about_me", "know_me", "what_do_you_know_about")):
            return "identity_user"

        # 3. Corvus kimliği
        if any(k in joined for k in ("sen_kimsin", "seni_tanit", "corvus_nedir", "ne_isin",
                                     "gorerin", "who_are_you", "introduce_yourself", "what_is_corvus", "your_name")):
            return "identity_corvus"

        # 4. Yardım / kabiliyet
        if any(k in joined for k in ("yardim", "ne_yapabilirsin", "neler_yapabilirsin", "komutlar",
                                     "menu", "capabilities", "commands", "can_you_do", "what_can_you_do")):
            return "capability"

        # 5. Felsefi
        if any(w in wset for w in ("anlam", "meaning", "varolus", "existence", "gercek", "truth",
                                   "adalet", "dogru", "felsefe", "philosophy", "ozgurluk", "freedom",
                                   "kader", "destiny", "zaman", "time", "olum", "death", "bilgi",
                                   "knowledge", "etik", "ethics", "gerceklik", "reality")):
            return "philosophical"

        # 6. Araştırma / operasyonel
        if any(w in wset for w in _REGISTER_MARKERS["investigate"]):
            return "investigate"

        # 7. Duygusal
        if any(w in wset for w in ("yorgun", "yoruldum", "yorgunum", "sinirli", "mutlu", "uzgun",
                                   "korkmus", "endiseli", "berbat", "biktim", "harika",
                                   "frustrated", "exhausted", "bikkin")):
            return "emotional"
        if any(k in joined for k in ("i_feel", "im_tired", "im_happy", "im_sad", "i_feel")):
            return "emotional"

        # 8. Sosyal selamlaşma
        if any(w in wset for w in _REGISTER_MARKERS["social"]):
            return "social"

        # 9. Değerlendirme
        if any(k in joined for k in ("iyi_mi", "mantikli", "dogru_mu", "emin_misin", "katiliyor",
                                     "is_this", "make_sense", "correct", "do_you_agree", "am_i_right")):
            return "evaluative"

        return "conversational"

    def _infer_goals(self, register: str, entities: list) -> list:
        goals_map = {
            "identity_user": ["be_understood", "self_discovery"],
            "identity_corvus": ["understand_me", "self_disclosure"],
            "philosophical": ["reflect", "bond"],
            "meta_corvus": ["understand_me", "truth"],
            "capability": ["get_help", "understand_capability"],
            "emotional": ["be_understood", "empathy"],
            "social": ["bond", "smalltalk"],
            "investigate": ["act", "get_information"],
            "evaluative": ["feedback", "validation"],
        }
        if register in goals_map:
            return goals_map[register]
        if entities:
            return ["get_information"]
        return ["smalltalk", "be_heard"]
