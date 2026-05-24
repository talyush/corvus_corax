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
            "meta": {
                "created_at": self._now_iso(),
                "updated_at": self._now_iso(),
                "events": [],
            },
            "relations": [],  # Nexus hazirligi: varliklar arasi baglar
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

    def get_summary(self):
        """O ana kadar elde edilen verileri temizleyip döner."""
        return json.dumps(self.get_clean_data(), indent=4, ensure_ascii=False)

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
        meta = self.data.get("meta", {})
        events = meta.get("events", [])
        if len(events) > 200:
            events = events[-200:]

        return {
            "ips": clean_ips,
            "domains": clean_domains,
            "notes": clean_notes,
            "relations": clean_relations,
            "meta": {
                "created_at": meta.get("created_at"),
                "updated_at": meta.get("updated_at"),
                "event_count": len(meta.get("events", [])),
                "recent_events": events[-20:],
            },
        }
