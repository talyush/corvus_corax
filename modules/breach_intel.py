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

    # ------------------------------------------------------------------
    # v1.4 — Genişletilmiş kamuya açık breach kaynakları
    # ------------------------------------------------------------------

    def _http_get_json(self, url, timeout=20):
        """JSON döndüren GET isteği — tek seferlik yardımcı."""
        req = urllib.request.Request(url, headers={
            "User-Agent": "CorvusCorax/1.4 (+https://github.com/corvus-corax/project)",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))

    def _check_xposedornot(self, email, timeout=20):
        """
        XposedOrNot — ücretsiz, API anahtarı gerektirmez.
        /v1/check-email/{email} -> {status, email, breaches: [[isim, ...]]}
        """
        result = {"breaches": [], "ok": False}
        try:
            quick = self._http_get_json(
                f"https://api.xposedornot.com/v1/check-email/{urllib.parse.quote(email)}",
                timeout=timeout,
            )
            if quick.get("status") == "success":
                result["ok"] = True
                # breaches iç içe listeler halinde gelir: [[isim, isim2, ...]]
                for group in quick.get("breaches", []) or []:
                    if isinstance(group, list):
                        result["breaches"].extend(g for g in group if isinstance(g, str))
                    elif isinstance(group, str):
                        result["breaches"].append(group)
                result["breaches"] = list(dict.fromkeys(result["breaches"]))
            return result
        except Exception:
            return result

    def _check_xposedornot_analytics(self, email, timeout=20):
        """
        XposedOrNot breach-analytics — detaylı kırılım.
        Sadece meta-veri toplanır; breach başlığı dünya modeline girer, ham içerik asla.
        """
        result = {"breaches": [], "pastes": [], "pastes_summary": {}, "ok": False}
        try:
            j = self._http_get_json(
                f"https://api.xposedornot.com/v1/breach-analytics?email={urllib.parse.quote(email)}",
                timeout=timeout,
            )
            # ExposedBreaches -> {"breaches_details": [{"breach", "details", ...}]}
            exposed = j.get("ExposedBreaches") or {}
            details = exposed.get("breaches_details") or []
            for d in details:
                if isinstance(d, dict) and d.get("breach"):
                    result["breaches"].append(d["breach"])
            # PastesSummary -> {"cnt", "domain", "tmpstmp"}
            ps = j.get("PastesSummary") or {}
            if isinstance(ps, dict):
                result["pastes_summary"] = {
                    "count": ps.get("cnt", 0),
                    "domain": ps.get("domain", ""),
                    "timestamp": ps.get("tmpstmp", ""),
                }
            # BreachesSummary -> {"site": "A;B;C;..."}
            bs = j.get("BreachesSummary") or {}
            if isinstance(bs, dict) and bs.get("site"):
                result["breaches"].extend(
                    s.strip() for s in str(bs["site"]).split(";") if s.strip()
                )
            result["ok"] = True
            result["breaches"] = list(dict.fromkeys(result["breaches"]))
            return result
        except Exception:
            return result

    def _check_ahmia(self, query, timeout=20):
        """
        Ahmia — Tor .onion arama motoru (kamuya açık).
        Homepage'den anti-bot token alınır, search sorgusuna eklenir,
        çıkan .onion adresleri toplanır. SADECE link meta-verisi.
        """
        result = {"onions": [], "ok": False}
        try:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
            # 1) Homepage -> token
            req = urllib.request.Request("https://ahmia.fi/", headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                home = resp.read().decode("utf-8", "replace")
            m = re.search(r'name="([a-z0-9]+)"[^>]*value="([a-z0-9]+)"', home)
            tok_name = m.group(1) if m else "q"
            tok_val = m.group(2) if m else ""
            # 2) Search
            params = {"q": query, tok_name: tok_val}
            search_url = "https://ahmia.fi/search/?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(search_url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                page = resp.read().decode("utf-8", "replace")
            onions = re.findall(r"http://([a-z0-9]{16,56}\.onion)[/'\"]", page)
            result["onions"] = list(dict.fromkeys(onions))
            result["ok"] = True
            return result
        except Exception:
            return result

    def _check_tor_exit_nodes(self, ip_list, timeout=25):
        """
        dan.me.uk torlist — Tor çıkış düğümü listesi.
        Hedef IP'lerin listesinde olup olmadığını kontrol eder (altyapı bilgisi).
        """
        result = {"exit_matches": [], "total_nodes": 0, "ok": False}
        try:
            req = urllib.request.Request(
                "https://www.dan.me.uk/torlist/?exit",
                headers={"User-Agent": "Mozilla/5.0 Chrome/120"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", "replace")
            nodes = {ln.strip() for ln in text.splitlines()
                     if ln.strip() and not ln.startswith("#")}
            result["total_nodes"] = len(nodes)
            result["exit_matches"] = [ip for ip in (ip_list or []) if ip in nodes]
            result["ok"] = True
            return result
        except Exception:
            return result

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

        # 2. XposedOrNot — hızlı tarama + detaylı analiz (kamuya açık, anahtarsız)
        self.status_step("Querying XposedOrNot (check-email)")
        xon_quick = self._check_xposedornot(email)
        xon_breaches = xon_quick.get("breaches", []) if xon_quick.get("ok") else []

        self.status_step("Querying XposedOrNot (breach-analytics)")
        xon_analytics = self._check_xposedornot_analytics(email)
        if xon_analytics.get("ok"):
            xon_breaches = list(dict.fromkeys(xon_breaches + xon_analytics.get("breaches", [])))
        pastes_summary = xon_analytics.get("pastes_summary", {})

        # 3. Ahmia — .onion arama (token akışı ile)
        onion_links = []
        ahmia_ok = False
        if "--no-onion" not in args:
            self.status_step("Searching Ahmia for .onion mentions")
            ahmia = self._check_ahmia(email)
            if ahmia.get("ok"):
                onion_links = ahmia.get("onions", [])
                ahmia_ok = True

        # 4. Tor exit node eşleştirmesi — context'teki IP'lerle
        tor_exit = {"ok": False, "total_nodes": 0, "matched": []}
        candidate_ips = []
        if self.context:
            for ip in list(self.context.data.get("ips", {}).keys())[:20]:
                candidate_ips.append(ip)
        if candidate_ips:
            self.status_step("Checking Tor exit node list (dan.me.uk)")
            tre = self._check_tor_exit_nodes(candidate_ips)
            tor_exit = {
                "ok": tre.get("ok", False),
                "total_nodes": tre.get("total_nodes", 0),
                "matched": tre.get("exit_matches", []),
            }

        # 5. Manuel sources birleştir
        all_sources = set()
        if firefox_breaches:
            all_sources.update(firefox_breaches)
        all_sources.update(xon_breaches)
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

        # --- v1.4: .onion / Tor altyapı sinyalleri ---
        if onion_links:
            self.add_entity("onion_service", onion_links[0], {
                "total_mentions": len(onion_links),
                "sample": onion_links[:5],
            })
            self.add_relation(
                "email", email, "mentioned_in_onion_services", "onion_service",
                f"{len(onion_links)} services",
                evidence=f"Ahmia search found {len(onion_links)} .onion mentions for {email}",
                confidence=0.4,  # arama eşleşmesi — doğrulanmış sahiplik değil
            )
            self.log_event("onion_mentions_found", entity=f"email:{email}",
                           metadata={"count": len(onion_links)})

        if tor_exit.get("matched"):
            for ip in tor_exit["matched"][:5]:
                self.add_relation(
                    "ip", ip, "is_tor_exit_node", "tor_network", "dan.me.uk list",
                    evidence="IP appears in current Tor exit node list (dan.me.uk)",
                    confidence=0.9,
                )
                self.log_event("tor_exit_match", entity=f"ip:{ip}",
                               metadata={"total_nodes": tor_exit.get("total_nodes", 0)})

        # --- Risk Değerlendirmesi ---
        risk_level = "Low"
        if len(all_sources) >= 5:
            risk_level = "Critical"
        elif len(all_sources) >= 3:
            risk_level = "High"
        elif len(all_sources) >= 1:
            risk_level = "Medium"
        elif onion_links:
            risk_level = "Low"  # onion varlığı tek başına risk artırmaz, not düşer

        risk_flags = []
        if pastes_summary.get("count"):
            risk_flags.append(f"{pastes_summary['count']} exposed pastes")

        self.add_note(
            f"Email {email} — breach sources: {len(all_sources)}, risk level: {risk_level}"
            + (f", onion mentions: {len(onion_links)}" if onion_links else "")
            + (f", Tor exit IPs: {len(tor_exit.get('matched', []))}" if tor_exit.get("matched") else ""),
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
            # --- v1.4: yeni kaynaklar ---
            "source_breakdown": {
                "firefox_monitor": len(firefox_breaches or []),
                "xposedornot": len(xon_breaches),
                "ahmia_onion": len(onion_links),
            },
            "pastes_summary": pastes_summary,
            "onion_links": onion_links[:10],
            "tor_exit": tor_exit,
        }
        return self.success(target=email, data=data)