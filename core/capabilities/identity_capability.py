"""Corvus Corax Identity Capability.

Türkçe karakter normalizasyonu, ad/soyad mahlas (handle) permutasyonları ve e-posta kalıp üretimi.
"""
import re
import unicodedata

TR_MAP = str.maketrans({
    "ç": "c", "Ç": "C",
    "ğ": "g", "Ğ": "G",
    "ı": "i", "I": "I", "İ": "i",
    "ö": "o", "Ö": "O",
    "ş": "s", "Ş": "S",
    "ü": "u", "Ü": "U",
})


class IdentityCapability:
    """Kimlik türetme ve normalizasyon yeteneği."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Türkçe karakterleri dönüştürür ve temizler."""
        if not text:
            return ""
        text = text.translate(TR_MAP)
        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
        return text.strip()

    @staticmethod
    def parse_name(name_str: str) -> dict:
        """Ad-soyad dizgesini ad ve soyad parçalarına ayırır."""
        raw = name_str.strip()
        norm = IdentityCapability.normalize_text(raw).lower()
        parts = re.split(r"\s+", norm)

        if not parts:
            return {"first": "", "last": "", "full_norm": ""}

        if len(parts) == 1:
            return {"first": parts[0], "last": "", "full_norm": parts[0]}

        first = parts[0]
        last = parts[-1]
        middle = parts[1:-1] if len(parts) > 2 else []

        return {
            "first": first,
            "middle": middle,
            "last": last,
            "full_norm": f"{first}{last}",
            "raw": raw,
        }

    @staticmethod
    def generate_username_permutations(name_str: str) -> list:
        """Bir isim için olası kullanıcı adı (handle) varyasyonlarını üretir."""
        parsed = IdentityCapability.parse_name(name_str)
        first = parsed["first"]
        last = parsed["last"]

        if not first:
            return []

        handles = set()

        if not last:
            handles.add(first)
            handles.add(f"{first}1")
            handles.add(f"{first}_")
            return sorted(handles)

        f_init = first[0] if first else ""
        l_init = last[0] if last else ""

        # Temel kombinasyonlar
        handles.add(f"{first}{last}")
        handles.add(f"{first}.{last}")
        handles.add(f"{first}_{last}")
        handles.add(f"{first}-{last}")
        handles.add(f"{last}{first}")
        handles.add(f"{last}.{first}")
        handles.add(f"{f_init}{last}")
        handles.add(f"{f_init}.{last}")
        handles.add(f"{f_init}_{last}")
        handles.add(f"{first}{l_init}")

        # Yaygın yıl ekleri
        years = ["80", "85", "90", "95", "00", "05", "1980", "1990", "2000"]
        for yr in years:
            handles.add(f"{first}{last}{yr}")
            handles.add(f"{first}.{last}{yr}")
            handles.add(f"{first}_{last}{yr}")

        return sorted(handles)

    @staticmethod
    def generate_candidate_emails(name_str: str, domain: str = None) -> list:
        """Ad-soyad için olası e-posta adreslerini türetir."""
        handles = IdentityCapability.generate_username_permutations(name_str)
        domains = [domain.lower()] if domain else ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"]

        emails = []
        for h in handles[:10]:  # İlk 10 baskın permutasyon
            for d in domains:
                emails.append(f"{h}@{d}")

        return emails
