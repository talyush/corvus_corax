import json
from datetime import datetime, timezone

class ContextManager:
    """
    Tüm modüllerden gelen Recon verisini tutan Çoklu Bağlam Analizi sınıfı.
    Sosyal mühendislik ve diğer hedefler için yapılandırılmış merkezi bellek.
    """
    def __init__(self):
        self.data = {
            "ips": {},        # ip: {ports: [], geo: {}, hostname: ""}
            "domains": {},    # domain: {ips: []}
            "notes": [],      # genel notlar / tespitler
            "certificates": {},  # fingerprint: {cert_data, hosts: []}
            "dns_records": {},   # domain: {type: data}
            "http_headers": {},  # domain: {headers, cookies}
            "email_intel": {},   # domain: {provider, pattern, formats, report_emails}
            "metadata_intel": {},# domain: {robots, sitemap, security_txt, humans_txt, favicon}
            "tech_intel": {},    # domain: {server, runtime, cdn_waf, cms, frameworks, js_libs, stack_profile}
            "asn_intel": {},     # ip: {asn, org, cidr, country, related_ips}
            "meta": {
                "created_at": self._now_iso(),
                "updated_at": self._now_iso(),
                "events": [],
            },
            "relations": [],  # Nexus hazirligi: varliklar arasi baglar
            "derived_relations": [],  # Nexus tarafindan turetilen iliskiler
        }

    def _now_iso(self):
        return datetime.now(timezone.utc).isoformat()

    def _touch(self, event=None):
        self.data["meta"]["updated_at"] = self._now_iso()
        if event:
            self.data["meta"]["events"].append(event)

    def add_ip(self, ip):
        """Merkezi zihne bir IP adresi ekler."""
        if ip not in self.data["ips"]:
            self.data["ips"][ip] = {"ports": [], "geo": {}, "hostname": None}
            self._touch(event=f"ip_added:{ip}")

    def add_port(self, ip, port, service="Unknown"):
        """Bir IP'ye ait port ve servis bilgisini bağlar."""
        self.add_ip(ip)
        port_info = {"port": port, "service": service}
        if port_info not in self.data["ips"][ip]["ports"]:
            self.data["ips"][ip]["ports"].append(port_info)
            self._touch(event=f"port_added:{ip}:{port}/{service}")

    def add_geo(self, ip, geo_data):
        """Bir IP'ye Coğrafi lokasyon bilgilerini bağlar."""
        self.add_ip(ip)
        self.data["ips"][ip]["geo"].update(geo_data)
        self._touch(event=f"geo_updated:{ip}")

    def add_domain_mapping(self, domain, ip):
        """Domain ile IP adresini haritalar."""
        if domain not in self.data["domains"]:
            self.data["domains"][domain] = {"ips": []}
        if ip not in self.data["domains"][domain]["ips"]:
            self.data["domains"][domain]["ips"].append(ip)
        
        # IP'nin hostname bilgisini de dönüp güncelleyelim
        self.add_ip(ip)
        self.data["ips"][ip]["hostname"] = domain
        self.add_relation("domain", domain, "resolves_to", "ip", ip, "dns mapping")
        self._touch(event=f"domain_mapped:{domain}->{ip}")

    def add_certificate(self, host, fingerprint, cert_data):
        """Stores a certificate fingerprint and the host that served it.
        If the same fingerprint is seen on multiple hosts, they are grouped
        under the same certificate record (enabling shared-cert detection)."""
        if fingerprint not in self.data["certificates"]:
            entry = dict(cert_data)  # copy cert fields
            entry["hosts"] = []
            self.data["certificates"][fingerprint] = entry
        cert_entry = self.data["certificates"][fingerprint]
        if host not in cert_entry["hosts"]:
            cert_entry["hosts"].append(host)
        self._touch(event=f"certificate_added:{fingerprint[:16]}...@{host}")

    def add_dns_record(self, domain, dns_data):
        """Stores structured DNS records for a domain in the context."""
        if domain not in self.data["dns_records"]:
            self.data["dns_records"][domain] = {}
        self.data["dns_records"][domain].update(dns_data)
        self._touch(event=f"dns_record_added:{domain}")

    def add_http_headers(self, domain, headers_data):
        """Stores structured HTTP headers for a domain in the context."""
        if domain not in self.data["http_headers"]:
            self.data["http_headers"][domain] = {}
        self.data["http_headers"][domain].update(headers_data)
        self._touch(event=f"http_headers_added:{domain}")

    def add_email_intel(self, domain, email_data):
        """Stores email intelligence (provider, pattern, formats) for a domain."""
        if domain not in self.data["email_intel"]:
            self.data["email_intel"][domain] = {}
        self.data["email_intel"][domain].update(email_data)
        self._touch(event=f"email_intel_added:{domain}")

    def add_metadata_intel(self, domain, metadata_data):
        """Stores metadata intelligence (robots, sitemaps, favicon hash) for a domain."""
        if domain not in self.data["metadata_intel"]:
            self.data["metadata_intel"][domain] = {}
        self.data["metadata_intel"][domain].update(metadata_data)
        self._touch(event=f"metadata_intel_added:{domain}")

    def add_tech_intel(self, domain, tech_data):
        """Stores deep technology fingerprint data for a domain."""
        if domain not in self.data["tech_intel"]:
            self.data["tech_intel"][domain] = {}
        self.data["tech_intel"][domain].update(tech_data)
        self._touch(event=f"tech_intel_added:{domain}")

    def add_asn_intel(self, ip, asn_data):
        """Stores ASN intelligence data for an IP address."""
        if ip not in self.data["asn_intel"]:
            self.data["asn_intel"][ip] = {}
        self.data["asn_intel"][ip].update(asn_data)
        self._touch(event=f"asn_intel_added:{ip}")

    def add_note(self, text, source="system", severity="info", confidence=1.0):
        """Yapisal not ekler (Nexus'ta yorumlanabilir)."""
        if not text:
            return
        self.data["notes"].append(
            {
                "text": str(text),
                "source": source,
                "severity": severity,
                "confidence": float(confidence),
                "timestamp": self._now_iso(),
            }
        )
        self._touch(event=f"note_added:{source}")

    def add_relation(self, src_type, src_value, relation, dst_type, dst_value, evidence=None, confidence=1.0):
        """Varliklar arasi iliski ekler."""
        rel = {
            "src": {"type": src_type, "value": src_value},
            "relation": relation,
            "dst": {"type": dst_type, "value": dst_value},
            "evidence": evidence,
            "confidence": float(confidence),
            "timestamp": self._now_iso(),
        }
        if rel not in self.data["relations"]:
            self.data["relations"].append(rel)
            self._touch(event=f"relation_added:{src_type}->{dst_type}:{relation}")

    def add_derived_relation(self, src_type, src_value, relation, dst_type, dst_value, evidence=None, confidence=1.0):
        """Nexus Engine tarafindan turetilen iliskileri derived_relations alanina ekler."""
        rel = {
            "src": {"type": src_type, "value": src_value},
            "relation": relation,
            "dst": {"type": dst_type, "value": dst_value},
            "evidence": evidence,
            "confidence": float(confidence),
            "timestamp": self._now_iso(),
        }
        if rel not in self.data["derived_relations"]:
            self.data["derived_relations"].append(rel)
            self._touch(event=f"derived_relation_added:{src_type}->{dst_type}:{relation}")

    def query_relations(self, entity_type=None, entity_value=None, relation=None):
        """Sistemdeki hem ham hem de turetilen tum iliskileri sorgular."""
        results = []
        all_rels = self.data.get("relations", []) + self.data.get("derived_relations", [])
        for rel in all_rels:
            # Check source match
            src_match = True
            if entity_type and rel.get("src", {}).get("type") != entity_type:
                src_match = False
            if entity_value and rel.get("src", {}).get("value") != entity_value:
                src_match = False

            # Check destination match
            dst_match = True
            if entity_type and rel.get("dst", {}).get("type") != entity_type:
                dst_match = False
            if entity_value and rel.get("dst", {}).get("value") != entity_value:
                dst_match = False

            # Match if source or destination matches (or if no entity filter specified)
            entity_match = False
            if not entity_type and not entity_value:
                entity_match = True
            elif (entity_type or entity_value) and (src_match or dst_match):
                entity_match = True

            # Check relation type match
            rel_match = True
            if relation and rel.get("relation") != relation:
                rel_match = False

            if entity_match and rel_match:
                results.append(rel)
        return results

    def merge_context(self, other_context):
        """Disaridan gelen context yapisini mevcut yapiya birlestirir."""
        if not isinstance(other_context, dict):
            return

        for ip, ip_data in other_context.get("ips", {}).items():
            self.add_ip(ip)
            for p in ip_data.get("ports", []):
                self.add_port(ip, p.get("port"), p.get("service", "Unknown"))
            if ip_data.get("geo"):
                self.add_geo(ip, ip_data.get("geo", {}))
            hostname = ip_data.get("hostname")
            if hostname:
                self.add_domain_mapping(hostname, ip)

        for domain, domain_data in other_context.get("domains", {}).items():
            for ip in domain_data.get("ips", []):
                self.add_domain_mapping(domain, ip)

        for note in other_context.get("notes", []):
            if isinstance(note, dict):
                self.add_note(
                    text=note.get("text"),
                    source=note.get("source", "merge"),
                    severity=note.get("severity", "info"),
                    confidence=note.get("confidence", 1.0)
                )
            else:
                self.add_note(str(note), source="merge")

        # Hem 'relations' hem de 'relationships' yapisini destekle
        relations_list = other_context.get("relations") or other_context.get("relationships") or []
        for rel in relations_list:
            if isinstance(rel, dict):
                src = rel.get("src", {})
                dst = rel.get("dst", {})
                self.add_relation(
                    src_type=src.get("type", "unknown"),
                    src_value=src.get("value"),
                    relation=rel.get("relation", "related_to"),
                    dst_type=dst.get("type", "unknown"),
                    dst_value=dst.get("value"),
                    evidence=rel.get("evidence"),
                    confidence=rel.get("confidence", 1.0)
                )

        # derived_relations birlestirmeyi destekle
        derived_list = other_context.get("derived_relations") or []
        for rel in derived_list:
            if isinstance(rel, dict):
                src = rel.get("src", {})
                dst = rel.get("dst", {})
                self.add_derived_relation(
                    src_type=src.get("type", "unknown"),
                    src_value=src.get("value"),
                    relation=rel.get("relation", "related_to"),
                    dst_type=dst.get("type", "unknown"),
                    dst_value=dst.get("value"),
                    evidence=rel.get("evidence"),
                    confidence=rel.get("confidence", 1.0)
                )

    def get_summary(self):
        """O ana kadar elde edilen verileri temizleyip döner."""
        return json.dumps(self.get_clean_data(), indent=4, ensure_ascii=False)

    def get_admiralty_summary(self):
        """Show admiralty intelligence summary for all entities."""
        lines = []
        lines.append("=" * 80)
        lines.append("ADMIRALTY INTELLIGENCE SUMMARY")
        lines.append("=" * 80)
        
        # ASN Intelligence
        asn_intel = self.data.get("asn_intel", {})
        if asn_intel:
            lines.append(f"\nASN Intelligence ({len(asn_intel)} IPs):")
            for ip, data in asn_intel.items():
                lines.append(f"  {ip}:")
                lines.append(f"    ASN: {data.get('asn')}")
                lines.append(f"    Organization: {data.get('organization')}")
                lines.append(f"    CIDR: {data.get('cidr')}")
                lines.append(f"    Related IPs: {data.get('related_count', 0)}")
        
        # Tech Intelligence
        tech_intel = self.data.get("tech_intel", {})
        if tech_intel:
            lines.append(f"\nTechnology Intelligence ({len(tech_intel)} domains):")
            for domain, data in tech_intel.items():
                lines.append(f"  {domain}:")
                lines.append(f"    Server: {data.get('server')}")
                lines.append(f"    Runtime: {data.get('runtime')}")
                lines.append(f"    CMS: {[cms['name'] for cms in data.get('cms', [])]}")
                lines.append(f"    Stack Profile: {data.get('stack_profile')}")
        
        # Derived Relations (Admiralty-based)
        derived_relations = self.data.get("derived_relations", [])
        admiralty_relations = [r for r in derived_relations if r.get("relation") in (
            "shares_asn", "same_provider", "same_prefix", "shares_technology_stack"
        )]
        
        if admiralty_relations:
            lines.append(f"\nAdmiralty Correlations ({len(admiralty_relations)} relations):")
            for rel in admiralty_relations[:20]:  # Limit to first 20
                lines.append(f"  {rel.get('src', {}).get('value')} {rel.get('relation')} {rel.get('dst', {}).get('value')}")
                lines.append(f"    Evidence: {rel.get('evidence')}")
                lines.append(f"    Confidence: {rel.get('confidence')}")
        
        lines.append("\n" + "=" * 80)
        lines.append("Use 'context <entity> --admiralty' for detailed evidence chains")
        lines.append("=" * 80)
        
        return "\n".join(lines)

    def get_entity_admiralty(self, entity):
        """Show detailed admiralty evidence chain for a specific entity."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"ADMIRALTY INTELLIGENCE: {entity}")
        lines.append("=" * 80)
        
        # Check if entity is in ASN intel
        asn_intel = self.data.get("asn_intel", {})
        if entity in asn_intel:
            data = asn_intel[entity]
            lines.append(f"\nASN Intelligence:")
            lines.append(f"  ASN: {data.get('asn')}")
            lines.append(f"  AS Number: {data.get('as_number')}")
            lines.append(f"  Organization: {data.get('organization')}")
            lines.append(f"  ISP: {data.get('isp')}")
            lines.append(f"  Country: {data.get('country')}")
            lines.append(f"  CIDR: {data.get('cidr')}")
            lines.append(f"  Related IPs: {data.get('related_count', 0)}")
            if data.get('related_ips'):
                lines.append(f"  Related IP List: {', '.join(data['related_ips'][:10])}")
        
        # Check if entity is in tech intel
        tech_intel = self.data.get("tech_intel", {})
        if entity in tech_intel:
            data = tech_intel[entity]
            lines.append(f"\nTechnology Intelligence:")
            lines.append(f"  Server: {data.get('server')}")
            lines.append(f"  Runtime: {data.get('runtime')}")
            lines.append(f"  Generator: {data.get('generator')}")
            lines.append(f"  WAF/CDN: {[waf['name'] for waf in data.get('waf_cdn', [])]}")
            cms_list = [f"{cms['name']} {cms.get('version', '')}" for cms in data.get('cms', [])]
            lines.append(f"  CMS: {cms_list}")
            lines.append(f"  Frameworks: {[fw['name'] for fw in data.get('frameworks', [])]}")
            lines.append(f"  JS Libraries: {[js['name'] for js in data.get('js_libraries', [])]}")
            lines.append(f"  Stack Profile: {data.get('stack_profile')}")
        
        # Check derived relations for this entity
        derived_relations = self.data.get("derived_relations", [])
        entity_relations = []
        for rel in derived_relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            if src.get("value") == entity or dst.get("value") == entity:
                entity_relations.append(rel)
        
        if entity_relations:
            lines.append(f"\nAdmiralty Correlations ({len(entity_relations)} relations):")
            for rel in entity_relations:
                rel_type = rel.get("relation")
                src_val = rel.get("src", {}).get("value")
                dst_val = rel.get("dst", {}).get("value")
                evidence = rel.get("evidence")
                confidence = rel.get("confidence")
                
                if src_val == entity:
                    lines.append(f"  {entity} {rel_type} {dst_val}")
                else:
                    lines.append(f"  {dst_val} {rel_type} {entity}")
                lines.append(f"    Evidence: {evidence}")
                lines.append(f"    Confidence: {confidence}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def get_clean_data(self):
        """
        Nexus uyumluluğu için veri şemasını korur,
        sadece boş/noise alanları temizler.
        """
        clean_ips = {}
        for ip, ip_data in self.data["ips"].items():
            ports = ip_data.get("ports", [])
            geo = {k: v for k, v in ip_data.get("geo", {}).items() if v not in (None, "", [])}
            hostname = ip_data.get("hostname")
            clean_ips[ip] = {
                "ports": ports,
                "geo": geo,
                "hostname": hostname if hostname else None,
            }

        clean_domains = {}
        for domain, domain_data in self.data["domains"].items():
            ips = domain_data.get("ips", [])
            if ips:
                clean_domains[domain] = {"ips": ips}

        clean_notes = [n for n in self.data["notes"] if n]
        clean_relations = [r for r in self.data.get("relations", []) if r]
        clean_derived = [r for r in self.data.get("derived_relations", []) if r]
        meta = self.data.get("meta", {})
        events = meta.get("events", [])
        if len(events) > 200:
            events = events[-200:]

        clean_certs = {}
        for fp, cert_entry in self.data.get("certificates", {}).items():
            clean_certs[fp] = cert_entry

        clean_dns = {}
        for dom, records in self.data.get("dns_records", {}).items():
            clean_dns[dom] = records

        clean_http = {}
        for dom, records in self.data.get("http_headers", {}).items():
            clean_http[dom] = records

        clean_email = {}
        for dom, records in self.data.get("email_intel", {}).items():
            clean_email[dom] = records

        clean_metadata = {}
        for dom, records in self.data.get("metadata_intel", {}).items():
            clean_metadata[dom] = records

        clean_tech = {}
        for dom, records in self.data.get("tech_intel", {}).items():
            clean_tech[dom] = records

        return {
            "ips": clean_ips,
            "domains": clean_domains,
            "notes": clean_notes,
            "certificates": clean_certs,
            "dns_records": clean_dns,
            "http_headers": clean_http,
            "email_intel": clean_email,
            "metadata_intel": clean_metadata,
            "tech_intel": clean_tech,
            "relations": clean_relations,
            "derived_relations": clean_derived,
            "meta": {
                "created_at": meta.get("created_at"),
                "updated_at": meta.get("updated_at"),
                "event_count": len(meta.get("events", [])),
                "recent_events": events[-20:],
            },
        }
