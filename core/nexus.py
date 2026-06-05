import re
from datetime import datetime, timezone

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

    def calculate_risk(self):
        """
        Kanıta dayalı (evidence-based) ağırlıklı bir risk modeli hesaplar.
        Tüm IP'leri ve Domainleri değerlendirerek risk profili oluşturur.
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
            score = 0
            evidence = []

            # 1. Admin Port Kontrolleri (Sadece IP'ler için)
            if ent_type == "ip":
                ip_data = ips.get(ent_val, {})
                ports = ip_data.get("ports", [])
                for p in ports:
                    p_num = p.get("port")
                    p_svc = p.get("service", "Unknown")
                    if p_num == 22:
                        score += 20
                        evidence.append(f"SSH (port 22) exposed to the public (+20)")
                    elif p_num == 3389:
                        score += 25
                        evidence.append(f"RDP (port 3389) exposed to the public (+25)")
                    elif p_num in (21, 23, 445):
                        score += 15
                        evidence.append(f"Administrative port {p_num} ({p_svc}) exposed (+15)")

            # 2. Outdated Software İlişkisi Kontrolü
            for rel in derived_relations:
                if rel.get("relation") == "outdated_software":
                    src = rel.get("src", {})
                    if src.get("type") == ent_type and src.get("value") == ent_val:
                        tech_val = rel.get("dst", {}).get("value")
                        score += 15
                        evidence.append(f"Outdated software detected: {tech_val} (+15)")
                    elif ent_type == "ip" and src.get("type") == "domain":
                        dom_ips = domains.get(src.get("value"), {}).get("ips", [])
                        if ent_val in dom_ips:
                            tech_val = rel.get("dst", {}).get("value")
                            score += 15
                            evidence.append(f"Associated domain ({src.get('value')}) utilizes outdated software: {tech_val} (+15)")

            # 3. High Risk Exposure İlişkisi Kontrolü
            for rel in derived_relations:
                if rel.get("relation") == "high_risk_exposure":
                    src = rel.get("src", {})
                    # high_risk_exposure IP düzeyindedir, eğer domain ise IP'leri üzerinden eşleştir
                    if ent_type == "ip" and src.get("type") == "ip" and src.get("value") == ent_val:
                        dst_val = rel.get("dst", {}).get("value")
                        score += 20
                        evidence.append(f"Critical exposure: Outdated software coupled with admin port {dst_val} (+20)")
                    elif ent_type == "domain":
                        # Domain'in IP'lerinden biri bu eşleşmeye sahipse
                        domain_ips = domains.get(ent_val, {}).get("ips", [])
                        if src.get("type") == "ip" and src.get("value") in domain_ips:
                            dst_val = rel.get("dst", {}).get("value")
                            score += 15
                            evidence.append(f"Associated IP ({src.get('value')}) has outdated software on admin port {dst_val} (+15)")

            # 4. Notlar Üzerinden Güvenlik Header / Form Analizi
            # Varlıkla ilgili notları tara (not metninde varlık adı geçiyorsa)
            missing_headers_count = 0
            for note in notes:
                text = note.get("text", "")
                if ent_val in text:
                    # Güvenlik başlığı kontrolleri
                    for header in ("HSTS", "CSP", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"):
                        if header.lower() in text.lower() and "missing" in text.lower():
                            if missing_headers_count < 3: # En fazla 3 header puanlansın (+15 max)
                                score += 5
                                missing_headers_count += 1
                                evidence.append(f"Missing security header: {header} (+5)")
                    
                    # Crawl hassas form kontrolü
                    if "form" in text.lower() and ("password" in text.lower() or "login" in text.lower() or "admin" in text.lower()):
                        score += 10
                        evidence.append(f"Sensitive web input/form detected (e.g. password field) (+10)")

            # Skoru sınırla (0 - 100)
            score = min(max(score, 0), 100)

            # Seviye tespiti
            if score >= 75:
                level = "Critical"
            elif score >= 50:
                level = "High"
            elif score >= 25:
                level = "Medium"
            else:
                level = "Low"

            # Profil kaydı
            self.risk_profiles[f"{ent_type}:{ent_val}"] = {
                "type": ent_type,
                "value": ent_val,
                "score": score,
                "level": level,
                "evidence": list(set(evidence)) # Tekilleştir
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
