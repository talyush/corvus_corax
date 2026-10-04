"""Corvus Corax v1.4 — Phase 5 Batch 1: dns/geoip/asn/cert Perception doğrulama.

Her adaptörün normalize()+eligibility+native pipeline akışını GERÇEK AĞ
ÇAĞRISI YAPMADAN (sahte fetch payload'ı ile) uçtan uca doğrular.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import ContextManager
from core.perception.adapters.dns import DnsAdapter
from core.perception.adapters.geoip import GeoipAdapter
from core.perception.adapters.asn import AsnAdapter
from core.perception.adapters.cert import CertAdapter
from core.perception.adapter import SourceAdapter
from core.perception.model import SourceDeclaration
from core.perception.pipeline import PerceptionPipeline

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"   OK  {name} {detail}")
    else:
        FAIL += 1
        print(f"   FAIL {name} {detail}")


print("=" * 72)
print("[1] DNS adapter normalize")
print("=" * 72)
dns_raw = {
    "module": "dns", "target": "example.com", "status": "success",
    "data": {
        "domain": "example.com",
        "A": ["93.184.216.34"],
        "AAAA": [],
        "NS": ["a.iana-servers.net"],
        "MX": [{"host": "mail.example.com", "priority": 10}],
        "TXT": [],
        "spf": "v=spf1 -all",
        "dmarc": "v=DMARC1; p=none",
        "spf_weak": False,
        "dmarc_weak": True,
        "dkim": {},
    },
}
n = DnsAdapter().normalize(dns_raw, "example.com")
check("dns domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                               for e in n["entities"]))
check("dns ip entity", any(e["type"] == "ip" and e["value"] == "93.184.216.34"
                           for e in n["entities"]))
rels = [r["relation"] for r in n["relations"]]
check("resolves_to", "resolves_to" in rels)
check("has_mx_server", "has_mx_server" in rels)
check("has_ns_server", "has_ns_server" in rels)
check("has_spf_record", "has_spf_record" in rels)
check("has_dmarc_record", "has_dmarc_record" in rels)
check("dmarc weak notu", any(nt.get("severity") == "warning" for nt in n["notes"]))

print()
print("=" * 72)
print("[2] GeoIP adapter normalize")
print("=" * 72)
geo_raw = {
    "module": "geoip", "target": "8.8.8.8", "status": "success",
    "data": {"ip": "8.8.8.8", "country": "United States", "region": "California",
             "city": "Mountain View", "isp": "Google LLC", "org": "Google LLC",
             "lat": 37.4, "lon": -122.0},
}
ng = GeoipAdapter().normalize(geo_raw, "8.8.8.8")
check("geoip ip entity", any(e["type"] == "ip" and e["value"] == "8.8.8.8"
                             for e in ng["entities"]))
check("geoip location entity", any(e["type"] == "location" for e in ng["entities"]))
grels = [r["relation"] for r in ng["relations"]]
check("located_in", "located_in" in grels)
print()
print("=" * 72)
print("[3] ASN adapter normalize")
print("=" * 72)
asn_raw = {
    "module": "asn", "target": "8.8.8.8", "status": "success",
    "data": {"ip": "8.8.8.8", "asn": "AS15169", "as_number": "15169",
             "organization": "Google LLC", "isp": "Google LLC",
             "country": "United States", "cidr": "8.8.8.0/24", "related_count": 10},
}
na = AsnAdapter().normalize(asn_raw, "8.8.8.8")
check("asn ip entity", any(e["type"] == "ip" and e["value"] == "8.8.8.8"
                           for e in na["entities"]))
check("asn entity", any(e["type"] == "asn" and e["value"] == "15169"
                        for e in na["entities"]))
arels = [r["relation"] for r in na["relations"]]
check("belongs_to_asn", "belongs_to_asn" in arels)
check("owned_by (candidate)", "owned_by" in arels)
check("in_cidr", "in_cidr" in arels)
owned = [r for r in na["relations"] if r["relation"] == "owned_by"][0]
check("owned_by confidence<1 (candidate)",
      owned["confidence"] < 1.0 and owned["confidence"] >= 0.5, f"({owned['confidence']})")

print()
print("=" * 72)
print("[4] Cert adapter normalize")
print("=" * 72)
cert_raw = {
    "module": "cert", "target": "example.com", "status": "success",
    "data": {"host": "example.com", "port": 443, "subject_cn": "example.com",
             "organization": "Internet Corp", "issuer": "DigiCert TLS RSA",
             "san": ["example.com", "www.example.com"], "wildcards": ["*.example.com"],
             "wildcard": True, "expired": False, "days_remaining": 200,
             "valid_from": "2025-01-01", "valid_to": "2026-01-01",
             "serial_number": "ABC123", "fingerprint": "AA:BB:CC:DD"},
}
nc = CertAdapter().normalize(cert_raw, "example.com")
check("cert entity", any(e["type"] == "certificate" and e["value"] == "AA:BB:CC:DD"
                         for e in nc["entities"]))
check("host entity", any(e["type"] == "host" and e["value"] == "example.com"
                         for e in nc["entities"]))
crels = [r["relation"] for r in nc["relations"]]
check("issued_to", "issued_to" in crels)
check("cert_issued_by", "cert_issued_by" in crels)
check("wildcard_covers", "wildcard_covers" in crels)
print()
print("=" * 72)
print("[5] Pipeline uçtan uca — eligibility + context yazımı (ağsız)")
print("=" * 72)
ctx = ContextManager()
pipe = PerceptionPipeline(context=ctx, register_defaults=False)


class StubDnsAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="dns", kind="dns", auth_level="public")
    def fetch(self, target, **params):
        return dns_raw
    def normalize(self, raw, target):
        return DnsAdapter().normalize(raw, target)


pipe.register(StubDnsAdapter())
res = pipe.perceive("dns", "example.com")
check("perceive ok", res.ok, f"({res.error})")
check("written>0", res.eligibility["written"] >= 1,
      f"(written={res.eligibility['written']}, rejected={res.eligibility['rejected']})")
check("domain context'e yazıldı", "domain:example.com" in ctx.data.get("entities", {}))
check("ip context'e yazıldı", "ip:93.184.216.34" in ctx.data.get("entities", {}))


class DirtyDnsAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="dns2", kind="dns", auth_level="public")
    def fetch(self, target, **params):
        return dict(dns_raw, data=dict(dns_raw["data"], A=["not_an_ip"]))
    def normalize(self, raw, target):
        return DnsAdapter().normalize(raw, target)


ctx2 = ContextManager()
pipe2 = PerceptionPipeline(context=ctx2, register_defaults=False)
pipe2.register(DirtyDnsAdapter())
res2 = pipe2.perceive("dns2", "example.com")
check("geçersiz ip reddedildi", "ip:not_an_ip" not in ctx2.data.get("entities", {}))
check("geçerli domain yazıldı", "domain:example.com" in ctx2.data.get("entities", {}))

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)
check("operated_by (org)", "operated_by" in grels)