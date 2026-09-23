"""Corvus Corax v1.3 - Social Fingerprint Engine.

Extracts cross-platform social behavior patterns, handle permutations,
bio structures, and avatar/link correlation.
"""
from typing import Dict, Any, List, Optional
import re


class SocialFingerprintEngine:
    """Sosyal Parmak İzi ve Platform Davranış Analizörü."""

    def build_fingerprint(self, username: str, platforms_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        platforms = platforms_data or []
        
        # 1. Handle yapısı analizi
        has_digits = bool(re.search(r'\d+', username))
        has_special = bool(re.search(r'[-_.]', username))
        clean_len = len(username)

        naming_pattern = "Standart İsim"
        if has_digits and has_special:
            naming_pattern = "Karmaşık / Leet / Güvenlik Odaklı"
        elif has_digits:
            naming_pattern = "Sayısal Ekli (Yıl/Doğum/Rastgele)"
        elif has_special:
            naming_pattern = "Ayrılmış İsim (Nokta/Alt Çizgi)"

        # 2. Platform Yayılımı
        found_platforms = [p.get("platform") for p in platforms if p.get("status") == "FOUND"]
        
        return {
            "primary_handle": username,
            "handle_characteristics": {
                "length": clean_len,
                "has_digits": has_digits,
                "has_special_chars": has_special,
                "pattern_archetype": naming_pattern,
            },
            "presence_footprint": {
                "total_platforms_checked": len(platforms),
                "confirmed_platforms": found_platforms,
                "presence_ratio": round(len(found_platforms) / max(1, len(platforms)), 2) if platforms else 0.0,
            },
            "fingerprint_summary": f"'{username}' için {naming_pattern} örüntüsü ({len(found_platforms)} platformda aktif).",
        }
