import json
import urllib.parse
import urllib.request
from core.module_base import BaseModule


class SubdomainEnumModule(BaseModule):
    name = "subdomain"

    def _fetch_crtsh(self, domain, timeout, user_agent):
        try:
            query = urllib.parse.quote(f"%.{domain}")
            url = f"https://crt.sh/?q={query}&output=json"
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            if not raw.strip():
                return []
            return json.loads(raw)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"crt.sh fetch failed: {e}")
            return None

    def _normalize_crtsh_names(self, rows, domain):
        if not rows:
            return []
        found = set()
        suffix = f".{domain}".lower()

        for row in rows:
            name_value = str(row.get("name_value", "")).strip()
            if not name_value:
                continue

            for part in name_value.splitlines():
                host = part.strip().lower().lstrip("*.").rstrip(".")
                if not host:
                    continue
                if host == domain or host.endswith(suffix):
                    found.add(host)
        return sorted(found)

    def _fetch_hackertarget(self, domain, timeout, user_agent):
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            found = set()
            suffix = f".{domain}".lower()
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if parts:
                    host = parts[0].strip().lower()
                    if host == domain or host.endswith(suffix):
                        found.add(host)
            return sorted(found)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"HackerTarget fetch failed: {e}")
            return None

    def _fetch_rapiddns(self, domain, timeout, user_agent):
        try:
            import re
            url = f"https://rapiddns.io/subdomain/{domain}?full=1&down=1"
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            found = set()
            suffix = f".{domain}".lower()
            for match in re.finditer(r'<td>([^<]+)</td>', raw):
                host = match.group(1).strip().lower()
                if host == domain or host.endswith(suffix):
                    found.add(host)
            return sorted(found)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"RapidDNS fetch failed: {e}")
            return None

    def _load_wordlist(self, path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip().lower() for line in f]
        return [w for w in lines if w and not w.startswith("#")]

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: subdomain <domain> [wordlist_path]")

        domain = args[0].strip().lower()
        wordlist_path = args[1].strip() if len(args) > 1 else None
        
        config_timeout = float(self.config.get("timeout", 3.0)) if self.config else 3.0
        timeout = max(config_timeout, 8.0)
        user_agent = (self.config or {}).get("user_agent", "CorvusCorax/0.3")

        inv = self.begin_investigation(
            f"Enumerate passive certificate & DNS subdomains for {domain}",
            ["CERTIFICATE TRANSPARENCY LOGS", "PASSIVE DNS APIS", "DEDUPLICATION & CONTEXT SYNC"]
        )

        sources_status = {
            "crt_sh": {"success": False, "count": 0},
            "hackertarget": {"success": False, "count": 0},
            "rapiddns": {"success": False, "count": 0},
            "wordlist": {"success": False, "count": 0}
        }

        crt_subdomains = []
        with inv.phase(0):
            def fetch_crt():
                nonlocal crt_subdomains
                crt_rows = self._fetch_crtsh(domain, timeout=timeout, user_agent=user_agent)
                if crt_rows is not None:
                    crt_subdomains = self._normalize_crtsh_names(crt_rows, domain)
                    sources_status["crt_sh"] = {"success": True, "count": len(crt_subdomains)}
                else:
                    self.add_note(f"Passive source crt.sh query timed out or failed for {domain}.", severity="warning")

            self.status_step(f"Querying crt.sh certificate transparency logs for {domain}", work=fetch_crt)

        ht_subdomains = []
        rapid_subdomains = []
        with inv.phase(1):
            def fetch_passive():
                nonlocal ht_subdomains, rapid_subdomains
                ht_rows = self._fetch_hackertarget(domain, timeout=timeout, user_agent=user_agent)
                if ht_rows is not None:
                    ht_subdomains = ht_rows
                    sources_status["hackertarget"] = {"success": True, "count": len(ht_subdomains)}

                rapid_rows = self._fetch_rapiddns(domain, timeout=timeout, user_agent=user_agent)
                if rapid_rows is not None:
                    rapid_subdomains = rapid_rows
                    sources_status["rapiddns"] = {"success": True, "count": len(rapid_subdomains)}

            self.status_step("Querying HackTarget & RapidDNS passive DNS APIs", work=fetch_passive)
            self.add_note(f"Passive source HackerTarget query timed out or failed for {domain}.", severity="warning")

        # 3. RapidDNS
        rd_subdomains = []
        rd_rows = self._fetch_rapiddns(domain, timeout=timeout, user_agent=user_agent)
        if rd_rows is not None:
            rd_subdomains = rd_rows
            sources_status["rapiddns"] = {"success": True, "count": len(rd_subdomains)}
        else:
            self.add_note(f"Passive source RapidDNS query timed out or failed for {domain}.", severity="warning")

        # 4. Wordlist
        wordlist_candidates = []
        if wordlist_path:
            try:
                words = self._load_wordlist(wordlist_path)
                wordlist_candidates = sorted({f"{word}.{domain}" for word in words})
                sources_status["wordlist"] = {"success": True, "count": len(wordlist_candidates)}
            except Exception as e:
                self.add_note(f"Wordlist loading failed for {wordlist_path}: {e}", severity="warning")

        # Combine all subdomains and assign relations based on where they were found
        all_passive_subs = {}
        for sub in crt_subdomains:
            all_passive_subs.setdefault(sub, []).append("crt.sh passive lookup")
        for sub in ht_subdomains:
            all_passive_subs.setdefault(sub, []).append("HackerTarget passive lookup")
        for sub in rd_subdomains:
            all_passive_subs.setdefault(sub, []).append("RapidDNS passive lookup")

        merged = sorted(set(all_passive_subs.keys()) | set(wordlist_candidates))

        # Check if we got any results or if everything failed
        any_success = (
            sources_status["crt_sh"]["success"] or
            sources_status["hackertarget"]["success"] or
            sources_status["rapiddns"]["success"] or
            sources_status["wordlist"]["success"]
        )

        if not any_success:
            return self.error("All subdomain enumeration sources (crt.sh, HackerTarget, RapidDNS) and wordlist failed or timed out.", target=domain)

        # Context updates
        if self.context:
            for host in merged:
                self.context.data["domains"].setdefault(host, {"ips": []})

        # Add relations for passive sources
        for host, evidences in all_passive_subs.items():
            evidence_str = " & ".join(evidences)
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_subdomain",
                dst_type="domain",
                dst_value=host,
                evidence=evidence_str
            )

        # Add relations for wordlist
        for host in wordlist_candidates:
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_subdomain",
                dst_type="domain",
                dst_value=host,
                evidence="wordlist candidate"
            )

        # Generate module note summary
        summary_parts = []
        for name, status in sources_status.items():
            if status["success"]:
                summary_parts.append(f"{status['count']} from {name}")
            else:
                summary_parts.append(f"{name} failed")
        
        self.add_note(
            text=f"Subdomain enumeration completed for {domain}: {', '.join(summary_parts)} (Total unique: {len(merged)})",
            severity="info"
        )

        return self.success(
            target=domain,
            data={
                "domain": domain,
                "sources": {
                    "crt_sh": sources_status["crt_sh"]["success"],
                    "hackertarget": sources_status["hackertarget"]["success"],
                    "rapiddns": sources_status["rapiddns"]["success"],
                    "wordlist": sources_status["wordlist"]["success"],
                },
                "counts": {
                    "crt_sh": sources_status["crt_sh"]["count"],
                    "hackertarget": sources_status["hackertarget"]["count"],
                    "rapiddns": sources_status["rapiddns"]["count"],
                    "wordlist": sources_status["wordlist"]["count"],
                    "total": len(merged)
                },
                "crt_sh_count": sources_status["crt_sh"]["count"],
                "wordlist_count": sources_status["wordlist"]["count"],
                "total_count": len(merged),
                "subdomains": merged,
            },
        )
