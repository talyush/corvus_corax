import re
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class BreachIntelModule(BaseModule):
    """
    v0.9 — Data Breach Intelligence Module.

    EMAIL AKTARICI ETİK TASARIM:
    Bu modül SADECE meta-veri toplar. Ham şifre, kredi kartı veya kişisel içerik
    ASLA depolanmaz veya gösterilmez. Sadece "bu email hangi breach listelerinde
    geçiyor" bilgisi tutulur.

    API anahtarı gerektirmez:
    - Firefox Monitor API (kamuya açık, HIBP verisini kullanır)
    - HIBP Pwned Passwords (k-anonimlik — şifre asla tam gönderilmez)
    - Kullanıcı manuel breach listesi
    """
    name = "breach"

    def _normalize_email(self, raw):
        """Email adresini normalize eder."""
        if not raw or "@" not in raw:
            return None
        return raw.strip().lower()

    def _check_firefox_monitor(self, email, timeout=10):
        """
        Firefox Monitor API ile email breach geçmişini sorgular.
        API anahtarı gerektirmez. HIBP verisini kullanır.
        """
        try:
            # Firefox Monitor scan endpoint'i — kamuya açık
            url = "https://monitor.firefox.com/scan"
            form_data = urllib.parse.urlencode({"email": email}).encode("utf-8")
            req = urllib.request.Request(url, data=form_data, headers={
                "User-Agent": "CorvusCorax/0.9 (+https://github.com/corvus-corax/project)",
                "Content-Type": "application/x-www-form-urlencoded",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Firefox Monitor response format — breaches listesi
                breaches = data.get("breaches", [])
                return [b.get("Name", b.get("name", "Unknown")) for b in breaches]
        except Exception:
            return None

    def _check_hibp_pwned_password(self, password_hash, timeout=10):
        """
        HIBP Pwned Passwords — k-anonimlik kontrolü.
        Şifrenin tamamı asla gönderilmez; sadece SHA-1 hash'in 5 karakterlik prefix'i gönderilir.
        """
        if not password_hash:
            return False, 0
        sha1 = hashlib.sha1(password_hash.encode("utf-8")).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]
        try:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorvusCorax/0.9"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8")
                for line in content.splitlines():
                    cand_suffix, count = line.split(":")
                    if cand_suffix.strip().upper() == suffix:
                        return True, int(count)
        except Exception:
            pass
        return False, 0

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: breach <email> [--sources=LinkedIn,Adobe]")

        email = self._normalize_email(args[0])
        if not email:
            return self.error(f"Invalid email address: {args[0]}")

        # Manuel sources (opsiyonel)
        manual_sources = []
        for arg in args[1:]:
            if arg.startswith("--sources="):
                manual_sources = [s.strip() for s in arg.split("=", 1)[1].split(",") if s.strip()]

        self.begin_investigation(
            goal=f"Data Breach Intelligence — {email}",
            phases=[
                (1, "BREACH SOURCE SCAN"),
                (2, "K-ANONYMITY PASSWORD CHECK"),
                (3, "RISK ASSESSMENT"),
            ],
        )

        # 1. Firefox Monitor sorgusu (anahtarsız)
        self.status_step("Querying Firefox Monitor (public API)")
        firefox_breaches = self._check_firefox_monitor(email)

        # 2. Manuel sources birleştir
        all_sources = set()
        if firefox_breaches:
            all_sources.update(firefox_breaches)
        all_sources.update(manual_sources)

        # 3. K-anonim şifre kontrolü (opsiyonel — kullanıcı şifre hash'i sağlarsa)
        pwned_count = 0
        for arg in args[1:]:
            if arg.startswith("--password="):
                password = arg.split("=", 1)[1]
                self.status_step("Checking password via k-anonymity (HIBP)")
                is_pwned, count = self._check_hibp_pwned_password(password)
                if is_pwned:
                    pwned_count = count
                    self.add_note(
                        f"Password associated with this session has appeared in {count} breaches "
                        f"(k-anonymity check — full password never transmitted)",
                        severity="warning",
                    )
                break

        # --- Varlık ve İlişki Kaydı ---
        self.add_email(email)

        if all_sources:
            self.add_relation(
                "email", email, "appeared_in_breaches", "breach_record", f"{len(all_sources)} sources",
                evidence=f"Email found in {len(all_sources)} breach sources: {', '.join(sorted(all_sources)[:5])}",
                confidence=0.7,
            )
            self.log_event("breach_found", entity=f"email:{email}",
                           metadata={"breach_count": len(all_sources),
                                     "sources": list(all_sources)[:5]})
        else:
            self.log_event("breach_checked", entity=f"email:{email}",
                           metadata={"result": "no_breaches_found"})

        # --- Risk Değerlendirmesi ---
        risk_level = "Low"
        if len(all_sources) >= 5:
            risk_level = "Critical"
        elif len(all_sources) >= 3:
            risk_level = "High"
        elif len(all_sources) >= 1:
            risk_level = "Medium"

        self.add_note(
            f"Email {email} — breach sources: {len(all_sources)}, risk level: {risk_level}",
            severity="warning" if risk_level != "Low" else "info",
            confidence=0.7,
        )

        data = {
            "email": email,
            "breach_sources": sorted(all_sources),
            "breach_count": len(all_sources),
            "risk_level": risk_level,
            "password_pwned_count": pwned_count,
            "manual_sources": manual_sources,
        }
        return self.success(target=email, data=data)