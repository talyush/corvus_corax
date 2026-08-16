"""Corvus Corax Intelligence Enrichment Capability.

Gravatar MD5 avatar hash çözümleme ve kamuya açık OSINT veri zenginleştirme yeteneği.
"""
import hashlib
import json
import urllib.request


class EnrichmentCapability:
    """Kamuya açık profil ve avatar zenginleştirme yeteneği."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CorvusCorax/0.9.1"

    @staticmethod
    def get_gravatar_hash(email: str) -> str:
        """E-posta adresinin MD5 Gravatar karmasını hesaplar."""
        clean_email = email.strip().lower()
        return hashlib.md5(clean_email.encode("utf-8")).hexdigest()

    @staticmethod
    def check_gravatar_profile(email: str, timeout: float = 5.0) -> dict:
        """E-posta adresinin Gravatar üzerinde kayıtlı bir hesabı/profili var mı kontrol eder."""
        grav_hash = EnrichmentCapability.get_gravatar_hash(email)
        url = f"https://www.gravatar.com/{grav_hash}.json"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": EnrichmentCapability.USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_json = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(raw_json)

            entry = data.get("entry", [{}])[0]
            display_name = entry.get("displayName") or entry.get("preferredUsername", "")
            about_me = entry.get("aboutMe", "")
            current_location = entry.get("currentLocation", "")
            profile_url = entry.get("profileUrl", f"https://gravatar.com/{grav_hash}")

            return {
                "status": "found",
                "email": email,
                "gravatar_hash": grav_hash,
                "display_name": display_name,
                "about_me": about_me,
                "location": current_location,
                "profile_url": profile_url,
            }
        except Exception:
            return {
                "status": "not_found",
                "email": email,
                "gravatar_hash": grav_hash,
                "profile_url": f"https://www.gravatar.com/avatar/{grav_hash}",
            }
