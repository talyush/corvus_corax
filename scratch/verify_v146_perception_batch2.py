"""Corvus Corax v1.4 — Phase 5 Batch 2: subdomain/tech/metadata/headers doğrulama.

Her adaptörün normalize()+eligibility akışını GERÇEK AĞ ÇAĞRISI YAPMADAN
(sahte fetch payload'ı ile) doğrular.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import ContextManager
from core.perception.adapters.subdomain import SubdomainAdapter
from core.perception.adapters.tech import TechAdapter
from core.perception.adapters.metadata import MetadataAdapter
from core.perception.adapters.headers import HeadersAdapter
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
print("[1] Subdomain adapter normalize")
print("=" * 72)
sub_raw = {
    "module": "subdomain", "target": "example.com", "status": "success",
    "data": {"domain": "example.com",
             "sources": {"crt_sh": True, "hackertarget": True,
                         "rapiddns": True, "wordlist": False},
             "counts": {"crt_sh": 2, "hackertarget": 2, "rapiddns": 1,
                        "wordlist": 0, "total": 3},
             "subdomains": ["www.example.com", "mail.example.com", "api.example.com"]},
}
n = SubdomainAdapter().normalize(sub_raw, "example.com")
check("subdomain ana domain", any(e["type"] == "domain" and e["value"] == "example.com"
                                  for e in n["entities"]))
rels = [r for r in n["relations"] if r["relation"] == "has_subdomain"]
check("has_subdomain x3", len(rels) == 3, f"({len(rels)})")
check("subdomain confidence<1", all(r["confidence"] < 1.0 for r in rels))
check("host değerleri doğru", sorted(r["dst"]["value"] for r in rels) ==
      ["api.example.com", "mail.example.com", "www.example.com"])

print()
print("=" * 72)
print("[2] Tech adapter normalize")
print("=" * 72)
tech_raw = {
    "module": "tech", "target": "example.com", "status": "success",
    "data": {"domain": "example.com", "http_status": 200,
             "server": "nginx/1.24.0", "server_name": "nginx",
             "runtime": "PHP", "runtime_version": "8.1",
             "cms": [{"name": "WordPress", "version": "6.4"}],
             "frameworks": [{"name": "Laravel"}],
             "js_libraries": [{"name": "jQuery", "version": "3.6.0"}],
             "waf_cdn": [{"name": "Cloudflare", "evidence": "CF-Ray"}],
             "stack_profile": "nginx + php"},
}
nt = TechAdapter().normalize(tech_raw, "example.com")
check("tech domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                                for e in nt["entities"]))
trels = [r["relation"] for r in nt["relations"]]
check("uses_server", "uses_server" in trels)
check("uses_runtime", "uses_runtime" in trels)
check("uses_technology x3", sum(1 for r in nt["relations"]
        if r["relation"] == "uses_technology" and r["dst"]["type"] == "tech") >= 3)
print()
print("=" * 72)
print("[3] Metadata adapter normalize")
print("=" * 72)
meta_raw = {
    "module": "metadata", "target": "example.com", "status": "success",
    "data": {"domain": "example.com", "robots_txt": True, "sitemap_xml": True,
             "security_txt": {"emails": ["security@example.com"]},
             "humans_txt": {"emails": ["info@example.com"]},
             "favicon": {"url": "https://example.com/favicon.ico",
                         "shodan_hash": 123456789, "md5": "abc"}},
}
nm = MetadataAdapter().normalize(meta_raw, "example.com")
check("metadata domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                                    for e in nm["entities"]))
mrels = [r["relation"] for r in nm["relations"]]
check("has_security_contact", "has_security_contact" in mrels)
check("has_staff_email", "has_staff_email" in mrels)
check("has_favicon_hash", "has_favicon_hash" in mrels)
check("favicon_hash entity", any(e["type"] == "favicon_hash"
                                 and e["value"] == "123456789" for e in nm["entities"]))

print()
print("=" * 72)
print("[4] Headers adapter normalize")
print("=" * 72)
hdr_raw = {
    "module": "headers", "target": "https://example.com", "status": "success",
    "data": {"url": "https://example.com", "http_status": 200,
             "headers": {"server": "nginx", "x-powered-by": "PHP/8.1"},
             "cookies": [], "missing_security_headers": ["content-security-policy",
                                                          "strict-transport-security"]},
}
nh = HeadersAdapter().normalize(hdr_raw, "example.com")
check("headers domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                                   for e in nh["entities"]))
hrels = [r["relation"] for r in nh["relations"]]
check("uses_server", "uses_server" in hrels)
check("uses_technology (powered-by)", "uses_technology" in hrels)
check("eksik başlık warning x2", sum(1 for nt2 in nh["notes"]
                                     if nt2.get("severity") == "warning") >= 2)

print()
print("=" * 72)
print("[5] Pipeline uçtan uca — eligibility + context yazımı (ağsız)")
print("=" * 72)
ctx = ContextManager()
pipe = PerceptionPipeline(context=ctx, register_defaults=False)


class StubTechAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="tech", kind="http", auth_level="public")
    def fetch(self, target, **params):
        return tech_raw
    def normalize(self, raw, target):
        return TechAdapter().normalize(raw, target)


pipe.register(StubTechAdapter())
res = pipe.perceive("tech", "example.com")
check("perceive ok", res.ok, f"({res.error})")
check("written>0", res.eligibility["written"] >= 1,
      f"(written={res.eligibility['written']})")
check("domain context yazıldı", "domain:example.com" in ctx.data.get("entities", {}))
check("server context entity", any(k.startswith("server:") for k in ctx.data.get("entities", {})))
check("rejected==0", res.eligibility["rejected"] == 0,
      f"(rejected={res.eligibility['rejected']})")

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)
check("protected_by (waf)", "protected_by" in trels)