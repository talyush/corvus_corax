"""Corvus Corax v1.4 — Phase 5 Batch 4: org/academic/phone/wallet doğrulama.

Her adaptörün normalize()+eligibility akışını GERÇEK AĞ ÇAĞRISI YAPMADAN
(sahte fetch payload'ı ile) doğrular. KANDİDAT ilişkilerin (conf < 0.5)
gate tarafından REDDEDİLDİĞİNİ de kontrol eder.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import ContextManager
from core.perception.adapters.org import OrgAdapter
from core.perception.adapters.academic import AcademicAdapter
from core.perception.adapters.phone import PhoneAdapter
from core.perception.adapters.wallet import WalletAdapter
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
print("[1] Org adapter normalize")
print("=" * 72)
org_raw = {
    "module": "org", "target": "Acme Corp", "status": "success",
    "data": {"organization": "Acme Corp", "domain": "acme.com",
             "person": "Jane Doe", "parent": "MegaCorp",
             "infra_correlations": ["ip:1.2.3.4 (AS15169)", "domain:acme.com (server: nginx)"]},
}
o = OrgAdapter().normalize(org_raw, "Acme Corp")
check("org entity", any(e["type"] == "organization" and e["value"] == "Acme Corp"
                        for e in o["entities"]))
orels = o["relations"]
od = [r for r in orels if r["relation"] == "org_owns_domain"]
check("org_owns_domain conf 0.6", od and od[0]["confidence"] == 0.6)
check("employs_candidate conf 0.4", any(r["relation"] == "employs_candidate"
                                        and r["confidence"] == 0.4 for r in orels))
check("owns_subsidiary conf 0.5", any(r["relation"] == "owns_subsidiary"
                                      and r["confidence"] == 0.5 for r in orels))
check("infra korrelasyon notu x2", sum(1 for n in o["notes"]
      if n.get("severity") == "info") >= 2)

print()
print("=" * 72)
print("[2] Academic adapter normalize")
print("=" * 72)
aca_raw = {
    "module": "academic", "target": "alice.smith@mit.edu", "status": "success",
    "data": {"person": "Alice Smith", "is_email": True,
             "author_info": {"display_name": "Alice Smith",
                             "orcid": "0000-0001-2345-6789", "h_index": 12,
                             "affiliations": ["MIT", "Lab X"]},
             "publications": [{"title": "Paper One", "year": 2023,
                               "doi": "10.1/abc", "venue": "J. Research"},
                              {"title": "Paper Two", "year": 2021,
                               "doi": None, "venue": None}],
             "university": "MIT"},
}
a = AcademicAdapter().normalize(aca_raw, "alice.smith@mit.edu")
check("person entity", any(e["type"] == "person" and e["value"] == "Alice Smith"
                           for e in a["entities"]))
check("academic_profile entity", any(e["type"] == "academic_profile"
                                     and e["value"] == "Alice Smith" for e in a["entities"]))
check("publication x2", sum(1 for e in a["entities"]
      if e["type"] == "publication") >= 2)
check("university org", any(e["type"] == "organization" and e["value"] == "MIT"
                            for e in a["entities"]))
arels = a["relations"]
check("has_academic_profile conf 0.9", any(r["relation"] == "has_academic_profile"
                                           and r["confidence"] == 0.9 for r in arels))
check("academic_affiliated_with 0.7", any(r["relation"] == "academic_affiliated_with"
                                          and r["confidence"] == 0.7 for r in arels))
check("authored_publication 0.6", any(r["relation"] == "authored_publication"
                                      and r["confidence"] == 0.6 for r in arels))

print()
print("=" * 72)
print("[3] Phone adapter normalize")
print("=" * 72)
phn_raw = {
    "module": "phone", "target": "+905551234567", "status": "success",
    "data": {"phone": "+905551234567", "original_input": "+905551234567",
             "country_code": "90", "local_number": "5551234567",
             "number_type": "mobile",
             "operator_prefix": {"prefix_detected": "555",
                                 "possible_operator": "Turkcell",
                                 "basis": "numbering_plan", "confidence": 0.4},
             "person_candidate": "Jane Doe"},
}
p = PhoneAdapter().normalize(phn_raw, "+905551234567")
check("phone entity", any(e["type"] == "phone" and e["value"] == "+905551234567"
                          for e in p["entities"]))
prels = p["relations"]
check("has_number_type conf 0.9", any(r["relation"] == "has_number_type"
                                      and r["confidence"] == 0.9 for r in prels))
check("possible_operator 0.4", any(r["relation"] == "possible_operator"
                                   and r["confidence"] == 0.4 for r in prels))
check("phone_candidate_for 0.4", any(r["relation"] == "phone_candidate_for"
                                     and r["confidence"] == 0.4 for r in prels))
print()
print("=" * 72)
print("[4] Wallet adapter normalize")
print("=" * 72)
wal_raw = {
    "module": "wallet", "target": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT", "status": "success",
    "data": {"address": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT", "chain": "btc",
             "explorer_url": "https://www.blockchain.com/btc/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
             "balance_btc": 0.125, "person_candidate": None},
}
w = WalletAdapter().normalize(wal_raw, "1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
check("wallet entity", any(e["type"] == "wallet" and e["value"] == wal_raw["data"]["address"]
                           for e in w["entities"]))
wrels = w["relations"]
check("on_chain conf 1.0", any(r["relation"] == "on_chain" and r["confidence"] == 1.0
                               for r in wrels))
check("chain prop btc", any(e.get("properties", {}).get("chain") == "btc"
                            for e in w["entities"]))
check("candidate yok (person=None)", not any(r["relation"] == "wallet_candidate_for"
                                             for r in wrels))
wal_raw2 = dict(wal_raw); wal_raw2["data"] = dict(wal_raw["data"])
wal_raw2["data"]["person_candidate"] = "John Doe"
w2 = WalletAdapter().normalize(wal_raw2, wal_raw["data"]["address"])
check("wallet_candidate_for 0.4", any(r["relation"] == "wallet_candidate_for"
                                      and r["confidence"] == 0.4 for r in w2["relations"]))

print()
print("=" * 72)
print("[5] Pipeline uçtan uca — gate + context yazımı (ağsız)")
print("=" * 72)
ctx = ContextManager()
pipe = PerceptionPipeline(context=ctx, register_defaults=False)


class StubOrgAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="org", kind="registry", auth_level="local")
    def fetch(self, target, **params):
        return org_raw
    def normalize(self, raw, target):
        return OrgAdapter().normalize(raw, target)


class StubPhoneAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="phone", kind="registry", auth_level="local")
    def fetch(self, target, **params):
        return phn_raw
    def normalize(self, raw, target):
        return PhoneAdapter().normalize(raw, target)


pipe.register(StubOrgAdapter())
pipe.register(StubPhoneAdapter())
rorg = pipe.perceive("org", "Acme Corp")
check("org perceive ok", rorg.ok, f"({rorg.error})")
check("org entity context", "organization:Acme Corp" in ctx.data.get("entities", {}))
rorg_rels = [r.get("value") for r in rorg.written if r["type"] == "relation"]
check("org_owns_domain yazıldı", any("acme.com" in v for v in rorg_rels))
check("employs_candidate REDDEDİLDİ (conf 0.4)",
      any("Jane Doe" in r.get("value") for r in rorg.rejected))
rphn = pipe.perceive("phone", "+905551234567")
check("phone perceive ok", rphn.ok, f"({rphn.error})")
check("phone entity ctx (gate whitelist)", "phone:+905551234567" in ctx.data.get("entities", {}))
check("has_number_type yazıldı", any("->mobile" in r.get("value")
      for r in rphn.written if r["type"] == "relation"))
check("possible_operator REDDEDİLDİ (0.4)",
      any("->Turkcell" in r.get("value") for r in rphn.rejected))

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)