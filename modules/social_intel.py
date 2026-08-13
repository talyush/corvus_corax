import re
import urllib.request
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class SocialIntelModule(BaseModule):
    """
    v0.9 — Sosyal Medya İstihbarat Modülü.

    Aynı kullanıcı adının (username) birden çok platformdaki varlığını araştırır.
    ÖNEMLİ: Aynı username farklı kişilere ait olabilir — bu modül sadece
    'possible_username_match' (olası eşleşme) ilişkisi kurar, KESİN aynı kişi
    olduğunu iddia etmez. Korelasyon olasılığı config/rules.json'daki
    username_match politikasına göre hesaplanır.
    """
    name = "social"

    def _build_url(self, platform_key, platform_cfg, handle):
        """Platform URL şablonunu kullanarak profil URL'si üretir."""
        template = platform_cfg.get("url_template")
        if not template:
            return None
        return template.format(handle=handle)

    def _check_http_ok(self, url, timeout=8):
        """Belirli bir URL'nin HTTP 200 döndürüp döndürmediğini kontrol eder (HEAD isteği)."""
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": "CorvusCorax/0.9 (+https://github.com/corvus-corax/project)",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _search_platforms(self, handle, timeout=8):
        """
        Kullanıcı adını tüm platformlarda arar.
        Bazı platformlar (github, reddit, steam) HTTP HEAD ile kontrol edilebilir;
        diğerleri için sadece URL üretilir (canlı doğrulama yapılmaz).
        """
        rules = load_rules()
        platforms = rules.get("social_platforms", {})

        results = []
        for key, cfg in platforms.items():
            url = self._build_url(key, cfg, handle)
            if not url:
                continue

            # Canlı doğrulama yapılabilen platformlar
            verified = False
            if key in ("github", "reddit", "steam", "twitter", "instagram", "telegram", "tiktok"):
                verified = self._check_http_ok(url, timeout=timeout)

            results.append({
                "platform": key,
                "url": url,
                "weight": cfg.get("weight", 0.5),
                "verified": verified,
                "confidence": cfg.get("weight", 0.5) if verified else 0.0,
            })
        return results

    def _calculate_username_confidence(self, found_count, verified_count, total_platforms):
        """
        Aynı username'in kaç platformda bulunduğuna göre olasılık hesaplar.
        Politika: base_confidence + boost_per_platform * (N-1), max_confidence sınırı.
        config/rules.json'daki username_match politikası kullanılır.
        """
        rules = load_rules()
        policy = rules.get("relationship_policies", {}).get("username_match", {})
        base = policy.get("base_confidence", 0.15)
        boost = policy.get("confidence_boost_per_platform", 0.1)
        max_conf = policy.get("max_confidence", 0.7)

        # Sadece doğrulanmış platformlar sayılır (canlı HTTP 200)
        if verified_count == 0:
            return 0.0
        confidence = base + boost * (verified_count - 1)
        return min(confidence, max_conf)

    def execute(self):
        target = self.target
        if not target:
            return self.error("No username provided. Usage: social <username> [person_name]")

        handle = target[0]
        person_name = target[1] if len(target) >= 2 else None

        self.begin_investigation(
            goal="Social Media Username Intelligence",
            phases=[
                (1, "PLATFORM SWEEP"),
                (2, "USERNAME CORRELATION"),
                (3, "ENTITY MAPPING"),
            ],
        )

        # 1. Platform taraması
        def run_sweep():
            return self._search_platforms(handle)

        self.status_step(f"Sweeping platforms for '{handle}'", work=run_sweep)
        platform_results = self._search_platforms(handle)

        verified_results = [r for r in platform_results if r.get("verified")]
        found_platforms = [r["platform"] for r in verified_results]

        # 2. Username correlation olasılığı
        confidence = self._calculate_username_confidence(
            len(found_platforms), len(verified_results), len(platform_results)
        )

        self.status_step(f"Correlation assessment (confidence: {confidence:.2f})")

        # 3. Varlık kayıtları
        for pr in verified_results:
            self.add_social_profile(pr["platform"], handle, properties={
                "url": pr["url"],
                "verified": True,
                "weight": pr["weight"],
            })
            # Temporal olay
            self.log_event("profile_found", entity=f"social_profile:{pr['platform']}/{handle}",
                           metadata={"url": pr["url"], "platform": pr["platform"]})

        # Username varlığı — sosyal profil korelasyonu için grup anahtarı
        self.add_entity("username", handle, {
            "platforms_found": found_platforms,
            "total_platforms_checked": len(platform_results),
            "verified_count": len(verified_results),
        })

        # --- İlişkiler ---
        # Her bulunan platformda username varlığına bağla (kesin gözlem — profil var)
        for pr in verified_results:
            self.add_relation(
                "username", handle, "username_present_on", "social_profile", f"{pr['platform']}/{handle}",
                evidence=f"Verified: username '{handle}' exists on {pr['platform']} ({pr['url']})",
                confidence=1.0,  # Kesin gözlem — profil URL'si doğrulandı
            )

        # Olası aynı kişi eşleşmesi (correlation — KESİN değil)
        if len(verified_results) >= 2:
            conf_msg = (f"Username '{handle}' found on {len(verified_results)} platforms "
                        f"({', '.join(found_platforms)}) — correlation suggests possible same person "
                        f"(confidence: {confidence:.2f})")
            self.add_note(conf_msg, severity="info", confidence=confidence)

            # Kişiye aday bağlantı (eğer kullanıcı kişi adı verdiyse)
            if person_name:
                self.add_person(person_name)
                self.add_relation(
                    "person", person_name, "possible_username_match", "username", handle,
                    evidence=f"User-provided association: '{handle}' linked as possible username for {person_name} "
                             f"(found on {len(verified_results)} platforms: {', '.join(found_platforms)})",
                    confidence=confidence,
                )
                self.log_event("possible_username_match", entity=f"person:{person_name}",
                               metadata={"username": handle, "platforms": found_platforms,
                                         "confidence": confidence})
        else:
            self.status_step(f"No verified platform profiles found for '{handle}' (offline check or blocked)")

        self.add_note(
            f"Username '{handle}' — {len(verified_results)}/{len(platform_results)} platforms found, "
            f"correlation confidence: {confidence:.2f}",
            severity="info", confidence=confidence,
        )

        data = {
            "username": handle,
            "platforms_checked": len(platform_results),
            "platforms_found": found_platforms,
            "verified_profiles": [pr for pr in verified_results],
            "correlation_confidence": round(confidence, 3),
            "person_candidate": person_name,
        }
        return self.success(target=handle, data=data)