import json
from datetime import datetime

class OutputManager:
    def __init__(self, logger=None, mode="text"):
        self.results = []
        self.logger = logger
        self.mode = (mode or "text").lower()

    def add_result(self, result):
        if result is None:
            return
        self.results.append(result)

    def clear(self):
        self.results.clear()

    def to_json(self):
        return json.dumps(self.results, indent=4)

    def to_log(self):
        if not self.logger:
            return
        for r in self.results:
            self.logger.info(json.dumps(r))

    def export_json(self, filename="report.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4)

    def to_text(self):
        if self.mode == "json":
            return self.to_json()

        lines = []
        # ANSI Escape codes for professional terminal look
        C_CYAN = "\033[36m"
        C_GREEN = "\033[32m"
        C_YELLOW = "\033[33m"
        C_RED = "\033[31m"
        C_MAGENTA = "\033[35m"
        C_BOLD = "\033[1m"
        C_RESET = "\033[0m"

        for r in self.results:
            status = r.get("status", "unknown").upper()
            module = r.get("module", "unknown")
            target = r.get("target", "N/A")
            timestamp = r.get("timestamp", "")
            
            # Module header
            if status == "SUCCESS":
                lines.append(f"{C_BOLD}{C_GREEN}[+] {module.upper()} SUCCESS{C_RESET}")
            else:
                lines.append(f"{C_BOLD}{C_RED}[-] {module.upper()} ERROR{C_RESET}")

            lines.append(f"  {C_BOLD}Target:{C_RESET} {target}")
            if timestamp:
                lines.append(f"  {C_BOLD}Time  :{C_RESET} {timestamp}")
            lines.append("")

            # Format body depending on success / error
            if status == "SUCCESS":
                data = r.get("data", {})
                
                # Module specific formatters
                if module == "scan":
                    open_ports = data.get("open_ports", [])
                    lines.append(f"  {C_CYAN}{C_BOLD}Open Ports discovered on {data.get('ip')}:{C_RESET}")
                    if open_ports:
                        lines.append(f"    {C_BOLD}{'Port':<8} {'Service':<12}{C_RESET}")
                        lines.append(f"    {'-'*4}     {'-'*7}")
                        for p in open_ports:
                            lines.append(f"    {p.get('port'):<8} {p.get('service'):<12}")
                    else:
                        lines.append("    No open ports detected in the scanned range.")
                
                elif module == "netscan":
                    alive = data.get("alive_hosts", [])
                    lines.append(f"  {C_CYAN}{C_BOLD}Network Discovery Results for {data.get('network')}:{C_RESET}")
                    lines.append(f"    Discovered {data.get('count', 0)} alive hosts:")
                    for host in alive:
                        lines.append(f"    - {host.get('ip')} (Probe Port: {host.get('port')})")
                
                elif module == "footprint":
                    lines.append(f"  {C_CYAN}{C_BOLD}DNS Resolution & Reverse Lookup:{C_RESET}")
                    lines.append(f"    {C_BOLD}Domain      :{C_RESET} {data.get('domain')}")
                    lines.append(f"    {C_BOLD}Resolved IP :{C_RESET} {data.get('ip')}")
                    lines.append(f"    {C_BOLD}Reverse DNS :{C_RESET} {data.get('hostname') or 'N/A'}")
                
                elif module == "geoip":
                    lines.append(f"  {C_CYAN}{C_BOLD}GeoIP Location Intelligence:{C_RESET}")
                    lines.append(f"    {C_BOLD}Country     :{C_RESET} {data.get('country')}")
                    lines.append(f"    {C_BOLD}Region/City :{C_RESET} {data.get('region')} / {data.get('city')}")
                    lines.append(f"    {C_BOLD}ISP / Org   :{C_RESET} {data.get('isp')} / {data.get('org')}")
                    lines.append(f"    {C_BOLD}Coordinates :{C_RESET} {data.get('lat')}, {data.get('lon')}")
                
                elif module == "whois":
                    lines.append(f"  {C_CYAN}{C_BOLD}WHOIS Registry Query:{C_RESET}")
                    lines.append(f"    {C_BOLD}Server Used :{C_RESET} {data.get('server_used')}")
                    lines.append(f"    {C_BOLD}Raw Result Snippet (First 15 lines):{C_RESET}")
                    lines.append("    " + "-" * 50)
                    raw_lines = str(data.get("raw", "")).splitlines()[:15]
                    for line in raw_lines:
                        lines.append(f"      {line}")
                    if len(raw_lines) >= 15:
                        lines.append("      ... [Output truncated. Log has full data.]")
                    lines.append("    " + "-" * 50)
                
                elif module == "subdomain":
                    subdomains = data.get("subdomains", [])
                    lines.append(f"  {C_CYAN}{C_BOLD}Subdomain Enumeration for {data.get('domain')}:{C_RESET}")
                    lines.append(f"    {C_BOLD}Sources     :{C_RESET} crt.sh (Passive) | Wordlist ({'Enabled' if data.get('sources', {}).get('wordlist') else 'Disabled'})")
                    lines.append(f"    {C_BOLD}Total Found :{C_RESET} {data.get('total_count', 0)}")
                    if subdomains:
                        lines.append("    Discovered Subdomains:")
                        for s in subdomains[:30]:
                            lines.append(f"    - {s}")
                        if len(subdomains) > 30:
                            lines.append(f"    ... and {len(subdomains) - 30} more (see logs/report for full list)")
                
                elif module == "tech":
                    frameworks = data.get("frameworks", [])
                    lines.append(f"  {C_CYAN}{C_BOLD}Technology Stack Discovery:{C_RESET}")
                    lines.append(f"    {C_BOLD}URL         :{C_RESET} {data.get('url')}")
                    lines.append(f"    {C_BOLD}Web Server  :{C_RESET} {data.get('server') or 'N/A'}")
                    lines.append(f"    {C_BOLD}X-Powered-By:{C_RESET} {data.get('x_powered_by') or 'N/A'}")
                    if frameworks:
                        lines.append(f"    {C_BOLD}Frameworks  :{C_RESET} {', '.join(frameworks)}")
                    else:
                        lines.append(f"    {C_BOLD}Frameworks  :{C_RESET} None detected")
                
                elif module == "crawl":
                    links = data.get("links", [])
                    forms = data.get("forms", [])
                    lines.append(f"  {C_CYAN}{C_BOLD}Lightweight Page Crawl Information:{C_RESET}")
                    lines.append(f"    {C_BOLD}Final URL   :{C_RESET} {data.get('url')}")
                    lines.append(f"    {C_BOLD}Status Code :{C_RESET} {data.get('status_code')}")
                    lines.append(f"    {C_BOLD}Page Title  :{C_RESET} '{data.get('title') or 'N/A'}'")
                    lines.append(f"    {C_BOLD}Links Found :{C_RESET} {len(links)}")
                    lines.append(f"    {C_BOLD}Forms Found :{C_RESET} {len(forms)}")
                    
                    if forms:
                        lines.append("    Forms:")
                        for f in forms[:5]:
                            inputs_desc = ", ".join([f"{inp.get('name')} [{inp.get('type')}]" for inp in f.get("inputs", [])])
                            lines.append(f"      - {f.get('method')} -> {f.get('action')} (Inputs: {inputs_desc or 'None'})")
                        if len(forms) > 5:
                            lines.append(f"      ... and {len(forms) - 5} more forms")
                    
                    if links:
                        lines.append("    Discovered Links (First 10):")
                        for l in links[:10]:
                            lines.append(f"      - {l}")
                        if len(links) > 10:
                            lines.append(f"      ... and {len(links) - 10} more links")

                elif module == "help":
                    lines.append(str(data))
                
                elif module == "version":
                    lines.append(f"  {C_CYAN}{C_BOLD}{data.get('name') or 'Corvus Corax'} {data.get('version') or 'v0.5'}{C_RESET}")
                    lines.append(f"  Motto: {data.get('motto') or ''}")

                elif module == "nexus":
                    stats = data.get("stats", {})
                    dist = data.get("risk_distribution", {})
                    profiles = data.get("risk_profiles", [])
                    threats = data.get("threat_findings", [])

                    lines.append(f"  {C_MAGENTA}{C_BOLD}NEXUS CORE CORRELATION ENGINE SUMMARY{C_RESET}")
                    lines.append(f"  {'='*45}")
                    lines.append(f"  {C_CYAN}{C_BOLD}[+] Intelligence Summary Stats:{C_RESET}")
                    lines.append(f"    - Total Monitored Entities : {stats.get('total_entities', 0)}")
                    lines.append(f"    - Raw Collected Relations  : {stats.get('total_raw_relations', 0)}")
                    lines.append(f"    - Inferred Nexus Relations : {stats.get('total_derived_relations', 0)}")
                    lines.append("")

                    # Risk distribution bar chart
                    lines.append(f"  {C_CYAN}{C_BOLD}[+] Asset Risk Distribution:{C_RESET}")
                    max_val = max(dist.values()) if dist and dist.values() else 0
                    for level in ("Critical", "High", "Medium", "Low"):
                        val = dist.get(level, 0)
                        stars_count = int(val * 10 / max_val) if max_val > 0 else 0
                        stars = "*" * stars_count
                        color = C_RESET
                        if level == "Critical": color = C_RED + C_BOLD
                        elif level == "High": color = C_RED
                        elif level == "Medium": color = C_YELLOW
                        elif level == "Low": color = C_GREEN
                        lines.append(f"    - {color}{level:<9}{C_RESET} : [{stars:<10}] {val}")
                    lines.append("")

                    # Threat findings
                    if threats:
                        lines.append(f"  {C_YELLOW}{C_BOLD}[!] Inferred Security Alerts:{C_RESET}")
                        for t in threats:
                            ent = t.get("entity")
                            t_type = t.get("type")
                            desc = t.get("description")
                            conf = t.get("confidence", 1.0)
                            lines.append(f"    - {C_RED}{C_BOLD}[{t_type}]{C_RESET} {ent}: {desc} (Confidence: {conf})")
                        lines.append("")

                    # Asset profiles and evidence
                    if profiles:
                        lines.append(f"  {C_CYAN}{C_BOLD}[+] Detailed Risk Profiles & Evidence:{C_RESET}")
                        sorted_profiles = sorted(profiles, key=lambda x: x.get("score", 0), reverse=True)
                        for p in sorted_profiles:
                            val = p.get("value")
                            p_type = p.get("type")
                            score = p.get("score")
                            level = p.get("level")
                            ev = p.get("evidence", [])

                            color = C_RESET
                            if level == "Critical": color = C_RED + C_BOLD
                            elif level == "High": color = C_RED
                            elif level == "Medium": color = C_YELLOW
                            elif level == "Low": color = C_GREEN

                            lines.append(f"    * ({p_type}) {C_BOLD}{val}{C_RESET} -> Risk Score: {color}{score} ({level}){C_RESET}")
                            if ev:
                                lines.append("      Evidence:")
                                for e in ev:
                                    lines.append(f"        - {e}")

                else:
                    lines.append(f"  {C_BOLD}Result Data:{C_RESET}")
                    lines.append(str(data))
                
            else:
                lines.append(f"  {C_BOLD}{C_RED}Error details:{C_RESET} {r.get('error', 'Unknown error')}")

            # Notes
            notes = r.get("notes", [])
            if notes:
                lines.append("")
                lines.append(f"  {C_BOLD}{C_YELLOW}[*] MODULE NOTES{C_RESET}")
                for note in notes:
                    text = note.get("text")
                    severity = str(note.get("severity", "info")).upper()
                    conf = note.get("confidence", 1.0)
                    lines.append(f"    - [{severity}] {text} (Confidence: {conf})")

            # Relationships (Nexus)
            relationships = r.get("relationships", [])
            if relationships:
                lines.append("")
                lines.append(f"  {C_BOLD}{C_MAGENTA}[*] NEXUS INTELLIGENCE RELATIONSHIPS{C_RESET}")
                for rel in relationships:
                    src = rel.get("src", {})
                    dst = rel.get("dst", {})
                    relation = rel.get("relation")
                    evidence = rel.get("evidence") or "N/A"
                    conf = rel.get("confidence", 1.0)
                    
                    src_str = f"({src.get('type')}) {src.get('value')}"
                    dst_str = f"({dst.get('type')}) {dst.get('value')}"
                    lines.append(f"    - {src_str} {C_BOLD}{C_CYAN}==[{relation}]==>{C_RESET} {dst_str} [Evidence: {evidence}, Conf: {conf}]")

            lines.append("")
            lines.append("-" * 65)

        return "\n".join(lines)