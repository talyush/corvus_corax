import dns.resolver
import dns.exception
from core.module_base import BaseModule

class DnsIntelModule(BaseModule):
    """
    Corvus Corax v0.8 — DNS Intelligence Module.
    Queries basic DNS records (A, AAAA, MX, NS, TXT, CAA) and security-specific
    records (SPF, DMARC, DKIM) to assess spoofing vulnerabilities and profile mail infrastructure.
    """
    name = "dns"

    def _get_resolver(self, timeout):
        """Constructs a dns.resolver.Resolver configured with public DNS nameservers
        (Google & Cloudflare) for stability and consistency across networks.
        """
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4', '1.0.0.1']
        resolver.timeout = timeout
        resolver.lifetime = timeout
        return resolver

    def _query_record(self, domain, rtype, timeout):
        try:
            resolver = self._get_resolver(timeout)
            answers = resolver.resolve(domain, rtype)
            return [str(rdata).strip('"\'') for rdata in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception:
            return []

    def _query_mx(self, domain, timeout):
        try:
            resolver = self._get_resolver(timeout)
            answers = resolver.resolve(domain, 'MX')
            mx_list = []
            for rdata in answers:
                mx_list.append({
                    "host": str(rdata.exchange).rstrip(".").lower(),
                    "priority": int(rdata.preference)
                })
            mx_list.sort(key=lambda x: x["priority"])
            return mx_list
        except Exception:
            return []

    def _query_caa(self, domain, timeout):
        try:
            resolver = self._get_resolver(timeout)
            answers = resolver.resolve(domain, 'CAA')
            caa_list = []
            for rdata in answers:
                tag = rdata.tag.decode('utf-8', errors='ignore') if isinstance(rdata.tag, bytes) else str(rdata.tag)
                val = rdata.value.decode('utf-8', errors='ignore') if isinstance(rdata.value, bytes) else str(rdata.value)
                caa_list.append(f"{rdata.flags} {tag} \"{val}\"")
            return caa_list
        except Exception:
            return []

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: dns <domain> [selector]")

        domain = args[0].strip().lower()
        custom_selector = args[1].strip() if len(args) > 1 else None

        config_timeout = float(self.config.get("timeout", 5.0)) if self.config else 5.0
        timeout = max(config_timeout, 4.0)

        inv = self.begin_investigation(
            f"Map DNS infrastructure & email security posture for {domain}",
            ["TARGET ACQUISITION", "RECORD ENUMERATION", "POLICY ANALYSIS", "CONTEXT INTEGRATION"]
        )

        with inv.phase(0):
            self.status_step(f"Initiating DNS resolver query for {domain}")

        a_records, aaaa_records, ns_records, txt_records, caa_records, mx_records = [], [], [], [], [], []
        with inv.phase(1):
            def fetch_records():
                nonlocal a_records, aaaa_records, ns_records, txt_records, caa_records, mx_records
                a_records = self._query_record(domain, "A", timeout)
                aaaa_records = self._query_record(domain, "AAAA", timeout)
                ns_records = self._query_record(domain, "NS", timeout)
                txt_records = self._query_record(domain, "TXT", timeout)
                caa_records = self._query_caa(domain, timeout)
                mx_records = self._query_mx(domain, timeout)

            self.status_step(f"Querying A, AAAA, NS, TXT, CAA & MX records for {domain}", work=fetch_records)

        spf_record = None
        dmarc_record = None
        dkim_keys = {}

        with inv.phase(2):
            def analyze_policies():
                nonlocal spf_record, dmarc_record, dkim_keys
                for txt in txt_records:
                    if txt.lower().startswith("v=spf1"):
                        spf_record = txt
                        break

                dmarc_txts = self._query_record(f"_dmarc.{domain}", "TXT", timeout)
                for txt in dmarc_txts:
                    if txt.lower().startswith("v=dmarc1"):
                        dmarc_record = txt
                        break

                common_selectors = ["default", "google", "mail", "k1", "smtp", "key1", "dkim"]
                if custom_selector and custom_selector not in common_selectors:
                    common_selectors.insert(0, custom_selector)

                for sel in common_selectors:
                    dkim_domain = f"{sel}._domainkey.{domain}"
                    dkim_txts = self._query_record(dkim_domain, "TXT", timeout)
                    for txt in dkim_txts:
                        if "v=dkim1" in txt.lower() or "p=" in txt.lower():
                            dkim_keys[sel] = txt
                            break

            self.status_step("Evaluating SPF, DMARC policy & DKIM selectors", work=analyze_policies)

        # --- Security & Email Spoofing Analysis ---
        spf_weak = False
        if not spf_record:
            self.add_note(
                f"Missing SPF record on {domain}. Mail spoofing is highly likely.",
                severity="critical"
            )
            spf_weak = True
            self.analyst_log(f"SPF record missing on {domain} — email spoofing protection absent")
        else:
            spf_lower = spf_record.lower()
            if "+all" in spf_lower:
                self.add_note(
                    f"SPF record on {domain} allows anybody (+all). Email spoofing is trivial.",
                    severity="critical"
                )
                spf_weak = True
                self.analyst_log("SPF record permits all (+all) — spoofing risk CRITICAL")
            elif "?all" in spf_lower:
                self.add_note(
                    f"SPF record on {domain} uses neutral fail (?all). Soft authentication only.",
                    severity="warning"
                )
            elif "~all" in spf_lower:
                self.add_note(
                    f"SPF record on {domain} uses softfail (~all). Spoofed mail is often accepted.",
                    severity="info"
                )

        dmarc_weak = False
        if not dmarc_record:
            self.analyst_log("DMARC record missing — domain unprotected against executive impersonation")
            self.add_note(
                f"Missing DMARC record on {domain}. Incoming spoofed mail has no verification policy.",
                severity="warning"
            )
            dmarc_weak = True
        else:
            dmarc_lower = dmarc_record.lower()
            if "p=none" in dmarc_lower:
                self.add_note(
                    f"DMARC policy on {domain} is 'none' (monitoring only). Spoofed mails will still be delivered.",
                    severity="warning"
                )
                dmarc_weak = True
            elif "p=quarantine" in dmarc_lower:
                self.add_note(
                    f"DMARC policy on {domain} is 'quarantine'. Spoofed emails will go to spam/junk folders.",
                    severity="info"
                )
            elif "p=reject" in dmarc_lower:
                self.add_note(
                    f"DMARC policy on {domain} is 'reject'. Spoofed emails will be hard-blocked.",
                    severity="info"
                )

        # --- Relations ---
        # domain -> mx
        for mx in mx_records:
            mx_host = mx["host"]
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_mx_server",
                dst_type="domain",
                dst_value=mx_host,
                evidence=f"MX priority: {mx['priority']}"
            )
            # Add MX hosts to context domains structure so they can be scanned
            if self.context:
                self.context.data["domains"].setdefault(mx_host, {"ips": []})

        # domain -> ns
        for ns in ns_records:
            ns_host = ns.rstrip(".").lower()
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_ns_server",
                dst_type="domain",
                dst_value=ns_host,
                evidence="NS record resolution"
            )

        if spf_record:
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_spf_record",
                dst_type="txt",
                dst_value=spf_record,
                evidence="SPF policy definition"
            )

        if dmarc_record:
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_dmarc_record",
                dst_type="txt",
                dst_value=dmarc_record,
                evidence="DMARC policy definition"
            )

        for sel, key in dkim_keys.items():
            self.add_relation(
                src_type="domain",
                src_value=domain,
                relation="has_dkim_record",
                dst_type="txt",
                dst_value=f"selector:{sel} -> {key[:30]}...",
                evidence=f"DKIM record resolved at {sel}._domainkey.{domain}"
            )

        # Save to ContextManager
        dns_data = {
            "domain": domain,
            "A": a_records,
            "AAAA": aaaa_records,
            "NS": ns_records,
            "MX": mx_records,
            "TXT": txt_records,
            "CAA": caa_records,
            "spf": spf_record,
            "dmarc": dmarc_record,
            "dkim": dkim_keys,
            "spf_weak": spf_weak,
            "dmarc_weak": dmarc_weak,
        }
        if self.context:
            self.context.add_dns_record(domain, dns_data)

            # Map domain to resolved IPs in Context
            for ip in a_records:
                self.context.add_domain_mapping(domain, ip)

        return self.success(
            target=domain,
            data=dns_data
        )
