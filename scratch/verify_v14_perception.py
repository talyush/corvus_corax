"""Corvus Corax v1.4 — Perception Pipeline Skeleton Doğrulama (Phase 1).

whois + social wrapper'ları Perception pipeline'a bağlar:
  - SourceDeclaration + SourceAdapter + PerceptionResult (kontrat)
  - provenance stamping (raw_hash = model.py:22 ile birebir)
  - normalize interface
  - EvidenceExtractor bağlantısı (mevcut model)
  - ELIGIBILITY GATE (yalnız VALIDATED yazılır; seed/UNVERIFIABLE reddedilir)
  - ContextManager'a kontrollü write path

Not: Bu test GERÇEK ağ çağrısı yapmaz — modül execute'ini mock'lar.
"""
import os
import sys
import hashlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import ContextManager
from core.perception.model import SourceDeclaration, stamp_provenance, raw_hash_str
from core.perception.adapter import SourceAdapter
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


# =====================================================================
# [1] SourceDeclaration + raw_hash model.py:22 uyumu
# =====================================================================
print("=" * 72)
print("[1] SourceDeclaration + raw_hash (model.py:22 uyumu)")
print("=" * 72)

src = SourceDeclaration(source_id="whois", kind="registry", auth_level="public",
                        base_url="whois.iana.org")
check("SourceDeclaration.source_id", src.source_id == "whois")
check("SourceDeclaration.auth_level", src.auth_level == "public")

payload = {"query": "example.com"}
expected = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()[:16]
got = raw_hash_str(payload)
check("raw_hash == model.py:22", got == expected, f"({got})")

prov = stamp_provenance(src, "example.com", payload)
check("provenance.source", prov["source"] == "whois")
check("provenance.raw_hash", prov["raw_hash"] == got)
check("provenance.auth", prov["auth"] == "public")
print(f"   provenance: {prov}")


# =====================================================================
# [2] Social adaptör — verified profile + eligibility
# =====================================================================
print()
print("=" * 72)
print("[2] Social adapter normalize + eligibility (verified profile)")
print("=" * 72)


