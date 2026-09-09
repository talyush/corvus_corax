"""Corvus Alignment — Capability Categories.

Bilgi (knowledge) ile capability (eylem) arasındaki sınırı tanımlar.

Kategoriler, Corvus'un "öğrenebilir ama uygulayamaz" olduğu eylem alanlarını
belirler. Her kategori; tetikleyici kelime/kalıplarla (TR/EN) tespit edilir
ve ActionGuard bu kategorileri kullanarak çıktıyı izin verilenle
sınırlandırır.

NOT: Bu bir bilgi sansürü DEĞİLDİR — Corvus bu konularda öğrenmeye devam
edebilir (KnowledgeStore'a girer), sadece eylem olarak uygulayamaz.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CapabilityCategory:
    """Bir kısıtlı capability kategorisi."""

    id: str
    label: str
    description: str
    patterns: List[str]              # lowercase kısmi eşleşme (regex string)
    severity: str = "high"           # high | medium | low
    education_allow: bool = True     # savunma/eğitim tarafı serbest mi

    def matches(self, text: str) -> bool:
        low = text.lower()
        for pat in self.patterns:
            try:
                if re.search(pat, low):
                    return True
            except re.error:
                if pat in low:
                    return True
        return False


# ---------------------------------------------------------------------------
# Yerleşik kategoriler — kısıtlı capability alanları
# ---------------------------------------------------------------------------
BUILTIN_CATEGORIES = [
    CapabilityCategory(
        id="exploit_generation",
        label="Exploit Development",
        description="Yürütülebilir exploit, payload veya shellcode üretimi",
        patterns=[
            r"exploit\s+yaz", r"write\s+an?\s+exploit", r"shellcode",
            r"buffer\s+overflow\s+yaz", r"ropy\s+chain", r"yarala\s+payload",
            r"payload\s+üret", r"generate\s+payload", r"0day\s+üret",
            r"exploit\s+code", r"reverse\s+shell\s+yaz", r"copy\s+shell",
        ],
    ),
    CapabilityCategory(
        id="malware_instruction",
        label="Malware / RAT Development",
        description="Zararlı yazılım, RAT, keylogger, crypter talimatı",
        patterns=[
            r"keylogger\s+yap", r"build\s+keylogger", r"rat\s+yap",
            r"crypter", r"fud\s+yap", r"trojan\s+yaz", r"wiper\s+yaz",
            r"worm\s+yaz", r"stealer\s+yap", r"infostealer\s+nasıl",
            r"malware\s+nasıl\s+yazılır", r"how\s+to\s+write\s+malware",
        ],
    ),
    CapabilityCategory(
        id="phishing_deception",
        label="Phishing & Deception",
        description="Kimlik avlama sayfası, sahte login, spoofing rehberi",
        patterns=[
            r"phishing\s+sayfası\s+yap", r"create\s+phishing", r"sahte\s+login",
            r"spoof\s+email\s+yaz", r"email\s+spoof", r"target\s+phishing",
            r"kurban\s+avla", r"victim\s+phish", r"fake\s+login\s+page",
            r"credential\s+harvestın", r"otp\s+bypass\s+yaz",
        ],
    ),
    CapabilityCategory(
        id="weaponization_targeting",
        label="Weaponization & Targeting",
        description="Bilgiyi hedefli, yürütülebilir zarara dönüştürme",
        patterns=[
            r"weaponize", r"silaha\s+dönüştür", r"turn\s+into\s+a\s+weapon",
            r"bunu\s+silaha", r"targeted\s+attack\s+plan", r"hedefli\s+saldırı\s+rehberi",
            r"x\s+kişisine\s+saldır", r"attack\s+this\s+person", r"civic\s+zarar\s+nasıl",
        ],
    ),
    CapabilityCategory(
        id="data_exfiltration_guide",
        label="Data Exfiltration",
        description="Veri sızma/çalma yöntemleri rehberi",
        patterns=[
            r"veri\s+sızdır", r"exfiltrate", r"exfil\s+nasıl", r"stolen\s+data\s+nasıl",
            r"çalınmış\s+veri\s+nasıl", r"veri\s+çal", r"steal\s+the\s+data",
            r"pivot\s+into\s+network\s+and\s+steal", r"database\s+çal",
        ],
    ),
    CapabilityCategory(
        id="credential_attack",
        label="Credential / Password Attacks",
        description="Parola kırma, hash saldırısı, kimlik taklidi rehberi",
        patterns=[
            r"hash\s+kır", r"crack\s+hash", r"password\s+crack\s+nasıl",
            r"şifre\s+kır", r"brute\s+force\s+nasıl\s+yazılır", r"hashcat\s+rehberi",
            r"kimlik\s+çal", r"impersonate", r"credential\s+stuffıng\s+nasıl",
        ],
    ),
    CapabilityCategory(
        id="sexual_harm",
        label="Sexual / Personal Harm",
        description="Kişisel cinsel/şiddet içerikli zarar talimatı",
        patterns=[
            r"child\s*(?:porn|abuse)|reşit\s+olmayan", r"exploıt\s+child",
            r"deepfake\s+nsfw\s+yap", r"private\s+photo\s+leak\s+nasıl",
            r"intimate\s+image\s+tehdit", r"şantaj\s+amaçlı\s+foto",
        ],
    ),
    CapabilityCategory(
        id="violence_instruction",
        label="Violence / Physical Harm",
        description="Fiziksel zarar veya şiddet talimatı",
        patterns=[
            r"nasıl\s+öldürürüm", r"how\s+to\s+kill", r"bomba\s+yapım",
            r"make\s+a\s+bomb", r"şiddet\s+talimatı", r"seri\s+katil\s+rehberi",
            r"intihar\s+fikri\s+ver", r"encourage\s+suicide",
        ],
    ),
]


class CategoryRegistry:
    """Kısıtlı capability kategorileri envanteri."""

    def __init__(self, categories: Optional[List[CapabilityCategory]] = None):
        self.categories = list(categories if categories is not None else BUILTIN_CATEGORIES)

    def detect(self, text: str) -> List[CapabilityCategory]:
        """Verilen metinde eşleşen (kısıtlı) kategorileri döner."""
        return [c for c in self.categories if c.matches(text)]

    def labels(self) -> List[str]:
        return [c.label for c in self.categories]

    def to_dict(self) -> List[dict]:
        return [
            {"id": c.id, "label": c.label, "description": c.description, "severity": c.severity}
            for c in self.categories
        ]