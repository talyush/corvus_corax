"""Corvus Corax v1.1.1 - Natural Language Intent & Entity Extraction.

Robust parser for messy, conversational, multilingual (TR/EN) queries:
Extracts intent category, focal entities, recommended tools/actions,
and sentiment/urgency without failing on slang or typographical errors.
"""
import re
from typing import List, Dict, Any, Optional


class IntentResult:
    """Ayrıştırılmış Niyet ve Varlık Sonucu."""

    def __init__(self, intent_type: str, entities: List[str], entity_types: Dict[str, str],
                 action_hint: Optional[str] = None, language: str = "tr", raw_text: str = ""):
        self.intent_type = intent_type  # GREETING, INVESTIGATE, INFER, BRIDGE, SUMMARY, TIMELINE, CHITCHAT, HELP
        self.entities = entities
        self.entity_types = entity_types
        self.action_hint = action_hint
        self.language = language
        self.raw_text = raw_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "entities": self.entities,
            "entity_types": self.entity_types,
            "action_hint": self.action_hint,
            "language": self.language,
            "raw_text": self.raw_text,
        }


class IntentExtractor:
    """Doğal Dil Niyet ve Varlık Çıkarıcı."""

    # Regex patterns for OSINT entities
    DOMAIN_REGEX = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")
    IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    GREETING_WORDS = {
        "hello", "hi", "hey", "greetings", "merhaba", "selam", "naber", "ne haber",
        "günaydın", "iyi akşamlar", "selamlar", "good morning", "good evening", "howdy"
    }

    INVESTIGATE_TRIGGERS = {
        "araştır", "arastir", "incele", "tara", "bul", "topla", "öğren", "ogren", "keşfet", "kesfet",
        "check", "scan", "investigate", "recon", "find", "search", "whois", "dns", "subdomain", "crawl"
    }

    INFER_TRIGGERS = {
        "çıkarım", "cikarim", "akıl yürüt", "akil yurut", "düşün", "dusun", "mantık", "mantik",
        "hipotez", "tahmin", "infer", "reason", "hypothesis", "bayesian", "sherlock", "analiz"
    }

    BRIDGE_TRIGGERS = {
        "köprü", "kopru", "bağlantı", "baglanti", "ilişki", "iliski", "arasında", "arasinda",
        "nasıl bağlı", "nasil bagli", "ortak", "bridge", "connect", "path", "correlation", "linked", "relation"
    }

    TIMELINE_TRIGGERS = {
        "zaman", "kronoloji", "sıra", "sira", "ne zaman", "timeline", "chronology", "sequence", "history"
    }

    SUMMARY_TRIGGERS = {
        "özet", "ozet", "rapor", "durum", "ne biliyorsun", "kimdir", "nedir", "summary", "report",
        "overview", "who is", "what is", "profile"
    }

    def extract(self, text: str, fallback_target: Optional[str] = None) -> IntentResult:
        raw_text = text.strip()
        lower = raw_text.lower()

        # 1. Detect language (Simple heuristic: TR specific chars or word match)
        tr_chars = set("çğıöşüÇĞİÖŞÜ")
        is_tr = any(c in raw_text for c in tr_chars) or any(
            w in lower for w in ["merhaba", "selam", "naber", "araştır", "ne", "bu", "ve", "ile", "için"]
        )
        lang = "tr" if is_tr else "en"

        # 2. Extract Entities
        entities = []
        entity_types = {}

        # Emails
        for em in self.EMAIL_REGEX.findall(raw_text):
            entities.append(em)
            entity_types[em] = "email"

        # IPs
        for ip in self.IP_REGEX.findall(raw_text):
            if ip not in entities:
                entities.append(ip)
                entity_types[ip] = "ip"

        # Domains (excluding matches already part of email)
        for dom in self.DOMAIN_REGEX.findall(raw_text):
            if not any(dom in em for em in entity_types if entity_types[em] == "email"):
                if dom.lower() not in ("corvus.ai", "corvus.corax"):
                    entities.append(dom)
                    entity_types[dom] = "domain"

        # If no regex entity found, check for quotes, capitalized person/org names, or fallback
        if not entities:
            # Check quoted terms "Target Alpha"
            quotes = re.findall(r'["\']([^"\']+)["\']', raw_text)
            if quotes:
                for q in quotes:
                    entities.append(q)
                    entity_types[q] = "person_or_org"
            else:
                # Check for capitalized names (e.g. 'Alexander Vance', 'Target Alpha')
                cap_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', raw_text)
                # Filter out system names
                cap_names = [n for n in cap_names if n.lower() not in ("corvus corax", "the machine", "hello friend")]
                if cap_names:
                    for cn in cap_names:
                        entities.append(cn)
                        entity_types[cn] = "person_or_org"
                elif fallback_target:
                    entities.append(fallback_target)
                    entity_types[fallback_target] = "referenced_target"

        # 3. Determine Intent
        words = set(re.findall(r"\w+", lower))
        
        # Check Greeting
        if any(w in words for w in self.GREETING_WORDS) and len(words) <= 4:
            return IntentResult("GREETING", entities, entity_types, "chat", lang, raw_text)

        # Check Bridge
        if any(w in lower for w in self.BRIDGE_TRIGGERS) and len(entities) >= 2:
            return IntentResult("BRIDGE", entities, entity_types, "nexus bridge", lang, raw_text)

        # Check Infer / Reasoning
        if any(w in lower for w in self.INFER_TRIGGERS):
            return IntentResult("INFER", entities, entity_types, "nexus infer", lang, raw_text)

        # Check Timeline
        if any(w in lower for w in self.TIMELINE_TRIGGERS):
            return IntentResult("TIMELINE", entities, entity_types, "nexus timeline", lang, raw_text)

        # Check Summary
        if any(w in lower for w in self.SUMMARY_TRIGGERS) or lower.startswith(("kimdir", "nedir", "who is", "what is")):
            return IntentResult("SUMMARY", entities, entity_types, "nexus summary", lang, raw_text)

        # Check Investigate
        if any(w in lower for w in self.INVESTIGATE_TRIGGERS) or entities:
            return IntentResult("INVESTIGATE", entities, entity_types, "recon", lang, raw_text)

        # Default: General Chat / Consultation
        return IntentResult("CHITCHAT", entities, entity_types, "chat", lang, raw_text)