class FakeSocialAdapter(SourceAdapter):
    """social_intel modülünü simüle eder (ağ çağrısı yok)."""

    def __init__(self):
        self.source = SourceDeclaration(
            source_id="social", kind="http", auth_level="public",
            base_url="https://social-platforms")

    def fetch(self, target, **params):
        return {
            "module": "social", "target": target, "status": "success",
            "data": {
                "username": "tbagci",
                "person_candidate": None,
                "platforms_checked": 12,
                "platforms_found": ["github", "reddit"],
                "verified_profiles": [
                    {"platform": "github", "url": "https://github.com/tbagci",
                     "weight": 0.9, "verified": True},
                    {"platform": "reddit", "url": "https://reddit.com/user/tbagci",
                     "weight": 0.9, "verified": True},
                ],
                "correlation_confidence": 0.35,
            },
            "notes": [], "relationships": [],
        }

    def normalize(self, raw, target):
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {})
        handle = data.get("username") or target
        entities = [{
            "type": "username", "value": handle,
            "properties": {"verified_count": len(data.get("verified_profiles", []))},
            "provenance": {"source": "corvus", "status": "discovered"},
        }]
        for pr in data.get("verified_profiles", []):
            platform = pr.get("platform")
            entities.append({
                "type": "social_profile",
                "value": f"{platform}/{handle}",
                "properties": {"url": pr.get("url"), "verified": True},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
        return {
            "entities": entities,
            "relations": [],
            "notes": [{"text": f"'{handle}' 2 platformda doğrulandı", "severity": "info"}],
        }

    def _target_type(self, normalized, target):
        return "username"


ctx = ContextManager()
pipe = PerceptionPipeline(context=ctx, register_defaults=False)
pipe.register(FakeSocialAdapter())

res = pipe.perceive("social", "tbagci")
check("social.perceive.ok", res.ok, f"({res.error})")
check("social.target_type", res.target_type in ("person", "username", "domain"), f"({res.target_type})")
check("social.evidence üretildi", len(res.evidence) >= 1, f"({len(res.evidence)})")
check("social yazma sayısı", res.eligibility["written"] >= 1,
      f"(written={res.eligibility['written']}, rejected={res.eligibility['rejected']})")
check("username context'e yazıldı", "username:tbagci" in ctx.data.get("entities", {}))
check("social_profile yazıldı", any(k.startswith("social_profile:") for k in ctx.data.get("entities", {})))
ent = ctx.data["entities"].get("username:tbagci", {})
check("provenance.source==social", ent.get("provenance", {}).get("source") == "social")
check("provenance.raw_hash", bool(ent.get("provenance", {}).get("raw_hash")))
# =====================================================================
# [3] Whois adaptör — domain + whois_server ilişkisi
# =====================================================================
print()
print("=" * 72)
print("[3] Whois adapter normalize + ilişki yazımı")
print("=" * 72)


class FakeWhoisAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(
            source_id="whois", kind="registry", auth_level="public",
            base_url="whois.iana.org")

    def fetch(self, target, **params):
        return {
            "module": "whois", "target": target, "status": "success",
            "data": {
                "query": target,
                "iana_server": "whois.iana.org",
                "referral_server": "whois.verisign.com",
                "server_used": "whois.verisign.com",
                "raw": "Domain Name: EXAMPLE.COM\nRegistrar: ...",
            },
            "notes": [], "relationships": [],
        }

    def normalize(self, raw, target):
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {})
        return {
            "entities": [{
                "type": "domain", "value": target,
                "properties": {"referral_server": data.get("referral_server")},
                "provenance": {"source": "corvus", "status": "discovered"},
            }],
            "relations": [{
                "src": {"type": "domain", "value": target},
                "relation": "queried_via_whois",
                "dst": {"type": "whois_server", "value": "whois.verisign.com"},
                "confidence": 1.0,
            }],
            "notes": [],
        }


pipe.register(FakeWhoisAdapter())
res_w = pipe.perceive("whois", "example.com")
check("whois.perceive.ok", res_w.ok, f"({res_w.error})")
check("whois domain yazıldı", "domain:example.com" in ctx.data.get("entities", {}))
rels = ctx.data.get("relations", [])
check("whois ilişki yazıldı",
      any(r.get("relation") == "queried_via_whois"
          and r["src"]["value"] == "example.com" for r in rels))
print("   CONTEXT relations:", [r.get("relation") for r in ctx.data.get("relations", [])])


# =====================================================================
# [4] ELIGIBILITY GATE — UNVERIFIABLE + seed reddi
# =====================================================================
print()
print("=" * 72)
print("[4] ELIGIBILITY GATE — UNVERIFIABLE & seed koruması")
print("=" * 72)


class FakeDirtyAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="dirty", kind="test", auth_level="local")

    def fetch(self, target, **params):
        return {"status": "success", "target": target, "data": {},
                "notes": [], "relationships": []}

    def normalize(self, raw, target):
        return {
            "entities": [
                {"type": "domain", "value": "ok.com", "confidence": 0.9},
                {"type": "domain", "value": "not_a_domain$", "confidence": 0.8},
                {"type": "person", "value": "Kullanıcı Seed",
                 "provenance": {"source": "user_input", "status": "seed"}},
            ],
            "relations": [],
            "notes": [],
        }


dirty_ctx = ContextManager()
pipe2 = PerceptionPipeline(context=dirty_ctx, register_defaults=False)
pipe2.register(FakeDirtyAdapter())
res_d = pipe2.perceive("dirty", "target")
check("dirty ok", res_d.ok)
by_value = {e["value"]: e for e in res_d.written}
check("ok.com yazıldı", "ok.com" in by_value)
entity_keys = set(dirty_ctx.data.get("entities", {}).keys())
check("UNVERIFIABLE domain ret", "domain:not_a_domain$" not in entity_keys)
check("seed ret (asla yazılamaz)", "person:Kullanıcı Seed" not in entity_keys)
print("   written:", [w["value"] for w in res_d.written])
print("   rejected:", [r["value"] for r in res_d.rejected])


# =====================================================================
# [5] Kayıtsız kaynak reddi
# =====================================================================
print()
print("=" * 72)
print("[5] Kayıtsız kaynak reddi")
print("=" * 72)
res_unknown = pipe.perceive("google", "x")
check("kayıtsız kaynak reddedildi", not res_unknown.ok and "kayıtlı değil" in res_unknown.error)

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)
print("   CONTEXT entities:", list(ctx.data["entities"].keys()))