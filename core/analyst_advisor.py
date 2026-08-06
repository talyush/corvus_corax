from colorama import Fore, Style

class AnalystAdvisor:
    """
    Corvus Corax v0.8.5 — Context-Aware Analyst Advisor.

    Analyzes current Context graph state and produces intelligent,
    context-driven next step suggestions for the investigator ("Cyber Sherlock Vibe").
    """

    def __init__(self, context):
        self.context = context

    def generate_suggestions(self):
        if not self.context or not hasattr(self.context, "data"):
            return []

        data = self.context.data
        suggestions = []

        certs = data.get("certificates", {})
        dns = data.get("dns_records", {})
        headers = data.get("http_headers", {})
        email = data.get("email_intel", {})
        metadata = data.get("metadata_intel", {})
        tech = data.get("tech_intel", {})
        derived = data.get("derived_relations", [])
        notes = data.get("notes", [])

        # 1. Certificate SANs expansion hint
        san_hosts = set()
        for fingerprint, cert in certs.items():
            for h in cert.get("hosts", []):
                if h not in dns and not h.startswith("*"):
                    san_hosts.add(h)
        if san_hosts:
            sample_san = list(san_hosts)[0]
            suggestions.append(
                f"Discovered un-profiled SAN target '{sample_san}' from TLS cert. "
                f"Run 'dns {sample_san}' or 'footprint {sample_san}' to map infrastructure."
            )

        # 2. Favicon / Shared infrastructure hint
        favicons = set()
        for dom, mdata in metadata.items():
            fav = mdata.get("favicon")
            if fav and fav.get("shodan_hash"):
                favicons.add(fav["shodan_hash"])
        if favicons:
            suggestions.append(
                f"Favicon MurmurHash3 fingerprints collected. "
                f"Run 'nexus analyze' to pivot and identify shared host infrastructure."
            )

        # 3. Personal email leak hint
        for dom, edata in email.items():
            pattern = edata.get("pattern")
            if pattern and pattern.get("is_personal_leak"):
                suggestions.append(
                    f"Personal email leak detected in DMARC for '{dom}'. "
                    f"Run 'nexus analyze' to correlate staff exposure."
                )
                break

        # 4. Sensitive path in robots.txt hint
        for dom, mdata in metadata.items():
            robots = mdata.get("robots")
            if robots and robots.get("sensitive_paths"):
                suggestions.append(
                    f"Sensitive paths disclosed in robots.txt for '{dom}' ({len(robots['sensitive_paths'])} paths). "
                    f"Review paths or run 'crawl {mdata.get('base_url', dom)}'."
                )
                break

        # 5. Missing security headers / Tech stack hint
        for dom, hdata in headers.items():
            missing = hdata.get("missing_security_headers", [])
            if len(missing) >= 3 and dom not in tech:
                suggestions.append(
                    f"Target '{dom}' missing {len(missing)} security headers. "
                    f"Run 'tech {dom}' to fingerprint web server & framework vulnerabilities."
                )
                break

        # 6. Correlation / Export hint
        if derived:
            suggestions.append(
                f"Nexus Graph contains {len(derived)} derived relations. "
                f"Run 'nexus export html' to generate an executive intelligence dossier."
            )

        return suggestions[:2]  # Return top 2 relevant suggestions

    def print_suggestions(self):
        suggestions = self.generate_suggestions()
        if suggestions:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}[Analyst Next Steps]{Style.RESET_ALL}")
            for sug in suggestions:
                print(f"  {Fore.CYAN}-->{Style.RESET_ALL} {sug}")
            print()
