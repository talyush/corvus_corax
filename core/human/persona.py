"""Corvus Corax v1.3 - Persona Analysis Engine.

Extracts observable communication habits, register choices, technical depth,
and interaction tone without clinical labeling.
"""
import re
from typing import Dict, Any, List, Optional


class PersonaAnalyzer:
    """İletişim ve Persona Tercihleri Analizörü."""

    def analyze_persona(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        combined = " ".join(texts)
        if not combined.strip():
            return self._default_persona()

        lower = combined.lower()
        words = re.findall(r'\b\w+\b', lower)
        total_words = max(1, len(words))

        # 1. Teknik Derinlik Seviyesi (Technical Vocabulary Density)
        tech_terms = {
            "api", "dns", "ip", "asn", "tls", "ssl", "sql", "linux", "python", "server",
            "database", "network", "router", "kernel", "payload", "cipher", "hash", "git",
            "docker", "kubernetes", "vulnerability", "patch", "auth", "token", "jwt", "endpoint"
        }
        tech_hits = sum(1 for w in words if w in tech_terms)
        tech_density = tech_hits / total_words

        if tech_density > 0.05:
            tech_level = "İleri Düzey Teknik / Mühendislik"
        elif tech_density > 0.015:
            tech_level = "Orta Düzey / Teknolojiye Aşina"
        else:
            tech_level = "Genel / Sivil Dil"

        # 2. İletişim Tonu ve Kaydı (Formality & Register)
        formal_markers = ["saygılarımla", "arz ederim", "bilgilerinize", "sayın", "beyefendi", "hanımefendi", "regards", "sincerely", "dear", "sir", "madam"]
        informal_markers = ["selam", "naber", "kanka", "eyvallah", "sa", "as", "bro", "dude", "hey", "sup", "lol", "haha", "yoo"]
        
        formal_hits = sum(1 for w in words if w in formal_markers)
        informal_hits = sum(1 for w in words if w in informal_markers)

        if formal_hits > informal_hits:
            tone = "Resmi / Kurumsal"
        elif informal_hits > formal_hits:
            tone = "Samimi / Gayriresmi"
        else:
            tone = "Nötr / Profesyonel"

        # 3. Hitap Biçimi ve Diyalog Dinamiği
        direct_commands = len(re.findall(r'\b(yap|getir|bak|incele|gönder|aç|kapat|do|get|check|run|send)\b', lower))
        polite_requests = len(re.findall(r'\b(lütfen|rica|mümkünse|edebilir misiniz|please|could you|kindly)\b', lower))

        if direct_commands > polite_requests * 2:
            interaction_style = "Doğrudan / Talimat Odaklı"
        elif polite_requests > 0:
            interaction_style = "Nezaket / Rica Odaklı"
        else:
            interaction_style = "Bilgi Alışverişi / Düz Anlatım"

        return {
            "technical_depth": tech_level,
            "technical_term_ratio": round(tech_density, 3),
            "communication_tone": tone,
            "interaction_style": interaction_style,
            "sample_size_words": total_words,
            "sample_size_messages": len(texts),
        }

    def _default_persona(self) -> Dict[str, Any]:
        return {
            "technical_depth": "Bilinmiyor (Yetersiz Veri)",
            "technical_term_ratio": 0.0,
            "communication_tone": "Nötr",
            "interaction_style": "Bilinmiyor",
            "sample_size_words": 0,
            "sample_size_messages": 0,
        }
