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
            module = r.get("module", "unknown")
            status = r.get("status", "unknown")
            target = r.get("target", "N/A")
            self.logger.info(f"[{module}] status={status} target={target}")

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

        # UI-only modules that manage their own output — no status header
        SILENT_HEADER_MODULES = {"help", "version"}

        for r in self.results:
            status = r.get("status", "unknown").upper()
            module = r.get("module", "unknown")
            target = r.get("target", "N/A")
            timestamp = r.get("timestamp", "")

            # Module header — suppressed for clean UI modules
            if module not in SILENT_HEADER_MODULES:
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

                    # --- Analyst Assessment ---
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if open_ports:
                        open_p_names = [f"{p['port']}/{p['service']}" for p in open_ports[:5]]
                        lines.append(f"      {C_CYAN}* Attack Surface Discovered: {len(open_ports)} exposed port(s) [{', '.join(open_p_names)}].{C_RESET}")
                        if any(p['port'] in (21, 23, 3389, 5900) for p in open_ports):
                            lines.append(f"      {C_RED}* High Risk Management Service: Remote administration/file transfer service exposed directly to network.{C_RESET}")
                    else:
                        lines.append(f"      {C_GREEN}* Minimal Surface Exposure: No open TCP services identified in scanned port profile.{C_RESET}")
                
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
                    sources = data.get("sources", {})
                    active_sources = [k for k, v in sources.items() if v]
                    total_count = data.get("total_count", data.get("counts", {}).get("total", len(subdomains)))
                    
                    lines.append(f"  {C_CYAN}{C_BOLD}Subdomain Enumeration for {data.get('domain')}:{C_RESET}")
                    lines.append(f"    {C_BOLD}Active Sources:{C_RESET} {', '.join(active_sources) if active_sources else 'None'}")
                    lines.append(f"    {C_BOLD}Total Found   :{C_RESET} {total_count}")
                    if subdomains:
                        lines.append("    Discovered Subdomains:")
                        for s in subdomains[:30]:
                            lines.append(f"    - {s}")
                        if len(subdomains) > 30:
                            lines.append(f"    ... and {len(subdomains) - 30} more (see logs/report for full list)")
                
                elif module == "cert":
                    expired       = data.get("expired", False)
                    days_rem      = data.get("days_remaining", 0)
                    is_wildcard   = data.get("wildcard", False)
                    wildcards     = data.get("wildcards", [])
                    san_list      = data.get("san", [])

                    # Expiry indicator
                    if expired:
                        expiry_label = f"{C_RED}{C_BOLD}EXPIRED{C_RESET}"
                    elif days_rem < 30:
                        expiry_label = f"{C_YELLOW}{C_BOLD}EXPIRING SOON ({days_rem}d){C_RESET}"
                    else:
                        expiry_label = f"{C_GREEN}Valid — {days_rem} days remaining{C_RESET}"

                    wildcard_label = f"{C_YELLOW}YES — {', '.join(wildcards)}{C_RESET}" if is_wildcard else "No"

                    lines.append(f"  {C_CYAN}{C_BOLD}Certificate Intelligence for {data.get('host')}:{data.get('port', 443)}{C_RESET}")
                    lines.append(f"    {C_BOLD}Subject CN    :{C_RESET} {data.get('subject_cn') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Organization  :{C_RESET} {data.get('organization') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Country       :{C_RESET} {data.get('country') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Issuer        :{C_RESET} {data.get('issuer') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Valid From    :{C_RESET} {data.get('valid_from') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Valid To      :{C_RESET} {data.get('valid_to') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Status        :{C_RESET} {expiry_label}")
                    lines.append(f"    {C_BOLD}Wildcard      :{C_RESET} {wildcard_label}")
                    if san_list:
                        lines.append(f"    {C_BOLD}SAN ({len(san_list)} entries):{C_RESET}")
                        for s in san_list[:10]:
                            lines.append(f"      - {s}")
                        if len(san_list) > 10:
                            lines.append(f"      ... and {len(san_list) - 10} more")
                    lines.append(f"    {C_BOLD}Serial No.    :{C_RESET} {data.get('serial_number') or 'N/A'}")
                    lines.append(f"    {C_BOLD}SHA-256       :{C_RESET} {data.get('fingerprint', 'N/A')[:59]}...")

                    # --- Analyst Assessment ---
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if is_wildcard:
                        lines.append(f"      {C_CYAN}* Wildcard certificate detected ({', '.join(wildcards)}). Represents centralized TLS termination.{C_RESET}")
                    if san_list and len(san_list) > 1:
                        lines.append(f"      {C_CYAN}* Certificate exposes {len(san_list)} SAN endpoints. Excellent asset discovery footprint.{C_RESET}")
                    if expired:
                        lines.append(f"      {C_RED}* CRITICAL: Certificate is EXPIRED. Users face TLS trust warnings.{C_RESET}")
                    elif days_rem < 30:
                        lines.append(f"      {C_YELLOW}* WARNING: Certificate expires in {days_rem} days. Renewal required.{C_RESET}")

                elif module == "dns":
                    domain = data.get("domain")
                    a_records = data.get("A", [])
                    aaaa_records = data.get("AAAA", [])
                    ns_records = data.get("NS", [])
                    mx_records = data.get("MX", [])
                    caa_records = data.get("CAA", [])
                    spf = data.get("spf")
                    dmarc = data.get("dmarc")
                    dkim = data.get("dkim", {})

                    # Email security indicators
                    if not spf:
                        spf_status = f"{C_RED}{C_BOLD}Missing (No SPF spoofing protection){C_RESET}"
                    elif data.get("spf_weak", False):
                        spf_status = f"{C_RED}{C_BOLD}WEAK ({spf}){C_RESET}"
                    else:
                        spf_status = f"{C_GREEN}Valid ({spf}){C_RESET}"

                    if not dmarc:
                        dmarc_status = f"{C_YELLOW}{C_BOLD}Missing (No DMARC spoofing policy){C_RESET}"
                    elif data.get("dmarc_weak", False):
                        dmarc_status = f"{C_YELLOW}{C_BOLD}Weak policy ({dmarc}){C_RESET}"
                    else:
                        dmarc_status = f"{C_GREEN}Strong policy ({dmarc}){C_RESET}"

                    lines.append(f"  {C_CYAN}{C_BOLD}DNS Intelligence & Email Security for {domain}:{C_RESET}")
                    
                    if a_records:
                        lines.append(f"    {C_BOLD}A Records     :{C_RESET} {', '.join(a_records)}")
                    if aaaa_records:
                        lines.append(f"    {C_BOLD}AAAA Records  :{C_RESET} {', '.join(aaaa_records)}")
                    if ns_records:
                        lines.append(f"    {C_BOLD}Nameservers   :{C_RESET} {', '.join(ns_records)}")
                    
                    if mx_records:
                        lines.append(f"    {C_BOLD}Mail Servers  :{C_RESET}")
                        for mx in mx_records:
                            lines.append(f"      - {mx['host']} (Priority: {mx['priority']})")

                    lines.append(f"    {C_BOLD}SPF Status    :{C_RESET} {spf_status}")
                    lines.append(f"    {C_BOLD}DMARC Status  :{C_RESET} {dmarc_status}")
                    
                    if dkim:
                        lines.append(f"    {C_BOLD}DKIM Keys ({len(dkim)} found):{C_RESET}")
                        for sel, key in dkim.items():
                            lines.append(f"      - {sel}._domainkey: {key[:50]}...")
                    else:
                        lines.append(f"    {C_BOLD}DKIM Keys     :{C_RESET} No keys found in tested selectors.")
                    
                    if caa_records:
                        lines.append(f"    {C_BOLD}CAA Records   :{C_RESET} {', '.join(caa_records)}")

                    # --- Analyst Assessment ---
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if not spf or data.get("spf_weak"):
                        lines.append(f"      {C_RED}* Vulnerable to Email Spoofing: SPF record is weak or unconfigured.{C_RESET}")
                    if not dmarc or data.get("dmarc_weak"):
                        lines.append(f"      {C_YELLOW}* Weak DMARC Policy: Threat actors can forge organization emails in targeted phishing.{C_RESET}")
                    if mx_records:
                        lines.append(f"      {C_CYAN}* Mail Routing: Handled by {mx_records[0]['host']}.{C_RESET}")

                elif module == "headers":
                    h_data = data.get("headers", {})
                    cookies = data.get("cookies", [])
                    missing = data.get("missing_security_headers", [])
                    
                    lines.append(f"  {C_CYAN}{C_BOLD}HTTP Header Analysis for {data.get('url')}:{C_RESET}")
                    
                    # Web server stack info
                    lines.append(f"    {C_BOLD}Server Stack  :{C_RESET}")
                    lines.append(f"      - Server      : {h_data.get('server') or 'N/A'}")
                    lines.append(f"      - X-Powered-By: {h_data.get('x-powered-by') or 'N/A'}")
                    if h_data.get("x-aspnet-version"):
                        lines.append(f"      - ASP.NET Ver : {h_data.get('x-aspnet-version')}")
                        
                    # Security compliance headers
                    def check_header(name):
                        val = h_data.get(name.lower())
                        if val:
                            return f"{C_GREEN}Present{C_RESET} ({val[:40]}...)" if len(val) > 40 else f"{C_GREEN}Present{C_RESET} ({val})"
                        return f"{C_RED}{C_BOLD}Missing{C_RESET}"
                        
                    lines.append(f"    {C_BOLD}Security Posture:{C_RESET}")
                    lines.append(f"      - Content-Security-Policy (CSP) : {check_header('Content-Security-Policy')}")
                    lines.append(f"      - Strict-Transport-Security (HSTS): {check_header('Strict-Transport-Security')}")
                    lines.append(f"      - X-Frame-Options (XFO)           : {check_header('X-Frame-Options')}")
                    lines.append(f"      - X-Content-Type-Options (XCTO)   : {check_header('X-Content-Type-Options')}")
                    lines.append(f"      - Referrer-Policy                 : {check_header('Referrer-Policy')}")
                    
                    # Access Control
                    lines.append(f"    {C_BOLD}Access Control (CORS):{C_RESET}")
                    lines.append(f"      - Access-Control-Allow-Origin     : {h_data.get('access-control-allow-origin') or 'N/A'}")
                    lines.append(f"      - Access-Control-Allow-Credentials: {h_data.get('access-control-allow-credentials') or 'N/A'}")
                    
                    # Cache & Encoding
                    lines.append(f"    {C_BOLD}Performance & Caching:{C_RESET}")
                    lines.append(f"      - Cache-Control : {h_data.get('cache-control') or 'N/A'}")
                    lines.append(f"      - Content-Encoding: {h_data.get('content-encoding') or 'N/A'}")
                    
                    # Cookies
                    if cookies:
                        lines.append(f"    {C_BOLD}Set-Cookie Headers ({len(cookies)} found):{C_RESET}")
                        for c in cookies:
                            flags = []
                            if c.get("httponly"):
                                flags.append(f"{C_GREEN}HttpOnly{C_RESET}")
                            else:
                                flags.append(f"{C_RED}HttpOnly missing{C_RESET}")
                                
                            if c.get("secure"):
                                flags.append(f"{C_GREEN}Secure{C_RESET}")
                            else:
                                flags.append(f"{C_RED}Secure missing{C_RESET}")
                                
                            if c.get("samesite"):
                                flags.append(f"SameSite={c.get('samesite')}")
                                
                            lines.append(f"      - {c.get('name')} = {c.get('value')} [{', '.join(flags)}]")
                    else:
                        lines.append(f"    {C_BOLD}Cookies       :{C_RESET} No cookies set in response.")

                elif module == "email":
                    provider      = data.get("provider")
                    prov_evidence = data.get("provider_evidence")
                    report_emails = data.get("dmarc_report_emails", [])
                    sample_emails = data.get("sample_emails", [])
                    pattern       = data.get("detected_pattern")
                    pat_conf      = data.get("pattern_confidence", 0)
                    formats       = data.get("suggested_formats", [])
                    domain_name   = data.get("domain")

                    role_emails   = data.get("role_emails", [])
                    personal_emails = data.get("personal_emails", [])

                    lines.append(f"  {C_CYAN}{C_BOLD}Email Intelligence for {domain_name}:{C_RESET}")

                    # Provider
                    if provider:
                        lines.append(f"    {C_BOLD}Email Provider :{C_RESET} {C_GREEN}{provider}{C_RESET}")
                        lines.append(f"    {C_BOLD}Evidence       :{C_RESET} {prov_evidence}")
                    else:
                        lines.append(f"    {C_BOLD}Email Provider :{C_RESET} {C_YELLOW}Unknown - run 'dns' first{C_RESET}")

                    # Role/System Emails
                    if role_emails:
                        lines.append(f"    {C_BOLD}Role/System Mailboxes ({len(role_emails)}):{C_RESET}")
                        for addr in role_emails:
                            lines.append(f"      - {C_YELLOW}{addr}{C_RESET}")
                    else:
                        lines.append(f"    {C_BOLD}Role/System Mailboxes : {C_RESET}None found")

                    # Personal Contacts
                    if personal_emails:
                        lines.append(f"    {C_BOLD}Personal Contacts ({len(personal_emails)}):{C_RESET}")
                        for addr in personal_emails:
                            lines.append(f"      - {C_GREEN}{addr}{C_RESET}")

                    # DMARC reporting addresses
                    if report_emails:
                        lines.append(f"    {C_BOLD}DMARC Report Inboxes ({len(report_emails)}):{C_RESET}")
                        for addr in report_emails:
                            lines.append(f"      - {C_YELLOW}{addr}{C_RESET}")

                    # Pattern
                    if pat_conf >= 0.85:
                        conf_color = C_GREEN
                    elif pat_conf >= 0.6:
                        conf_color = C_YELLOW
                    else:
                        conf_color = C_RED

                    lines.append(f"    {C_BOLD}Detected Pattern:{C_RESET} "
                                 f"{conf_color}{pattern}{C_RESET}  "
                                 f"(confidence: {conf_color}{int(pat_conf * 100)}%{C_RESET})")


                    # Format suggestions
                    if formats:
                        lines.append(f"    {C_BOLD}Suggested Formats:{C_RESET}")
                        for fmt in formats[:6]:
                            c = fmt["confidence"]
                            col = C_GREEN if c == "HIGH" else (C_YELLOW if c == "MEDIUM" else C_RED)
                            lines.append(f"      [{col}{c:6}{C_RESET}] {fmt['format']}")

                    # --- Analyst Assessment ---
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if isinstance(pattern, dict) and pattern.get("is_personal_leak"):
                        lines.append(f"      {C_RED}* Personal Email Exposure: DMARC reports route to personal inbox ({pattern.get('example_email')}). Target for spear-phishing.{C_RESET}")
                    if pattern and isinstance(pattern, str):
                        lines.append(f"      {C_CYAN}* Naming Standard: Target uses '{pattern}' structure across corporate inboxes.{C_RESET}")

                elif module == "metadata":
                    domain_name = data.get("domain")
                    robots      = data.get("robots") or {}
                    sitemap     = data.get("sitemap") or {}
                    sec_txt     = data.get("security_txt") or {}
                    humans      = data.get("humans_txt") or {}
                    favicon     = data.get("favicon") or {}

                    lines.append(f"  {C_CYAN}{C_BOLD}Metadata Intelligence for {domain_name}:{C_RESET}")

                    # --- robots.txt ---
                    if robots:
                        lines.append(f"    {C_BOLD}robots.txt:{C_RESET}")
                        lines.append(f"      Disallowed : {len(robots.get('disallowed', []))} path(s)")
                        lines.append(f"      Sitemaps   : {len(robots.get('sitemaps', []))} reference(s)")
                        sensitive = robots.get("sensitive_paths", [])
                        if sensitive:
                            lines.append(f"      {C_RED}{C_BOLD}Sensitive Paths ({len(sensitive)}):{C_RESET}")
                            for sp in sensitive[:10]:
                                lines.append(f"        {C_RED}- {sp}{C_RESET}")
                    else:
                        lines.append(f"    {C_BOLD}robots.txt    :{C_RESET} Not found")

                    # --- sitemap.xml ---
                    if sitemap:
                        lines.append(f"    {C_BOLD}sitemap.xml:{C_RESET}")
                        lines.append(f"      Total URLs : {sitemap.get('total_urls', 0)}")
                    else:
                        lines.append(f"    {C_BOLD}sitemap.xml   :{C_RESET} Not found")

                    # --- security.txt ---
                    if sec_txt:
                        contacts = sec_txt.get("contacts", [])
                        emails   = sec_txt.get("emails", [])
                        policy   = sec_txt.get("policy")
                        lines.append(f"    {C_BOLD}security.txt:{C_RESET}")
                        if emails:
                            lines.append(f"      {C_GREEN}Security Contacts:{C_RESET}")
                            for e in emails:
                                lines.append(f"        - {C_GREEN}{e}{C_RESET}")
                        if policy:
                            lines.append(f"      Policy URL : {policy}")
                    else:
                        lines.append(f"    {C_BOLD}security.txt  :{C_RESET} Not found")

                    # --- humans.txt ---
                    if humans:
                        h_emails = humans.get("emails", [])
                        h_tech   = humans.get("tech_hints", [])
                        lines.append(f"    {C_BOLD}humans.txt:{C_RESET}")
                        if h_emails:
                            lines.append(f"      {C_YELLOW}Staff Emails ({len(h_emails)}):{C_RESET}")
                            for e in h_emails:
                                lines.append(f"        - {C_YELLOW}{e}{C_RESET}")
                        if h_tech:
                            lines.append(f"      Tech Hints : {', '.join(h_tech[:3])}")
                    else:
                        lines.append(f"    {C_BOLD}humans.txt    :{C_RESET} Not found")

                    # --- favicon ---
                    if favicon:
                        fhash = favicon.get("shodan_hash")
                        furl  = favicon.get("url")
                        lines.append(f"    {C_BOLD}favicon.ico:{C_RESET}")
                        lines.append(f"      URL        : {furl}")
                        lines.append(f"      MD5        : {favicon.get('md5')}")
                        lines.append(f"      {C_CYAN}Shodan Hash: {fhash}{C_RESET}")
                        lines.append(f"      {C_CYAN}Shodan Query: http.favicon.hash:{fhash}{C_RESET}")
                    else:
                        lines.append(f"    {C_BOLD}favicon.ico   :{C_RESET} Not found")

                    # --- Analyst Assessment ---
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if robots and robots.get("sensitive_paths"):
                        lines.append(f"      {C_RED}* Sensitive Path Disclosure: {len(robots['sensitive_paths'])} path(s) exposed in robots.txt.{C_RESET}")
                    if sec_txt and sec_txt.get("emails"):
                        lines.append(f"      {C_GREEN}* Verified Security Contact: {', '.join(sec_txt['emails'])} extracted from security.txt.{C_RESET}")
                    if favicon and favicon.get("shodan_hash"):
                        lines.append(f"      {C_CYAN}* Favicon Hash Fingerprinted: Use Shodan query 'http.favicon.hash:{favicon['shodan_hash']}' to locate hidden origin servers.{C_RESET}")

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

                    # --- Analyst Assessment ---
                    waf_cdn = data.get("waf_cdn", [])
                    cms = data.get("cms", [])
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if waf_cdn:
                        lines.append(f"      {C_CYAN}* Active WAF/CDN Protection: {', '.join(w['name'] for w in waf_cdn)} detected.{C_RESET}")
                    if cms:
                        lines.append(f"      {C_YELLOW}* CMS Fingerprinted: {', '.join(c['name'] for c in cms)}. Evaluate version against public CVE databases.{C_RESET}")
                    if data.get("stack_profile"):
                        lines.append(f"      {C_CYAN}* Stack Profile: {data.get('stack_profile')}{C_RESET}")
                
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

                elif module == "phone":
                    phone = data.get("phone")
                    country_code = data.get("country_code")
                    local_number = data.get("local_number")
                    number_type = data.get("number_type")
                    operator_info = data.get("operator_prefix") or {}
                    person_candidate = data.get("person_candidate")

                    lines.append(f"  {C_CYAN}{C_BOLD}Phone Intelligence — {phone}:{C_RESET}")
                    lines.append(f"    {C_BOLD}E.164         :{C_RESET} {phone}")
                    lines.append(f"    {C_BOLD}Country Code  :{C_RESET} {country_code or 'Unknown'}")
                    lines.append(f"    {C_BOLD}Local Number  :{C_RESET} {local_number}")
                    lines.append(f"    {C_BOLD}Number Type   :{C_RESET} {number_type}")

                    # Operatör prefix (candidate — kesin değil)
                    possible_op = operator_info.get("possible_operator")
                    prefix = operator_info.get("prefix_detected")
                    basis = operator_info.get("basis")
                    op_conf = operator_info.get("confidence", 0)
                    if possible_op and possible_op != "Unknown":
                        lines.append(f"    {C_BOLD}Operator      :{C_RESET} {possible_op}")
                        lines.append(f"      {C_BOLD}Prefix Detected:{C_RESET} {prefix}")
                        lines.append(f"      {C_BOLD}Basis          :{C_RESET} {basis}")
                        lines.append(f"      {C_BOLD}Confidence     :{C_RESET} {op_conf} {C_YELLOW}(candidate — MNP may apply){C_RESET}")
                    else:
                        lines.append(f"    {C_BOLD}Operator      :{C_RESET} {C_YELLOW}Unknown prefix (no match){C_RESET}")

                    # Kişi adayı (candidate_link)
                    if person_candidate:
                        lines.append(f"    {C_BOLD}Person Candidate:{C_RESET} {person_candidate} {C_YELLOW}(candidate — unverified ownership){C_RESET}")

                    # Temporal event note
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if number_type == "mobile":
                        lines.append(f"      {C_CYAN}* Mobile number classified ({number_type}).{C_RESET}")
                    if possible_op and possible_op != "Unknown":
                        lines.append(f"      {C_YELLOW}* Operator '{possible_op}' is a PREFIX-BASED estimate (basis: {basis}).{C_RESET}")
                        lines.append(f"        Number portability (MNP) may mean actual operator differs.{C_RESET}")
                    if person_candidate:
                        lines.append(f"      {C_YELLOW}* Phone linked to {person_candidate} as CANDIDATE — requires verification.{C_RESET}")

                elif module == "social":
                    username = data.get("username")
                    platforms_found = data.get("platforms_found", [])
                    platforms_checked = data.get("platforms_checked", 0)
                    confidence = data.get("correlation_confidence", 0)
                    person_candidate = data.get("person_candidate")
                    verified_profiles = data.get("verified_profiles", [])

                    lines.append(f"  {C_CYAN}{C_BOLD}Social Media Intelligence — {username}:{C_RESET}")
                    lines.append(f"    {C_BOLD}Platforms Checked :{C_RESET} {platforms_checked}")

                    if platforms_found:
                        lines.append(f"    {C_BOLD}Platforms Found   :{C_RESET} {', '.join(platforms_found)}")
                        lines.append(f"    {C_BOLD}Correlation Conf  :{C_RESET} {confidence:.2f} {C_YELLOW}(possible match — not confirmed){C_RESET}")
                    else:
                        lines.append(f"    {C_BOLD}Platforms Found   :{C_RESET} {C_YELLOW}None (offline or blocked){C_RESET}")

                    # Doğrulanmış profiller
                    if verified_profiles:
                        lines.append(f"\n    {C_BOLD}Verified Profiles:{C_RESET}")
                        for pr in verified_profiles:
                            lines.append(f"      - {C_GREEN}{pr.get('platform')}:{C_RESET} {pr.get('url')}")
                    else:
                        lines.append(f"\n    {C_BOLD}Verified Profiles:{C_RESET} None")

                    # Kişi adayı
                    if person_candidate:
                        lines.append(f"    {C_BOLD}Person Candidate :{C_RESET} {person_candidate} {C_YELLOW}(possible — username may belong to different person){C_RESET}")

                    # Analyst Assessment
                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if len(platforms_found) >= 2:
                        lines.append(f"      {C_YELLOW}* Same username on {len(platforms_found)} platforms suggests POSSIBLE same person.{C_RESET}")
                        lines.append(f"        Not confirmed — different people may use the same handle.{C_RESET}")
                    elif len(platforms_found) == 1:
                        lines.append(f"      {C_CYAN}* Username found on 1 platform only — low correlation confidence.{C_RESET}")
                    else:
                        lines.append(f"      {C_YELLOW}* No verified profiles found — username may not exist or platform blocks bots.{C_RESET}")

                elif module == "org":
                    org_name = data.get("organization")
                    domain = data.get("domain")
                    person = data.get("person")
                    parent = data.get("parent")
                    infra = data.get("infra_correlations", [])

                    lines.append(f"  {C_CYAN}{C_BOLD}Organization Intelligence — {org_name}:{C_RESET}")
                    if domain:
                        lines.append(f"    {C_BOLD}Domain (candidate):{C_RESET} {domain} {C_YELLOW}(conf: 0.6){C_RESET}")
                    if person:
                        lines.append(f"    {C_BOLD}Person (candidate):{C_RESET} {person} {C_YELLOW}(conf: 0.4){C_RESET}")
                    if parent:
                        lines.append(f"    {C_BOLD}Parent Company   :{C_RESET} {parent}")
                    if infra:
                        lines.append(f"    {C_BOLD}Infra Correlations ({len(infra)}):{C_RESET}")
                        for match in infra[:10]:
                            lines.append(f"      - {match}")
                    else:
                        lines.append(f"    {C_BOLD}Infra Correlations:{C_RESET} None in current context")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if domain:
                        lines.append(f"      {C_YELLOW}* Domain ownership is CANDIDATE — verify via WHOIS/ASN records.{C_RESET}")
                    if person:
                        lines.append(f"      {C_YELLOW}* Employment is CANDIDATE — requires verification.{C_RESET}")

                elif module == "wallet":
                    address = data.get("address")
                    chain = data.get("chain")
                    explorer = data.get("explorer_url")
                    balance = data.get("balance_btc")
                    person_candidate = data.get("person_candidate")

                    lines.append(f"  {C_CYAN}{C_BOLD}Wallet Intelligence — {address[:16]}...:{C_RESET}")
                    lines.append(f"    {C_BOLD}Chain     :{C_RESET} {chain.upper()}")
                    lines.append(f"    {C_BOLD}Explorer  :{C_RESET} {explorer}")
                    if balance is not None:
                        lines.append(f"    {C_BOLD}Balance   :{C_RESET} {C_GREEN}{balance} BTC{C_RESET}")
                    if person_candidate:
                        lines.append(f"    {C_BOLD}Person    :{C_RESET} {person_candidate} {C_YELLOW}(candidate — wallets may be shared){C_RESET}")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    lines.append(f"      {C_YELLOW}* Wallet ownership is CANDIDATE — wallets can be shared or multi-sig.{C_RESET}")

                elif module == "academic":
                    person = data.get("person")
                    author_info = data.get("author_info") or {}
                    publications = data.get("publications", [])
                    university = data.get("university")

                    lines.append(f"  {C_CYAN}{C_BOLD}Academic Intelligence — {person}:{C_RESET}")
                    if author_info:
                        lines.append(f"    {C_BOLD}Name      :{C_RESET} {author_info.get('name')}")
                        lines.append(f"    {C_BOLD}ORCID     :{C_RESET} {author_info.get('orcid') or 'N/A'}")
                        lines.append(f"    {C_BOLD}h-index   :{C_RESET} {author_info.get('h_index') or 'N/A'}")
                        lines.append(f"    {C_BOLD}Works     :{C_RESET} {author_info.get('works_count', 0)}")
                        affs = author_info.get("affiliations", [])
                        if affs:
                            lines.append(f"    {C_BOLD}Affiliation:{C_RESET} {', '.join(affs[:3])}")
                    if university:
                        lines.append(f"    {C_BOLD}University :{C_RESET} {university} {C_YELLOW}(candidate — from email domain){C_RESET}")
                    if publications:
                        lines.append(f"    {C_BOLD}Publications ({len(publications)}):{C_RESET}")
                        for pub in publications[:5]:
                            year = pub.get("year")
                            title = pub.get("title", "Untitled")[:60]
                            lines.append(f"      - [{year}] {title}")
                        if len(publications) > 5:
                            lines.append(f"      ... and {len(publications) - 5} more")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if university:
                        lines.append(f"      {C_YELLOW}* Academic affiliation is CANDIDATE — verify via ORCID/OpenAlex.{C_RESET}")

                elif module == "breach":
                    email = data.get("email")
                    sources = data.get("breach_sources", [])
                    count = data.get("breach_count", 0)
                    risk = data.get("risk_level", "Low")
                    pwned = data.get("password_pwned_count", 0)

                    risk_color = C_GREEN
                    if risk == "Critical": risk_color = C_RED + C_BOLD
                    elif risk == "High": risk_color = C_RED
                    elif risk == "Medium": risk_color = C_YELLOW

                    lines.append(f"  {C_CYAN}{C_BOLD}Data Breach Intelligence — {email}:{C_RESET}")
                    lines.append(f"    {C_BOLD}Breach Sources :{C_RESET} {count}")
                    lines.append(f"    {C_BOLD}Risk Level     :{C_RESET} {risk_color}{risk}{C_RESET}")
                    if sources:
                        lines.append(f"    {C_BOLD}Sources        :{C_RESET} {', '.join(sources[:8])}")
                    if pwned:
                        lines.append(f"    {C_BOLD}Password Pwned :{C_RESET} {C_RED}Yes ({pwned} breaches){C_RESET} {C_YELLOW}(k-anonymity check){C_RESET}")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    lines.append(f"      {C_YELLOW}* Meta-data only — no raw credentials stored or displayed.{C_RESET}")
                    if risk != "Low":
                        lines.append(f"      {C_RED}* Email exposed in {count} breaches — identity theft risk elevated.{C_RESET}")

                elif module == "github":
                    username = data.get("username")
                    user_info = data.get("user_info") or {}
                    repos = data.get("repos", [])
                    emails = data.get("commit_emails", [])
                    secrets = data.get("secret_findings", [])

                    lines.append(f"  {C_CYAN}{C_BOLD}GitHub Intelligence — {username}:{C_RESET}")
                    lines.append(f"    {C_BOLD}Name      :{C_RESET} {user_info.get('name') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Company   :{C_RESET} {user_info.get('company') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Location  :{C_RESET} {user_info.get('location') or 'N/A'}")
                    lines.append(f"    {C_BOLD}Repos     :{C_RESET} {len(repos)}")
                    lines.append(f"    {C_BOLD}Followers :{C_RESET} {user_info.get('followers', 0)}")
                    if repos:
                        lines.append(f"    {C_BOLD}Top Repos :{C_RESET}")
                        for repo in repos[:5]:
                            lang = repo.get('language') or 'N/A'
                            stars = repo.get('stars', 0)
                            lines.append(f"      - {repo.get('name')} [{lang}] ⭐{stars}")
                    if emails:
                        lines.append(f"    {C_BOLD}Emails    :{C_RESET} {', '.join(emails[:5])} {C_YELLOW}(candidate){C_RESET}")
                    if secrets:
                        lines.append(f"    {C_BOLD}Secrets   :{C_RESET} {C_RED}{len(secrets)} potential exposure(s){C_RESET}")
                        for s in secrets[:3]:
                            lines.append(f"      - {s.get('repo')}: {s.get('type')} {s.get('value')}")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if secrets:
                        lines.append(f"      {C_RED}* Potential secret exposure in public repos — investigate.{C_RESET}")
                    if emails:
                        lines.append(f"      {C_YELLOW}* Emails from commits are CANDIDATE associations.{C_RESET}")

                elif module == "wayback":
                    url = data.get("url")
                    snapshot = data.get("snapshot") or {}
                    records = data.get("historical_records", [])
                    count = data.get("record_count", 0)

                    lines.append(f"  {C_CYAN}{C_BOLD}Wayback Machine Intelligence — {url}:{C_RESET}")
                    if snapshot and snapshot.get("available"):
                        lines.append(f"    {C_BOLD}Snapshot   :{C_RESET} {C_GREEN}Available{C_RESET}")
                        lines.append(f"    {C_BOLD}Timestamp  :{C_RESET} {snapshot.get('timestamp')}")
                        lines.append(f"    {C_BOLD}Snapshot URL:{C_RESET} {snapshot.get('url')}")
                        lines.append(f"    {C_BOLD}Status     :{C_RESET} {snapshot.get('status')}")
                    else:
                        lines.append(f"    {C_BOLD}Snapshot   :{C_RESET} {C_YELLOW}Not archived{C_RESET}")
                    lines.append(f"    {C_BOLD}History    :{C_RESET} {count} CDX records")
                    if records:
                        lines.append(f"    {C_BOLD}Recent Records:{C_RESET}")
                        for rec in records[:5]:
                            ts = rec[0] if len(rec) > 0 else ""
                            status = rec[1] if len(rec) > 1 else ""
                            lines.append(f"      - {ts} (HTTP {status})")

                    lines.append(f"\n    {C_YELLOW}{C_BOLD}[Analyst Assessment]{C_RESET}")
                    if snapshot and snapshot.get("available"):
                        lines.append(f"      {C_CYAN}* Web history preserved — useful for content evolution analysis.{C_RESET}")

                elif module == "geoint":
                    export_type = data.get("export_type")
                    filepath = data.get("filepath")
                    message = data.get("message", "")

                    lines.append(f"  {C_MAGENTA}{C_BOLD}GEOINT VISUALIZATION — {export_type.upper()}{C_RESET}")
                    lines.append(f"  {'='*52}")
                    lines.append(f"  {C_GREEN}{C_BOLD}[+] {message}{C_RESET}")
                    lines.append(f"    {C_BOLD}File Path  :{C_RESET} {filepath}")

                    if export_type == "map":
                        lines.append(f"  {C_CYAN}Open the HTML file in a browser to view the interactive map.{C_RESET}")
                    elif export_type == "graph":
                        lines.append(f"  {C_CYAN}Open the HTML file in a browser to view the D3.js graph.{C_RESET}")
                    elif export_type == "timeline":
                        event_count = data.get("event_count", 0)
                        lines.append(f"    {C_BOLD}Events     :{C_RESET} {event_count}")
                        lines.append(f"  {C_CYAN}Timeline format is POL-ready (Pattern of Life).{C_RESET}")
                    elif export_type == "geojson":
                        feature_count = data.get("feature_count", 0)
                        lines.append(f"    {C_BOLD}Features   :{C_RESET} {feature_count}")
                        lines.append(f"  {C_CYAN}GeoJSON ready for QGIS/D3/other tools.{C_RESET}")

                elif module == "help":
                    lines.append(str(data))
                
                elif module == "version":
                    lines.append(f"  {C_CYAN}{C_BOLD}{data.get('name') or 'Corvus Corax'} {data.get('version') or 'v0.5'}{C_RESET}")
                    lines.append(f"  Motto: {data.get('motto') or ''}")

                elif module == "nexus":
                    export_type = data.get("export_type")
                    verbose = data.get("verbose", False)

                    # --- Export Sonucu Çıktısı ---
                    if export_type == "html":
                        lines.append(f"  {C_MAGENTA}{C_BOLD}NEXUS INTELLIGENCE DOSSIER — HTML EXPORT{C_RESET}")
                        lines.append(f"  {'='*52}")
                        lines.append(f"  {C_GREEN}{C_BOLD}[+] Report generated successfully.{C_RESET}")
                        lines.append(f"    {C_BOLD}File Path      :{C_RESET} {data.get('filepath')}")
                        lines.append(f"    {C_BOLD}Entities       :{C_RESET} {data.get('entities', 0)}")
                        lines.append(f"    {C_BOLD}Raw Relations  :{C_RESET} {data.get('relations', 0)}")
                        lines.append(f"    {C_BOLD}Nexus Derived  :{C_RESET} {data.get('derived_relations', 0)}")
                        lines.append(f"  {C_CYAN}Open the file in a browser to view the interactive dashboard.{C_RESET}")

                    elif export_type == "neo4j_json":
                        lines.append(f"  {C_MAGENTA}{C_BOLD}NEXUS INTELLIGENCE — NEO4J JSON EXPORT{C_RESET}")
                        lines.append(f"  {'='*52}")
                        lines.append(f"  {C_GREEN}{C_BOLD}[+] Graph schema exported successfully.{C_RESET}")
                        lines.append(f"    {C_BOLD}File Path      :{C_RESET} {data.get('filepath')}")
                        lines.append(f"    {C_BOLD}Graph Nodes    :{C_RESET} {data.get('nodes', 0)}")
                        lines.append(f"    {C_BOLD}Graph Edges    :{C_RESET} {data.get('relationships', 0)}")
                        lines.append(f"  {C_CYAN}Ready for LOAD CSV or APOC import into Neo4j.{C_RESET}")

                    elif export_type == "graph_json":
                        lines.append(f"  {C_MAGENTA}{C_BOLD}NEXUS INTELLIGENCE — GENERIC GRAPH JSON EXPORT{C_RESET}")
                        lines.append(f"  {'='*52}")
                        lines.append(f"  {C_GREEN}{C_BOLD}[+] Graph data exported successfully.{C_RESET}")
                        lines.append(f"    {C_BOLD}File Path      :{C_RESET} {data.get('filepath')}")
                        lines.append(f"    {C_BOLD}Graph Nodes    :{C_RESET} {data.get('nodes', 0)}")
                        lines.append(f"    {C_BOLD}Graph Edges    :{C_RESET} {data.get('edges', 0)}")
                        lines.append(f"    {C_BOLD}Format         :{C_RESET} {data.get('format', 'corvus_graph_v1')}")
                        lines.append(f"  {C_CYAN}Ready for AI/ML pipelines and visualization tools.{C_RESET}")

                    # --- Analiz Özeti Çıktısı ---
                    else:
                        stats = data.get("stats", {})
                        dist = data.get("risk_distribution", {})
                        profiles = data.get("risk_profiles", [])
                        threats = data.get("threat_findings", [])

                        lines.append(f"  {C_MAGENTA}{C_BOLD}NEXUS CORE CORRELATION ENGINE{C_RESET}")
                        lines.append(f"  {C_MAGENTA}{'='*52}{C_RESET}")
                        lines.append(f"  {C_CYAN}{C_BOLD}Intelligence Summary{C_RESET}")
                        lines.append(f"  {'-'*52}")
                        lines.append(f"  {'Entities Monitored':<30} {stats.get('total_entities', 0)}")
                        lines.append(f"  {'Raw Collected Relations':<30} {stats.get('total_raw_relations', 0)}")
                        lines.append(f"  {'Nexus Inferred Relations':<30} {C_MAGENTA}{stats.get('total_derived_relations', 0)}{C_RESET}")
                        lines.append("")

                        # Risk dağılım bar chart
                        lines.append(f"  {C_CYAN}{C_BOLD}Asset Risk Distribution{C_RESET}")
                        lines.append(f"  {'-'*52}")
                        max_val = max(dist.values()) if dist and any(dist.values()) else 1
                        for level in ("Critical", "High", "Medium", "Low"):
                            val = dist.get(level, 0)
                            bar_len = int(val * 20 / max_val) if max_val > 0 else 0
                            bar = "#" * bar_len
                            color = C_RESET
                            if level == "Critical": color = C_RED + C_BOLD
                            elif level == "High": color = C_RED
                            elif level == "Medium": color = C_YELLOW
                            elif level == "Low": color = C_GREEN
                            lines.append(f"  {color}{level:<10}{C_RESET} |{bar:<20}| {val}")
                        lines.append("")

                        # Tehdit uyarıları
                        if threats:
                            lines.append(f"  {C_RED}{C_BOLD}[!] Security Alerts{C_RESET}")
                            lines.append(f"  {'-'*52}")
                            for t in threats:
                                ent = t.get("entity")
                                t_type = t.get("type")
                                desc = t.get("description")
                                conf = t.get("confidence", 1.0)
                                lines.append(f"  {C_RED}{C_BOLD}[{t_type}]{C_RESET} {C_BOLD}{ent}{C_RESET}")
                                lines.append(f"    {desc}")
                                lines.append(f"    Confidence: {conf}")
                            lines.append("")

                        # Risk profilleri ve kanıtlar
                        if profiles:
                            lines.append(f"  {C_CYAN}{C_BOLD}Risk Profiles{C_RESET}")
                            lines.append(f"  {'-'*52}")
                            sorted_profiles = sorted(profiles, key=lambda x: x.get("score", 0), reverse=True)
                            for p in sorted_profiles:
                                val = p.get("value")
                                p_type = p.get("type")
                                score = p.get("score")
                                level = p.get("level")
                                admiralty_rating = p.get("admiralty_rating", "N/A")
                                evidence_count = p.get("evidence_count", 0)

                                color = C_RESET
                                if level == "Critical": color = C_RED + C_BOLD
                                elif level == "High": color = C_RED
                                elif level == "Medium": color = C_YELLOW
                                elif level == "Low": color = C_GREEN

                                bar_len = int(score / 5)
                                bar = "#" * bar_len
                                lines.append(f"  {C_BOLD}({p_type}) {val}{C_RESET}")
                                lines.append(f"    Risk Score: {color}{score:>3}/100 ({level}){C_RESET} [{bar:<20}]")
                                lines.append(f"    Admiralty Rating: {C_CYAN}{admiralty_rating}{C_RESET}")
                                
                                if verbose:
                                    # Verbose mode: show full evidence chain
                                    evidence_chain = p.get("evidence_chain", [])
                                    lines.append(f"    Evidence Chain ({evidence_count} items):")
                                    for i, ev in enumerate(evidence_chain, 1):
                                        ev_type = ev.get("type")
                                        adm_code = ev.get("admiralty_code")
                                        weighted_score = ev.get("weighted_score")
                                        description = ev.get("description")
                                        source = ev.get("source")
                                        
                                        lines.append(f"      {i}. {C_BOLD}{ev_type}{C_RESET} ({C_CYAN}{adm_code}{C_RESET}) - +{weighted_score} points")
                                        lines.append(f"         Source: {source}")
                                        lines.append(f"         {description}")
                                else:
                                    # Summary mode: just show count
                                    lines.append(f"    Evidence: {evidence_count} items (use --verbose for details)")

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