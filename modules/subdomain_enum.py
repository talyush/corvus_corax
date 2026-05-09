import json
import urllib.parse
import urllib.request
from core.module_base import BaseModule


class SubdomainEnumModule(BaseModule):
    name = "subdomain"

    def _fetch_crtsh(self, domain, timeout, user_agent):
        query = urllib.parse.quote(f"%.{domain}")
        url = f"https://crt.sh/?q={query}&output=json"
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="ignore")
        if not raw.strip():
            return []
        return json.loads(raw)

    def _normalize_crtsh_names(self, rows, domain):
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
        timeout = float(self.config.get("timeout", 3.0)) if self.config else 3.0
        user_agent = (self.config or {}).get("user_agent", "CorvusCorax/0.3")

        try:
            crt_rows = self._fetch_crtsh(domain, timeout=timeout, user_agent=user_agent)
            crt_subdomains = self._normalize_crtsh_names(crt_rows, domain)

            wordlist_candidates = []
            if wordlist_path:
                words = self._load_wordlist(wordlist_path)
                wordlist_candidates = sorted({f"{word}.{domain}" for word in words})

            merged = sorted(set(crt_subdomains) | set(wordlist_candidates))

            if self.context:
                for host in crt_subdomains:
                    self.context.data["domains"].setdefault(host, {"ips": []})
                self.context.add_note(
                    text=f"subdomain enum completed for {domain} ({len(crt_subdomains)} from crt.sh)",
                    source="subdomain",
                    severity="info",
                )

            return self.success(
                target=domain,
                data={
                    "domain": domain,
                    "sources": {
                        "crt_sh": True,
                        "wordlist": bool(wordlist_path),
                    },
                    "crt_sh_count": len(crt_subdomains),
                    "wordlist_count": len(wordlist_candidates),
                    "total_count": len(merged),
                    "subdomains": merged,
                },
            )
        except Exception as e:
            return self.error(e, target=domain)
