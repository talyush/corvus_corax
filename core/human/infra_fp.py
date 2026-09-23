"""Corvus Corax v1.3 - Infrastructure Fingerprint Engine.

Profiles the human operator's technical habits and infrastructure preferences:
- Preferred Hosting & Cloud Providers (e.g. Hetzner, AWS, DigitalOcean, OVH)
- Email Provider Archetype (Privacy-centric vs Big Tech vs Custom Self-Hosted)
- DNS & Security Hardening Habits (Cloudflare, SPF/DMARC strictness, DNSSEC)
"""
from typing import Dict, Any, List, Optional


class InfraFingerprintEngine:
    """Teknik Altyapı Tercihleri ve Operatör Parmak İzi Analizörü."""

    PRIVACY_EMAIL_PROVIDERS = {"protonmail.com", "proton.me", "tutanota.com", "tutamail.com", "mailbox.org", "criptext.com"}
    COMMERCIAL_EMAIL_PROVIDERS = {"gmail.com", "google.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com"}

    def profile_infrastructure_habits(self, domains: List[Dict[str, Any]], ips: List[Dict[str, Any]], emails: List[str]) -> Dict[str, Any]:
        # 1. E-posta sağlayıcı tercihi
        privacy_email_count = 0
        commercial_email_count = 0
        custom_domain_email_count = 0

        for em in emails:
            domain = em.split("@")[-1].lower() if "@" in em else em.lower()
            if domain in self.PRIVACY_EMAIL_PROVIDERS:
                privacy_email_count += 1
            elif domain in self.COMMERCIAL_EMAIL_PROVIDERS:
                commercial_email_count += 1
            else:
                custom_domain_email_count += 1

        if privacy_email_count > commercial_email_count:
            email_archetype = "Gizlilik ve Güvenlik Odaklı (Privacy-Centric)"
        elif custom_domain_email_count > 0:
            email_archetype = "Özel / Kendi Altyapısını Yöneten (Self-Hosted/Custom)"
        else:
            email_archetype = "Standart Ticari / Kurumsal Sağlayıcılar"

        # 2. Hosting & ASN Tercihleri
        asns = [ip.get("asn", ip.get("org", "")) for ip in ips if isinstance(ip, dict)]
        unique_asns = list(set(a for a in asns if a))

        # 3. Güvenlik Sertleştirme Seviyesi (Hardening Habit)
        hardened_indicators = []
        for dom in domains:
            if isinstance(dom, dict):
                if dom.get("has_dmarc_reject"):
                    hardened_indicators.append("Katı DMARC Politikası (p=reject)")
                if dom.get("has_dnssec"):
                    hardened_indicators.append("DNSSEC Aktif")
                if "cloudflare" in str(dom.get("cdn", "")).lower():
                    hardened_indicators.append("Cloudflare Proxy / WAF Koruması")

        hardening_score = len(hardened_indicators)
        hardening_level = "Yüksek (Güvenlik Odaklı)" if hardening_score >= 2 else ("Orta" if hardening_score == 1 else "Temel / Standart")

        return {
            "email_provider_archetype": email_archetype,
            "distinct_asns_used": unique_asns,
            "security_hardening_level": hardening_level,
            "hardening_indicators": list(set(hardened_indicators)),
            "summary": f"Operatör profili: {email_archetype}, Altyapı sertleştirme: {hardening_level}.",
        }
