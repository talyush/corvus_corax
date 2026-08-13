import json
from datetime import datetime, timezone

class ContextManager:
    """
    Corvus Corax v0.9 — Entity-Agnostic Intelligence Graph & Temporal Event Store

    Tüm varlıkları (ip, domain, person, organization, phone, email, social_profile,
    wallet, location, certificate, vb.) tek bir 'entities' havuzunda tutar.
    Temporal 'events' store, Pattern of Life (POL) analizi için zaman serisi olayları kaydeder.

    Geriye dönük uyumluluk: data["ips"], data["domains"], data["certificates"] vb.
    eski tür bazlı alanlar korunur — mevcut modüller ve Nexus motoru değişiklik
    yapılmadan çalışmaya devam eder.
    """
    def __init__(self):
        self.data = {
            # --- YENİ: Entity-Agnostik Varlık Havuzu ---
            "entities": {},   # "{type}:{value}" -> {"type", "value", "properties", "created_at", "updated_at"}
            "events": [],     # Temporal event store (POL altyapısı)

            # --- LEGACY: Mevcut tür bazlı alanlar (geriye dönük uyumluluk) ---
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
            if len(self.data["meta"]["events"]) > 200:
                self.data["meta"]["events"] = self.data["meta"]["events"][-200:]

    def clear(self):
        """Merkezi zekadaki toplanmış verileri sıfırlar."""
        self.__init__()

    # ============================================================
    # ENTITY-AGNOSTIC API (v0.9)
    # ============================================================

    def add_entity(self, entity_type, value, properties=None):
        """
        Genel varlık ekleme/güncelleme — tüm varlık tipleri buradan geçer.
        Varlık zaten varsa properties güncellenir; yoksa oluşturulur.
        Geriye dönük uyumluluk için legacy tür bazlı alanlara da senkronize edilir.
        """
        if not value:
            return None
        entity_key = f"{entity_type}:{value}"
        props = dict(properties or {})
        now = self._now_iso()

        if entity_key not in self.data["entities"]:
            self.data["entities"][entity_key] = {
                "type": entity_type,
                "value": value,
                "properties": props,
                "created_at": now,
                "updated_at": now,
            }
            self._touch(event=f"entity_added:{entity_key}")
        else:
            if props:
                self.data["entities"][entity_key]["properties"].update(props)
            self.data["entities"][entity_key]["updated_at"] = now

        self._sync_entity_to_legacy(entity_type, value)
        return entity_key

    def get_entity(self, entity_type, value):
        """Belirli bir varlığı sorgular."""
        return self.data["entities"].get(f"{entity_type}:{value}")

    def query_entities(self, entity_type=None, search=None):
        """
        Varlıkları tür ve/veya değer aramasıyla filtreleyerek sorgular.
        """
        results = []
        for key, ent in self.data["entities"].items():
            if entity_type and ent.get("type") != entity_type:
                continue
            if search:
                haystack = str(ent.get("value", "")) + " " + json.dumps(ent.get("properties", {}))
                if search.lower() not in haystack.lower():
                    continue
            results.append(ent)
        return results

    def _sync_entity_to_legacy(self, entity_type, value):
        """Varlığı eski tür bazlı alanlara senkronize eder (geriye dönük uyumluluk)."""
        if entity_type == "ip":
            if value not in self.data["ips"]:
                self.data["ips"][value] = {"ports": [], "geo": {}, "hostname": None}
        elif entity_type == "domain":
            if value not in self.data["domains"]:
                self.data["domains"][value] = {"ips": []}
        # Diğer tipler legacy alan gerektirmez — sadece entities'te yaşar.

    # --- Tür bazlı yardımcılar ---

    def add_person(self, name, properties=None):
        """Kişi varlığı ekler."""
        return self.add_entity("person", name, properties)

    def add_organization(self, name, properties=None):
        """Organizasyon/şirket varlığı ekler."""
        return self.add_entity("organization", name, properties)

    def add_phone(self, number, properties=None):
        """Telefon numarası varlığı ekler."""
        return self.add_entity("phone", number, properties)

    def add_email(self, email, properties=None):
        """Email adresi varlığı ekler."""
        return self.add_entity("email", email, properties)

    def add_social_profile(self, platform, handle, properties=None):
        """Sosyal medya profili varlığı ekler (örn. twitter/johndoe)."""
        value = f"{platform}/{handle}" if platform else handle
        props = dict(properties or {})
        props.setdefault("platform", platform)
        props.setdefault("handle", handle)
        return self.add_entity("social_profile", value, props)

    def add_wallet(self, address, chain="btc", properties=None):
        """Kripto cüzdan varlığı ekler."""
        props = dict(properties or {})
        props.setdefault("chain", chain)
        return self.add_entity("wallet", address, props)

    def add_location(self, lat, lon, label=None, properties=None):
        """Coğrafi konum varlığı ekler."""
        value = label or f"{lat},{lon}"
        props = dict(properties or {})
        props.setdefault("latitude", lat)
        props.setdefault("longitude", lon)
        return self.add_entity("location", value, props)

    # ============================================================
    # TEMPORAL EVENT STORE (v0.9 — Pattern of Life altyapısı)
    # ============================================================

    def add_event(self, entity, action, source="system", location=None, metadata=None):
        """
        Temporal olay ekler — Pattern of Life analizinin ham verisi.
        entity: "{type}:{value}" formatında varlık referansı (örn. "person:ahmet", "ip:8.8.8.8").
        action: Olay tipi (örn. "logged_in", "traveled", "located_in", "post_created").
        """
        if not entity or not action:
            return None
        event = {
            "timestamp": self._now_iso(),
            "entity": entity,
            "action": action,
            "source": source,
            "metadata": dict(metadata or {}),
        }
        if location:
            event["location"] = location
        self.data["events"].append(event)
        # Bellek şişmesini önlemek için buffer sınırı
        if len(self.data["events"]) > 10000:
            self.data["events"] = self.data["events"][-10000:]
        self._touch(event=f"event_added:{entity}:{action}")
        return event

    def query_events(self, entity=None, action=None, source=None, entity_type=None,
                     start_time=None, end_time=None, limit=200):
        """
        Temporal olayları filtreleyerek sorgular.
        - entity: Tam varlık referansı (örn. "person:ahmet")
        - entity_type: Varlık tipine göre filtre (örn. "person", "ip")
        - action: Olay tipi
        - source: Veri kaynağı
        - start_time/end_time: ISO zaman aralığı
        """
        results = []
        for ev in self.data["events"]:
            if entity and ev.get("entity") != entity:
                continue
            if entity_type and not ev.get("entity", "").startswith(f"{entity_type}:"):
                continue
            if action and ev.get("action") != action:
                continue
            if source and ev.get("source") != source:
                continue
            ts = ev.get("timestamp", "")
            if start_time and ts < start_time:
                continue
            if end_time and ts > end_time:
                continue
            results.append(ev)
            if limit and len(results) >= limit:
                break
        return results

    def get_entity_events(self, entity, limit=100):
        """Belirli bir varlığın tüm temporal olaylarını döndürür."""
        if ":" not in entity:
            # Tür belirtilmemişse herhangi bir türle eşleşmeyi dene
            results = []
            for ev in self.data["events"]:
                if ev.get("entity", "").endswith(f":{entity}"):
                    results.append(ev)
                    if limit and len(results) >= limit:
                        break
            return results
        return self.query_events(entity=entity, limit=limit)

    # ============================================================
    # LEGACY API (mevcut modüller için — geriye dönük uyumluluk)
    # ============================================================

    def add_ip(self, ip):
        """Merkezi zihne bir IP adresi ekler."""
        if ip not in self.data["ips"]:
            self.add_entity("ip", ip)
            self._touch(event=f"ip_added:{ip}")
        else:
            self.add_entity("ip", ip)

    def add_port(self, ip, port, service="Unknown"):
        """Bir IP'ye ait port ve servis bilgisini bağlar."""
        self.add_ip(ip)
        port_info = {"port": port, "service": service}
        if port_info not in self.data["ips"][ip]["ports"]:
            self.data["ips"][ip]["ports"].append(port_info)
            # Entity properties'e de işle
            entity = self.data["entities"].get(f"ip:{ip}")
            if entity:
                entity["properties"].setdefault("ports", [])
                if port_info not in entity["properties"]["ports"]:
                    entity["properties"]["ports"].append(port_info)
            # Temporal olay
            self.add_event(f"ip:{ip}", "port_opened", "scan",
                           metadata={"port": port, "service": service})
            self._touch(event=f"port_added:{ip}:{port}/{service}")

    def add_geo(self, ip, geo_data):
        """Bir IP'ye Coğrafi lokasyon bilgilerini bağlar."""
        self.add_ip(ip)
        self.data["ips"][ip]["geo"].update(geo_data)
        # Entity properties'e de işle
        entity = self.data["entities"].get(f"ip:{ip}")
        if entity:
            entity["properties"].setdefault("geo", {}).update(geo_data)
            entity["properties"]["updated_at"] = self._now_iso()
        # Coğrafi konum varlığı ve temporal olay
        country = geo_data.get("country")
        city = geo_data.get("city")
        label = ", ".join(filter(None, [city, country]))
        if label:
            self.add_location(geo_data.get("latitude"), geo_data.get("longitude"),
                              label=label, properties={"ip": ip, "country": country, "city": city})
            self.add_event(f"ip:{ip}", "located_in", "geoip", location=label)
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

        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        dom_entity = self.data["entities"].get(f"domain:{domain}")
        if dom_entity:
            dom_entity["properties"].setdefault("ips", [])
            if ip not in dom_entity["properties"]["ips"]:
                dom_entity["properties"]["ips"].append(ip)
        ip_entity = self.data["entities"].get(f"ip:{ip}")
        if ip_entity:
            ip_entity["properties"]["hostname"] = domain

        self.add_relation("domain", domain, "resolves_to", "ip", ip, "dns mapping")
        self.add_event(f"domain:{domain}", "resolves_to", "dns", metadata={"ip": ip})
        self._touch(event=f"domain_mapped:{domain}->{ip}")

    def add_certificate(self, host, fingerprint, cert_data):
        """
        Stores a certificate fingerprint and the host that served it.
        If the same fingerprint is seen on multiple hosts, they are grouped
        under the same certificate record (enabling shared-cert detection).
        """
        if fingerprint not in self.data["certificates"]:
            entry = dict(cert_data)  # copy cert fields
            entry["hosts"] = []
            self.data["certificates"][fingerprint] = entry
        cert_entry = self.data["certificates"][fingerprint]
        if host not in cert_entry["hosts"]:
            cert_entry["hosts"].append(host)

        # Entity senkronizasyonu
        self.add_entity("certificate", fingerprint, dict(cert_data))
        cert_entity = self.data["entities"].get(f"certificate:{fingerprint}")
        if cert_entity:
            cert_entity["properties"].setdefault("hosts", [])
            if host not in cert_entity["properties"]["hosts"]:
                cert_entity["properties"]["hosts"].append(host)

        self.add_event(f"certificate:{fingerprint}", "served_by", "cert_intel",
                       metadata={"host": host})
        self._touch(event=f"certificate_added:{fingerprint[:16]}...@{host}")

    def add_dns_record(self, domain, dns_data):
        """Stores structured DNS records for a domain in the context."""
        if domain not in self.data["dns_records"]:
            self.data["dns_records"][domain] = {}
        self.data["dns_records"][domain].update(dns_data)
        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        entity = self.data["entities"].get(f"domain:{domain}")
        if entity:
            entity["properties"].setdefault("dns_records", {}).update(dns_data)
        self._touch(event=f"dns_record_added:{domain}")

    def add_http_headers(self, domain, headers_data):
        """Stores structured HTTP headers for a domain in the context."""
        if domain not in self.data["http_headers"]:
            self.data["http_headers"][domain] = {}
        self.data["http_headers"][domain].update(headers_data)
        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        entity = self.data["entities"].get(f"domain:{domain}")
        if entity:
            entity["properties"].setdefault("http_headers", {}).update(headers_data)
        self._touch(event=f"http_headers_added:{domain}")

    def add_email_intel(self, domain, email_data):
        """Stores email intelligence (provider, pattern, formats) for a domain."""
        if domain not in self.data["email_intel"]:
            self.data["email_intel"][domain] = {}
        self.data["email_intel"][domain].update(email_data)
        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        entity = self.data["entities"].get(f"domain:{domain}")
        if entity:
            entity["properties"].setdefault("email_intel", {}).update(email_data)
        self._touch(event=f"email_intel_added:{domain}")

    def add_metadata_intel(self, domain, metadata_data):
        """Stores metadata intelligence (robots, sitemaps, favicon hash) for a domain."""
        if domain not in self.data["metadata_intel"]:
            self.data["metadata_intel"][domain] = {}
        self.data["metadata_intel"][domain].update(metadata_data)
        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        entity = self.data["entities"].get(f"domain:{domain}")
        if entity:
            entity["properties"].setdefault("metadata_intel", {}).update(metadata_data)
        self._touch(event=f"metadata_intel_added:{domain}")

    def add_tech_intel(self, domain, tech_data):
        """Stores deep technology fingerprint data for a domain."""
        if domain not in self.data["tech_intel"]:
            self.data["tech_intel"][domain] = {}
        self.data["tech_intel"][domain].update(tech_data)
        # Entity senkronizasyonu
        self.add_entity("domain", domain)
        entity = self.data["entities"].get(f"domain:{domain}")
        if entity:
            entity["properties"].setdefault("tech_intel", {}).update(tech_data)
        self._touch(event=f"tech_intel_added:{domain}")

    def add_asn_intel(self, ip, asn_data):
        """Stores ASN intelligence data for an IP address."""
        if ip not in self.data["asn_intel"]:
            self.data["asn_intel"][ip] = {}
        self.data["asn_intel"][ip].update(asn_data)
        # Entity senkronizasyonu
        self.add_entity("ip", ip)
        entity = self.data["entities"].get(f"ip:{ip}")
        if entity:
            entity["properties"].setdefault("asn_intel", {}).update(asn_data)
        self._touch(event=f"asn_intel_added:{ip}")

    def add_note(self, text, source="system", severity="info", confidence=1.0):
        """Yapisal not ekler (Nexus'ta yorumlanabilir). Duzenli mükerrer kayit engellenir."""
        if not text:
            return
        text_str = str(text)
        for existing in self.data["notes"]:
            if existing.get("text") == text_str and existing.get("source") == source:
                return
        self.data["notes"].append(
            {
                "text": text_str,
                "source": source,
                "severity": severity,
                "confidence": float(confidence),
                "timestamp": self._now_iso(),
            }
        )
        self._touch(event=f"note_added:{source}")

    def add_relation(self, src_type, src_value, relation, dst_type, dst_value, evidence=None, confidence=1.0):
        """Varliklar arasi iliski ekler (Mukerrer kontrolu yapilir)."""
        for existing in self.data["relations"]:
            if isinstance(existing, dict):
                src = existing.get("src", {})
                dst = existing.get("dst", {})
                if (isinstance(src, dict) and src.get("type") == src_type and src.get("value") == src_value and
                    existing.get("relation") == relation and
                    isinstance(dst, dict) and dst.get("type") == dst_type and dst.get("value") == dst_value):
                    return
        rel = {
            "src": {"type": src_type, "value": src_value},
            "relation": relation,
            "dst": {"type": dst_type, "value": dst_value},
            "evidence": evidence,
            "confidence": float(confidence),
            "timestamp": self._now_iso(),
        }
        self.data["relations"].append(rel)
        # Varlıkları entities'e senkronize et
        self.add_entity(src_type, src_value)
        self.add_entity(dst_type, dst_value)
        # Temporal olay
        self.add_event(f"{src_type}:{src_value}", relation, "relation",
                       metadata={"dst": f"{dst_type}:{dst_value}", "evidence": evidence})
        self._touch(event=f"relation_added:{src_type}->{dst_type}:{relation}")

    def add_derived_relation(self, src_type, src_value, relation, dst_type, dst_value, evidence=None, confidence=1.0):
        """Nexus Engine tarafindan turetilen iliskileri derived_relations alanina ekler (Mukerrer kontrolu yapilir)."""
        for existing in self.data["derived_relations"]:
            if isinstance(existing, dict):
                src = existing.get("src", {})
                dst = existing.get("dst", {})
                if (isinstance(src, dict) and src.get("type") == src_type and src.get("value") == src_value and
                    existing.get("relation") == relation and
                    isinstance(dst, dict) and dst.get("type") == dst_type and dst.get("value") == dst_value):
                    return
        rel = {
            "src": {"type": src_type, "value": src_value},
            "relation": relation,
            "dst": {"type": dst_type, "value": dst_value},
            "evidence": evidence,
            "confidence": float(confidence),
            "timestamp": self._now_iso(),
        }
        self.data["derived_relations"].append(rel)
        # Varlıkları entities'e senkronize et
        self.add_entity(src_type, src_value)
        self.add_entity(dst_type, dst_value)
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

        # Yeni entity ve event alanlarını birleştir
        for key, ent in other_context.get("entities", {}).items():
            if isinstance(ent, dict):
                self.add_entity(ent.get("type"), ent.get("value"), ent.get("properties", {}))

        for event in other_context.get("events", []):
            if isinstance(event, dict):
                self.add_event(
                    entity=event.get("entity"),
                    action=event.get("action"),
                    source=event.get("source", "merge"),
                    location=event.get("location"),
                    metadata=event.get("metadata"),
                )

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

    # ============================================================
    # GÖRÜNTÜLEME & ÖZET
    # ============================================================

    def get_events_summary(self, entity=None, limit=50):
        """Temporal event stream'in okunabilir özetini döndürür."""
        lines = []
        lines.append("=" * 80)
        if entity:
            lines.append(f"EVENT STREAM: {entity}")
        else:
            lines.append("EVENT STREAM (TEMPORAL INTELLIGENCE)")
        lines.append("=" * 80)

        if entity:
            events = self.get_entity_events(entity, limit=limit)
        else:
            events = self.data.get("events", [])[-limit:][::-1]

        if not events:
            lines.append("\n  No temporal events recorded yet.")
            lines.append("  Modules will log events automatically as intelligence is collected.")
        else:
            for ev in events:
                ts = ev.get("timestamp", "")[11:19]  # HH:MM:SS
                ent = ev.get("entity", "?")
                action = ev.get("action", "?")
                source = ev.get("source", "")
                loc = ev.get("location")
                meta = ev.get("metadata", {})
                line = f"  [{ts}] {ent} --{action}-- (src: {source})"
                if loc:
                    line += f" @ {loc}"
                lines.append(line)
                if meta:
                    meta_str = ", ".join(f"{k}={v}" for k, v in list(meta.items())[:4])
                    if meta_str:
                        lines.append(f"         {meta_str}")

        lines.append("\n" + "=" * 80)
        lines.append("Pattern of Life (POL) analysis will consume this event stream.")
        lines.append("=" * 80)
        return "\n".join(lines)

    def get_entities_summary(self, entity_type=None, limit=None):
        """Varlık havuzunun okunabilir özetini döndürür."""
        entities = self.query_entities(entity_type=entity_type)
        if limit:
            entities = entities[:limit]

        lines = []
        lines.append("=" * 80)
        lines.append("ENTITY REGISTRY")
        lines.append("=" * 80)

        if not entities:
            lines.append("\n  No entities registered yet.")
        else:
            # Tür bazında grupla
            by_type = {}
            for ent in entities:
                t = ent.get("type", "unknown")
                by_type.setdefault(t, []).append(ent)

            for t in sorted(by_type.keys()):
                ent_list = by_type[t]
                lines.append(f"\n  {t.upper()} ({len(ent_list)}):")
                for ent in ent_list:
                    value = ent.get("value", "")
                    props = ent.get("properties", {})
                    extra = ""
                    if t == "ip":
                        ports = props.get("ports", [])
                        if ports:
                            extra = f" [ports: {len(ports)}]"
                        hostname = props.get("hostname")
                        if hostname:
                            extra += f" [{hostname}]"
                    elif t == "domain":
                        ips = props.get("ips", [])
                        if ips:
                            extra = f" [{len(ips)} IPs]"
                    elif t == "certificate":
                        hosts = props.get("hosts", [])
                        if hosts:
                            extra = f" [hosts: {len(hosts)}]"
                    lines.append(f"    - {value}{extra}")

        lines.append("\n" + "=" * 80)
        total_events = len(self.data.get("events", []))
        lines.append(f"Total entities: {len(self.data.get('entities', {}))} | Temporal events: {total_events}")
        lines.append("Try 'context --events' for the temporal event stream.")
        lines.append("=" * 80)
        return "\n".join(lines)

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
        
        # Check entity registry entry
        for key, ent in self.data.get("entities", {}).items():
            if ent.get("value") == entity or key == entity:
                ent_type = ent.get("type")
                if ent_type not in ("ip", "domain"):  # IP/domain zaten yukarıda işlendi
                    lines.append(f"\nEntity Intelligence [{ent_type}]:")
                    props = ent.get("properties", {})
                    for k, v in list(props.items())[:10]:
                        if isinstance(v, list):
                            lines.append(f"  {k}: {', '.join(str(x) for x in v[:5])}")
                        elif not isinstance(v, (dict, list)):
                            lines.append(f"  {k}: {v}")
                break
        
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

        # Yeni: Entity havuzu ve temporal event stream
        clean_entities = {}
        for key, ent in self.data.get("entities", {}).items():
            clean_entities[key] = {
                "type": ent.get("type"),
                "value": ent.get("value"),
                "properties": ent.get("properties", {}),
                "created_at": ent.get("created_at"),
            }

        clean_events = []
        for ev in self.data.get("events", [])[-500:]:
            clean_events.append(ev)

        return {
            "entities": clean_entities,
            "events": clean_events,
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
