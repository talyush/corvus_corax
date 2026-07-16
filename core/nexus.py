import re
from datetime import datetime, timezone
from core.admiralty import AdmiraltyScorer, EvidenceType, SourceReliability, InformationReliability

class NexusEngine:
    """
    Corvus Corax v0.6 Nexus Correlation Çekirdek Motoru.
    Bağlam graflarını analiz ederek saklı ilişkileri türetir ve hedefleri risk puanına göre derecelendirir.
    """
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.risk_profiles = {}
        self.outdated_thresholds = {
            "apache": [2, 4, 50],
            "nginx": [1, 20, 0],
            "php": [8, 0, 0],
            "wordpress": [6, 0, 0],
            "drupal": [9, 0, 0],
        }

    def _parse_version(self, version_str):
        """
        Sürüm dizesinden rakam dizilimini çıkarır.
        Örnek: "Apache/2.4.41 (Ubuntu)" -> [2, 4, 41]
        """
        if not version_str:
            return []
        match = re.search(r'(\d+(?:\.\d+)+)', version_str)
        if not match:
            return []
        try:
            return [int(x) for x in match.group(1).split(".")]
        except ValueError:
            return []

    def _is_outdated(self, tech_name, version_parts):
        """Statik eşik kurallarına göre sürümün eski olup olmadığını belirler."""
        tech_name_lower = tech_name.lower()
        for key, threshold in self.outdated_thresholds.items():
            if key in tech_name_lower:
                # Sürüm parçalarını karşılaştır
                # Örnek: [2, 4, 41] vs [2, 4, 50]
                min_len = min(len(version_parts), len(threshold))
                for i in range(min_len):
                    if version_parts[i] < threshold[i]:
                        return True
                    elif version_parts[i] > threshold[i]:
                        return False
                # Eşitlik durumunda uzunluk kontrolü veya varsayılan false
                if len(version_parts) < len(threshold):
                    return True
        return False

    def correlate(self):
        """
        Bağlam verilerindeki ham ilişkileri tarar ve 4 ana kural setini kullanarak
        derived_relations (türetilmiş ilişkiler) üretir.
        """
        ips = self.context_manager.data.get("ips", {})
        domains = self.context_manager.data.get("domains", {})
        raw_relations = self.context_manager.data.get("relations", [])

        # --- RULE 1: Subnet Correlation (shares_subnet) ---
        subnet_groups = {}
        for ip in ips:
            # IP geçerlilik kontrolü ve /24 alt ağını çıkarma
            parts = ip.split(".")
            if len(parts) == 4:
                subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                if subnet not in subnet_groups:
                    subnet_groups[subnet] = []
                subnet_groups[subnet].append(ip)

        for subnet, ip_list in subnet_groups.items():
            if len(ip_list) > 1:
                # İkili kombinasyonları türet (redundancy olmaması için ip1 < ip2 şeklinde tek yönlü)
                sorted_ips = sorted(ip_list)
                for i in range(len(sorted_ips)):
                    for j in range(i + 1, len(sorted_ips)):
                        ip1 = sorted_ips[i]
                        ip2 = sorted_ips[j]
                        self.context_manager.add_derived_relation(
                            src_type="ip",
                            src_value=ip1,
                            relation="shares_subnet",
                            dst_type="ip",
                            dst_value=ip2,
                            evidence=f"Both belong to the same C-class subnet: {subnet}",
                            confidence=1.0
                        )

        # --- RULE 2: Shared Technology Stack Correlation (shares_stack) ---
        # Domainlerin kullandığı teknolojileri/sunucuları eşle
        domain_stacks = {}
        for rel in raw_relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "")

            if src.get("type") == "domain" and relation in ("uses_server", "uses_technology"):
                domain_val = src.get("value")
                tech_val = dst.get("value")
                if domain_val and tech_val:
                    if domain_val not in domain_stacks:
                        domain_stacks[domain_val] = set()
                    domain_stacks[domain_val].add(tech_val)

        sorted_domains = sorted(list(domain_stacks.keys()))
        for i in range(len(sorted_domains)):
            for j in range(i + 1, len(sorted_domains)):
                dom1 = sorted_domains[i]
                dom2 = sorted_domains[j]
                shared = domain_stacks[dom1].intersection(domain_stacks[dom2])
                for item in shared:
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom1,
                        relation="shares_stack",
                        dst_type="domain",
                        dst_value=dom2,
                        evidence=f"Both domains utilize: {item}",
                        confidence=0.8
                    )

        # --- RULE 3: Outdated Technology Detection (outdated_software) ---
        # Ham ilişkilerdeki server ve tech nesnelerini denetle
        outdated_entities = set() # (type, value, tech_name, version_str)
        for rel in raw_relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "")

            if relation in ("uses_server", "uses_technology"):
                tech_val = dst.get("value")
                if tech_val:
                    v_parts = self._parse_version(tech_val)
                    if v_parts and self._is_outdated(tech_val, v_parts):
                        src_type = src.get("type")
                        src_val = src.get("value")
                        if src_type and src_val:
                            outdated_entities.add((src_type, src_val, tech_val))

        for src_type, src_val, tech_val in outdated_entities:
            self.context_manager.add_derived_relation(
                src_type=src_type,
                src_value=src_val,
                relation="outdated_software",
                dst_type="tech" if src_type == "domain" else "server",
                dst_value=tech_val,
                evidence=f"Software/server version ({tech_val}) is outdated.",
                confidence=1.0
            )

        # --- RULE 4: Outdated Software + Admin Port Correlation (high_risk_exposure) ---
        # Eğer bir IP adresinde outdated_software varsa VE kritik yönetim portları açıksa yüksek risk bildir.
        admin_ports = {21: "FTP", 22: "SSH", 23: "TELNET", 445: "SMB", 3389: "RDP"}
        
        # Her IP için açık portları topla
        ip_ports = {}
        for ip, ip_data in ips.items():
            ports = ip_data.get("ports", [])
            ip_ports[ip] = {p.get("port"): p.get("service", "Unknown") for p in ports}

        # IP'ye bağlı domainler veya doğrudan IP üzerindeki outdated ilişkilerini sorgula
        derived_relations = self.context_manager.data.get("derived_relations", [])
        for rel in derived_relations:
            if rel.get("relation") == "outdated_software":
                src = rel.get("src", {})
                entity_type = src.get("type")
                entity_val = src.get("value")
                
                target_ips = []
                if entity_type == "ip":
                    target_ips.append(entity_val)
                elif entity_type == "domain":
                    # Domain'in çözümlendiği IP'leri bul
                    if entity_val in domains:
                        target_ips.extend(domains[entity_val].get("ips", []))

                for ip in target_ips:
                    if ip in ip_ports:
                        # Bu IP'deki açık portları ve admin port çakışmalarını denetle
                        for port_num, svc_name in ip_ports[ip].items():
                            if port_num in admin_ports:
                                self.context_manager.add_derived_relation(
                                    src_type="ip",
                                    src_value=ip,
                                    relation="high_risk_exposure",
                                    dst_type="port",
                                    dst_value=f"{port_num}/{svc_name}",
                                    evidence=f"Outdated software detected alongside open administrative port: {port_num} ({svc_name})",
                                    confidence=1.0
                                )

        # --- RULE 5: Shared Certificate Detection (shares_certificate) ---
        # If 2+ hosts serve the same certificate (same fingerprint), derive a relation.
        certificates = self.context_manager.data.get("certificates", {})
        for fingerprint, cert_entry in certificates.items():
            hosts = cert_entry.get("hosts", [])
            if len(hosts) < 2:
                continue

            is_wildcard  = cert_entry.get("wildcard", False)
            wildcards    = cert_entry.get("wildcards", [])
            subject_cn   = cert_entry.get("subject_cn", fingerprint[:16] + "...")
            expired      = cert_entry.get("expired", False)

            sorted_hosts = sorted(hosts)
            for i in range(len(sorted_hosts)):
                for j in range(i + 1, len(sorted_hosts)):
                    h1 = sorted_hosts[i]
                    h2 = sorted_hosts[j]

                    if is_wildcard:
                        wc_str = ", ".join(wildcards)
                        evidence = (
                            f"{h1} and {h2} share the same wildcard certificate "
                            f"({wc_str}) — fingerprint: {fingerprint[:32]}..."
                        )
                    else:
                        evidence = (
                            f"{h1} and {h2} share the same certificate "
                            f"(CN={subject_cn}) — fingerprint: {fingerprint[:32]}..."
                        )

                    confidence = 1.0 if not expired else 0.8
                    self.context_manager.add_derived_relation(
                        src_type="host",
                        src_value=h1,
                        relation="shares_certificate",
                        dst_type="host",
                        dst_value=h2,
                        evidence=evidence,
                        confidence=confidence
                    )

        # --- RULE 6: Software Stack Profiling (has_software_stack) ---
        domain_tech = {}
        for rel in raw_relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "")
            if src.get("type") == "domain" and relation in ("uses_server", "uses_technology"):
                dom_val = src.get("value")
                tech_val = dst.get("value").lower()
                if dom_val and tech_val:
                    domain_tech.setdefault(dom_val, set()).add(tech_val)

        # Merge http_headers cache data into technology profiles
        http_headers = self.context_manager.data.get("http_headers", {})
        for dom, h_data in http_headers.items():
            headers = h_data.get("headers", {})
            server = headers.get("server")
            powered_by = headers.get("x-powered-by")
            aspnet = headers.get("x-aspnet-version")
            if server:
                domain_tech.setdefault(dom, set()).add(server.lower())
            if powered_by:
                domain_tech.setdefault(dom, set()).add(powered_by.lower())
            if aspnet:
                domain_tech.setdefault(dom, set()).add("asp.net")
            
            for cookie in h_data.get("cookies", []):
                cname = cookie.get("name", "").lower()
                if cname == "laravel_session":
                    domain_tech.setdefault(dom, set()).add("laravel")
                    domain_tech.setdefault(dom, set()).add("php")
                elif cname in ("phpsessid", "php_session"):
                    domain_tech.setdefault(dom, set()).add("php")
                elif cname == "django":
                    domain_tech.setdefault(dom, set()).add("django")

        for dom, tech_set in domain_tech.items():
            stack_profile = None
            matched_items = []
            
            def has_tech(keyword):
                return any(keyword in t for t in tech_set)

            if has_tech("apache") and has_tech("php") and has_tech("laravel"):
                stack_profile = "Apache + PHP + Laravel"
                matched_items = [t for t in tech_set if any(k in t for k in ("apache", "php", "laravel"))]
            elif has_tech("nginx") and has_tech("php") and has_tech("wordpress"):
                stack_profile = "Nginx + PHP + WordPress"
                matched_items = [t for t in tech_set if any(k in t for k in ("nginx", "php", "wordpress"))]
            elif (has_tech("iis") or has_tech("microsoft-iis")) and has_tech("asp.net"):
                stack_profile = "IIS + ASP.NET"
                matched_items = [t for t in tech_set if any(k in t for k in ("iis", "microsoft-iis", "asp.net"))]
            elif has_tech("nginx") and (has_tech("django") or has_tech("gunicorn")):
                stack_profile = "Nginx + Python + Django"
                matched_items = [t for t in tech_set if any(k in t for k in ("nginx", "django", "gunicorn"))]

            if stack_profile:
                evidence_str = f"Target technology yığını eşleşti: {', '.join(matched_items)}"
                self.context_manager.add_derived_relation(
                    src_type="domain",
                    src_value=dom,
                    relation="has_software_stack",
                    dst_type="stack",
                    dst_value=stack_profile,
                    evidence=evidence_str,
                    confidence=1.0
                )

        # --- RULE 7: Web Security Posture Assessment (web_security_posture) ---
        for dom, h_data in http_headers.items():
            missing = h_data.get("missing_security_headers", [])
            for sh in missing:
                sh_name = "Content-Security-Policy (CSP)" if sh == "Content-Security-Policy" else sh
                sh_name = "Strict-Transport-Security (HSTS)" if sh == "Strict-Transport-Security" else sh_name
                
                if sh == "Content-Security-Policy":
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom,
                        relation="missing_security_header",
                        dst_type="header",
                        dst_value="Content-Security-Policy",
                        evidence="Domain does not enforce Content-Security-Policy (CSP), increasing exposure to XSS/Injection.",
                        confidence=1.0
                    )
                elif sh == "Strict-Transport-Security":
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom,
                        relation="missing_security_header",
                        dst_type="header",
                        dst_value="Strict-Transport-Security",
                        evidence="Domain does not enforce Strict-Transport-Security (HSTS), exposing users to SSL stripping/MITM.",
                        confidence=1.0
                    )

        # --- RULE 8: Email Intelligence & Leak Profiling (email_leak_profiling) ---
        email_intel = self.context_manager.data.get("email_intel", {})
        ROLE_ALIASES = [
            "support", "security", "admin", "info", "contact", "sales", "jobs", "hr", 
            "billing", "marketing", "webmaster", "noc", "abuse", "postmaster", "hostmaster",
            "mailauth-reports", "dmarc-forensics", "dmarc", "noreply", "no-reply", "office"
        ]
        for dom, e_data in email_intel.items():
            report_emails = e_data.get("dmarc_report_emails", [])
            for email in report_emails:
                local = email.split("@")[0].lower()
                is_role = local in ROLE_ALIASES or any(local.startswith(r + "-") or local.startswith(r + ".") for r in ROLE_ALIASES)
                if not is_role:
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom,
                        relation="personal_email_leak",
                        dst_type="email",
                        dst_value=email,
                        evidence=f"DMARC reports route to a personal inbox ({email}) instead of a generic role alias.",
                        confidence=0.9
                    )

        # --- RULE 9: Shared Favicon Pivoting (shares_favicon) ---
        # If two or more domains share the same favicon hash, correlate them.
        metadata_intel = self.context_manager.data.get("metadata_intel", {})
        favicon_index = {}  # hash -> [domain, ...]
        for dom, m_data in metadata_intel.items():
            fav = m_data.get("favicon")
            if fav and fav.get("shodan_hash") is not None:
                fhash = str(fav["shodan_hash"])
                favicon_index.setdefault(fhash, []).append(dom)

        for fhash, domains in favicon_index.items():
            if len(domains) >= 2:
                for i in range(len(domains)):
                    for j in range(i + 1, len(domains)):
                        dom_a, dom_b = domains[i], domains[j]
                        self.context_manager.add_derived_relation(
                            src_type="domain",
                            src_value=dom_a,
                            relation="shares_favicon",
                            dst_type="domain",
                            dst_value=dom_b,
                            evidence=f"Both domains serve the same favicon (Shodan hash: {fhash}). Likely same owner/infrastructure.",
                            confidence=0.85
                        )

        # --- RULE 10: Metadata Contact Mapping (metadata_contact_mapping) ---
        # Promote security.txt and humans.txt contacts into derived relations.
        for dom, m_data in metadata_intel.items():
            sec = m_data.get("security_txt")
            if sec:
                for email in sec.get("emails", []):
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom,
                        relation="security_contact",
                        dst_type="email",
                        dst_value=email,
                        evidence="Extracted from security.txt (official security contact for this domain).",
                        confidence=1.0
                    )
            humans = m_data.get("humans_txt")
            if humans:
                for email in humans.get("emails", []):
                    self.context_manager.add_derived_relation(
                        src_type="domain",
                        src_value=dom,
                        relation="staff_email_exposure",
                        dst_type="email",
                        dst_value=email,
                        evidence="Staff email exposed in publicly accessible humans.txt.",
                        confidence=0.85
                    )
            robots = m_data.get("robots")
            if robots and robots.get("sensitive_paths"):
                self.context_manager.add_derived_relation(
                    src_type="domain",
                    src_value=dom,
                    relation="sensitive_path_disclosure",
                    dst_type="file",
                    dst_value="robots.txt",
                    evidence=f"{len(robots['sensitive_paths'])} sensitive paths disclosed: {', '.join(robots['sensitive_paths'][:5])}",
                    confidence=0.9
                )

        # --- RULE 11: Technology Stack Correlation (tech_stack_correlation) ---
        tech_intel = self.context_manager.data.get("tech_intel", {})

        # 11a. WAF/CDN protection mapping
        for dom, t_data in tech_intel.items():
            for waf in t_data.get("waf_cdn", []):
                self.context_manager.add_derived_relation(
                    src_type="domain",
                    src_value=dom,
                    relation="has_waf_protection",
                    dst_type="waf_cdn",
                    dst_value=waf["name"],
                    evidence=waf.get("evidence", f"WAF/CDN detected: {waf['name']}"),
                    confidence=0.9
                )

        # 11b. Shared tech stack — group domains by normalized stack_profile
        stack_index = {}   # stack_profile -> [domain, ...]
        for dom, t_data in tech_intel.items():
            sp = t_data.get("stack_profile")
            if sp and sp != "Unknown":
                stack_index.setdefault(sp, []).append(dom)

        for stack, domains in stack_index.items():
            if len(domains) >= 2:
                for i in range(len(domains)):
                    for j in range(i + 1, len(domains)):
                        dom_a, dom_b = domains[i], domains[j]
                        self.context_manager.add_derived_relation(
                            src_type="domain",
                            src_value=dom_a,
                            relation="shares_technology_stack",
                            dst_type="domain",
                            dst_value=dom_b,
                            evidence=f"Both domains share identical stack profile: {stack}",
                            confidence=0.75
                        )

        # --- RULE 12: ASN Intelligence Correlation (shares_asn, same_provider, same_prefix) ---
        asn_intel = self.context_manager.data.get("asn_intel", {})

        # 12a. Shared ASN correlation (shares_asn)
        asn_index = {}  # as_number -> [ip, ...]
        for ip, asn_data in asn_intel.items():
            as_num = asn_data.get("as_number")
            if as_num:
                asn_index.setdefault(as_num, []).append(ip)

        for as_num, ip_list in asn_index.items():
            if len(ip_list) >= 2:
                for i in range(len(ip_list)):
                    for j in range(i + 1, len(ip_list)):
                        ip_a, ip_b = ip_list[i], ip_list[j]
                        org = asn_intel[ip_a].get("organization", "Unknown")
                        self.context_manager.add_derived_relation(
                            src_type="ip",
                            src_value=ip_a,
                            relation="shares_asn",
                            dst_type="ip",
                            dst_value=ip_b,
                            evidence=f"Both IPs belong to AS{as_num} ({org})",
                            confidence=0.95
                        )

        # 12b. Same provider correlation (same_provider)
        org_index = {}  # organization -> [ip, ...]
        for ip, asn_data in asn_intel.items():
            org = asn_data.get("organization")
            if org:
                org_index.setdefault(org, []).append(ip)

        for org, ip_list in org_index.items():
            if len(ip_list) >= 2:
                for i in range(len(ip_list)):
                    for j in range(i + 1, len(ip_list)):
                        ip_a, ip_b = ip_list[i], ip_list[j]
                        self.context_manager.add_derived_relation(
                            src_type="ip",
                            src_value=ip_a,
                            relation="same_provider",
                            dst_type="ip",
                            dst_value=ip_b,
                            evidence=f"Both IPs owned by same provider: {org}",
                            confidence=0.9
                        )

        # 12c. Same CIDR prefix correlation (same_prefix)
        cidr_index = {}  # cidr -> [ip, ...]
        for ip, asn_data in asn_intel.items():
            cidr = asn_data.get("cidr")
            if cidr:
                cidr_index.setdefault(cidr, []).append(ip)

        for cidr, ip_list in cidr_index.items():
            if len(ip_list) >= 2:
                for i in range(len(ip_list)):
                    for j in range(i + 1, len(ip_list)):
                        ip_a, ip_b = ip_list[i], ip_list[j]
                        self.context_manager.add_derived_relation(
                            src_type="ip",
                            src_value=ip_a,
                            relation="same_prefix",
                            dst_type="ip",
                            dst_value=ip_b,
                            evidence=f"Both IPs in same network block: {cidr}",
                            confidence=0.85
                        )

    def calculate_risk(self):
        """
        NATO Admiralty Code tabanlı kanıta dayalı risk modeli hesaplar.
        Tüm IP'leri ve Domainleri değerlendirerek Admiralty skorlarına göre risk profili oluşturur.
        """
        self.risk_profiles = {}
        ips = self.context_manager.data.get("ips", {})
        domains = self.context_manager.data.get("domains", {})
        notes = self.context_manager.data.get("notes", [])
        derived_relations = self.context_manager.data.get("derived_relations", [])

        # Değerlendirilecek tüm varlıklar
        entities = []
        for ip in ips:
            entities.append(("ip", ip))
        for dom in domains:
            entities.append(("domain", dom))

        for ent_type, ent_val in entities:
            # Admiralty Scorer başlat
            scorer = AdmiraltyScorer()

            # 1. Admin Port Kontrolleri (Sadece IP'ler için)
            if ent_type == "ip":
                ip_data = ips.get(ent_val, {})
                ports = ip_data.get("ports", [])
                for p in ports:
                    p_num = p.get("port")
                    p_svc = p.get("service", "Unknown")
                    if p_num == 22:
                        scorer.add_evidence(
                            EvidenceType.SHARED_SUBNET,  # Using as high-risk port evidence
                            "scan",
                            InformationReliability.CONFIRMED,
                            SourceReliability.A,
                            description=f"SSH (port 22) exposed to the public"
                        )
                    elif p_num == 3389:
                        scorer.add_evidence(
                            EvidenceType.SHARED_SUBNET,  # Using as high-risk port evidence
                            "scan",
                            InformationReliability.CONFIRMED,
                            SourceReliability.A,
                            description=f"RDP (port 3389) exposed to the public"
                        )
                    elif p_num in (21, 23, 445):
                        scorer.add_evidence(
                            EvidenceType.SHARED_SUBNET,  # Using as high-risk port evidence
                            "scan",
                            InformationReliability.CONFIRMED,
                            SourceReliability.A,
                            description=f"Administrative port {p_num} ({p_svc}) exposed"
                        )

            # 2. Outdated Software İlişkisi Kontrolü
            for rel in derived_relations:
                if rel.get("relation") == "outdated_software":
                    src = rel.get("src", {})
                    if src.get("type") == ent_type and src.get("value") == ent_val:
                        tech_val = rel.get("dst", {}).get("value")
                        scorer.add_evidence(
                            EvidenceType.SAME_TECH_STACK,  # Using as outdated software evidence
                            "nexus",
                            InformationReliability.PROBABLE,
                            SourceReliability.B,
                            description=f"Outdated software detected: {tech_val}"
                        )
                    elif ent_type == "ip" and src.get("type") == "domain":
                        dom_ips = domains.get(src.get("value"), {}).get("ips", [])
                        if ent_val in dom_ips:
                            tech_val = rel.get("dst", {}).get("value")
                            scorer.add_evidence(
                                EvidenceType.SAME_TECH_STACK,
                                "nexus",
                                InformationReliability.PROBABLE,
                                SourceReliability.B,
                                description=f"Associated domain ({src.get('value')}) utilizes outdated software: {tech_val}"
                            )

            # 3. High Risk Exposure İlişkisi Kontrolü
            for rel in derived_relations:
                if rel.get("relation") == "high_risk_exposure":
                    src = rel.get("src", {})
                    if ent_type == "ip" and src.get("type") == "ip" and src.get("value") == ent_val:
                        dst_val = rel.get("dst", {}).get("value")
                        scorer.add_evidence(
                            EvidenceType.CERTIFICATE_MATCH,  # Using as critical exposure evidence
                            "nexus",
                            InformationReliability.CONFIRMED,
                            SourceReliability.A,
                            description=f"Critical exposure: Outdated software coupled with admin port {dst_val}"
                        )
                    elif ent_type == "domain":
                        domain_ips = domains.get(ent_val, {}).get("ips", [])
                        if src.get("type") == "ip" and src.get("value") in domain_ips:
                            dst_val = rel.get("dst", {}).get("value")
                            scorer.add_evidence(
                                EvidenceType.CERTIFICATE_MATCH,
                                "nexus",
                                InformationReliability.CONFIRMED,
                                SourceReliability.A,
                                description=f"Associated IP ({src.get('value')}) has outdated software on admin port {dst_val}"
                            )

            # 4. Güvenlik Header / Form Analizi
            missing_headers_count = 0
            for note in notes:
                text = note.get("text", "")
                if ent_val in text:
                    for header in ("HSTS", "CSP", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"):
                        if header.lower() in text.lower() and "missing" in text.lower():
                            if missing_headers_count < 3:
                                scorer.add_evidence(
                                    EvidenceType.HTTP_HEADER_MATCH,
                                    "http_headers",
                                    InformationReliability.PROBABLE,
                                    SourceReliability.B,
                                    description=f"Missing security header: {header}"
                                )
                                missing_headers_count += 1
                    
                    if "form" in text.lower() and ("password" in text.lower() or "login" in text.lower() or "admin" in text.lower()):
                        scorer.add_evidence(
                            EvidenceType.HTTP_HEADER_MATCH,
                            "crawl",
                            InformationReliability.POSSIBLY_TRUE,
                            SourceReliability.C,
                            description=f"Sensitive web input/form detected (e.g. password field)"
                        )

            # 5. ASN Correlation Evidence (RULE 12)
            asn_intel = self.context_manager.data.get("asn_intel", {})
            if ent_type == "ip" and ent_val in asn_intel:
                asn_data = asn_intel[ent_val]
                scorer.add_evidence(
                    EvidenceType.SAME_ASN,
                    "asn",
                    InformationReliability.CONFIRMED,
                    SourceReliability.A,
                    description=f"IP belongs to {asn_data.get('asn')} ({asn_data.get('organization')})"
                )

            # Admiralty skorunu hesapla
            admiralty_result = scorer.calculate_confidence()
            score = admiralty_result["confidence_percentage"]
            admiralty_rating = admiralty_result["admiralty_rating"]

            # Seviye tespiti
            if score >= 75:
                level = "Critical"
            elif score >= 50:
                level = "High"
            elif score >= 25:
                level = "Medium"
            else:
                level = "Low"

            # Profil kaydı (Admiralty evidence chain ile)
            self.risk_profiles[f"{ent_type}:{ent_val}"] = {
                "type": ent_type,
                "value": ent_val,
                "score": score,
                "level": level,
                "admiralty_rating": admiralty_rating,
                "evidence_chain": admiralty_result["evidence_chain"],
                "evidence_count": admiralty_result["evidence_count"]
            }

        return self.risk_profiles

    def generate_report(self):
        """
        Nexus çekirdek raporunu üretir.
        Dışarıya aktarılabilir zengin bir veri sözlüğü sunar.
        """
        self.correlate()
        self.calculate_risk()

        derived_relations = self.context_manager.data.get("derived_relations", [])
        raw_relations = self.context_manager.data.get("relations", [])
        
        # Risk seviyesi dağılımı
        distribution = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for profile in self.risk_profiles.values():
            level = profile.get("level")
            if level in distribution:
                distribution[level] += 1

        # Kritik bulguları topla
        threat_findings = []
        for rel in derived_relations:
            if rel.get("relation") == "high_risk_exposure":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "High Risk Exposure",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 1.0)
                })
            elif rel.get("relation") == "outdated_software":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Outdated Software",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 1.0)
                })
            elif rel.get("relation") == "shares_certificate":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Shared Certificate",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 1.0)
                })
            elif rel.get("relation") == "missing_security_header":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": f"Missing Security Header: {rel.get('dst', {}).get('value')}",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 1.0)
                })
            elif rel.get("relation") == "has_software_stack":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Software Stack Profile",
                    "description": f"Web stack: {rel.get('dst', {}).get('value')} ({rel.get('evidence')})",
                    "confidence": rel.get("confidence", 1.0)
                })
            elif rel.get("relation") == "personal_email_leak":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Personal Email Leak in DMARC",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.9)
                })
            elif rel.get("relation") == "shares_favicon":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Shared Favicon - Infrastructure Pivot",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.85)
                })
            elif rel.get("relation") == "sensitive_path_disclosure":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Sensitive Path Disclosure (robots.txt)",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.9)
                })
            elif rel.get("relation") == "staff_email_exposure":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Staff Email Exposed in humans.txt",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.85)
                })
            elif rel.get("relation") == "has_waf_protection":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "WAF/CDN Protection Detected",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.9)
                })
            elif rel.get("relation") == "shares_technology_stack":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Shared Technology Stack",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.75)
                })
            elif rel.get("relation") == "shares_asn":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Shared ASN - Infrastructure Correlation",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.95)
                })
            elif rel.get("relation") == "same_provider":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Same Provider - ISP/Hosting Correlation",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.9)
                })
            elif rel.get("relation") == "same_prefix":
                threat_findings.append({
                    "entity": rel.get("src", {}).get("value"),
                    "type": "Same Network Prefix - CIDR Correlation",
                    "description": rel.get("evidence"),
                    "confidence": rel.get("confidence", 0.85)
                })

        # Expired certificates
        certificates = self.context_manager.data.get("certificates", {})
        for fingerprint, cert_entry in certificates.items():
            if cert_entry.get("expired"):
                for host in cert_entry.get("hosts", []):
                    threat_findings.append({
                        "entity": host,
                        "type": "Expired Certificate",
                        "description": (
                            f"Certificate (CN={cert_entry.get('subject_cn', 'N/A')}) "
                            f"served by {host} expired on {cert_entry.get('valid_to', 'N/A')}."
                        ),
                        "confidence": 1.0
                    })

        return {
            "stats": {
                "total_entities": len(self.risk_profiles),
                "total_raw_relations": len(raw_relations),
                "total_derived_relations": len(derived_relations),
            },
            "risk_distribution": distribution,
            "risk_profiles": list(self.risk_profiles.values()),
            "threat_findings": threat_findings,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
