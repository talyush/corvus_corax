"""Corvus Corax v1.4 — Phase 5 Batch 3: wayback/github/breach/email doğrulama.

Her adaptörün normalize()+eligibility akışını GERÇEK AĞ ÇAĞRISI YAPMADAN
(sahte fetch payload'ı ile) doğrular.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.context import ContextManager
from core.perception.adapters.wayback import WaybackAdapter
from core.perception.adapters.github import GithubAdapter
from core.perception.adapters.breach import BreachAdapter
from core.perception.adapters.email import EmailAdapter
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
print("[1] Wayback adapter normalize")
print("=" * 72)
wb_raw = {
    "module": "wayback", "target": "example.com", "status": "success",
    "data": {"url": "https://example.com",
             "snapshot": {"available": True,
                          "url": "https://web.archive.org/web/20240101/example.com",
                          "timestamp": "20240101"},
             "historical_records": [["20230101", "200", "x"], ["20240101", "200", "y"]],
             "record_count": 2},
}
n = WaybackAdapter().normalize(wb_raw, "example.com")
check("wayback domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                                   for e in n["entities"]))
check("web_snapshot entity", any(e["type"] == "web_snapshot" for e in n["entities"]))
wrels = [r["relation"] for r in n["relations"]]
check("has_web_history", "has_web_history" in wrels)
corr = [r for r in n["relations"] if r["relation"] == "web_history_correlation"]
check("correlation conf 0.4", corr and corr[0]["confidence"] == 0.4)

print()
print("=" * 72)
print("[2] GitHub adapter normalize")
print("=" * 72)
gh_raw = {
    "module": "github", "target": "tbagci", "status": "success",
    "data": {"username": "tbagci",
             "user_info": {"name": "Talha Bagci", "public_repos": 12,
                           "followers": 30},
             "repos": [{"name": "corvus", "language": "Python", "stars": 5,
                        "url": "https://github.com/tbagci/corvus"}],
             "commit_emails": ["tbagci@proton.me", "talha@corp.com"],
             "secret_findings": [{"type": "email", "value": "x@y.com",
                                  "repo": "tbagci/corvus"}],
             "person_candidate": "Talha Bagci"},
}
g = GithubAdapter().normalize(gh_raw, "tbagci")
check("github social_profile", any(e["type"] == "social_profile"
                                   and e["value"] == "github/tbagci" for e in g["entities"]))
check("repository entity", any(e["type"] == "repository"
                               and e["value"] == "corvus" for e in g["entities"]))
check("email entity x2", sum(1 for e in g["entities"] if e["type"] == "email") >= 2)
grels = [r["relation"] for r in g["relations"]]
check("github_profile_candidate", "github_profile_candidate" in grels)
check("github_email_correlation", "github_email_correlation" in grels)
cor = [r for r in g["relations"] if r["relation"] == "github_email_correlation"]
check("candidate conf<1", all(r["confidence"] < 1.0 for r in cor))
print()
print("=" * 72)
print("[3] Breach adapter normalize")
print("=" * 72)
br_raw = {
    "module": "breach", "target": "tbagci@proton.me", "status": "success",
    "data": {"email": "tbagci@proton.me",
             "breach_sources": ["LinkedIn", "Adobe"],
             "breach_count": 2, "risk_level": "Medium"},
}
b = BreachAdapter().normalize(br_raw, "tbagci@proton.me")
check("breach email entity", any(e["type"] == "email"
                                 and e["value"] == "tbagci@proton.me" for e in b["entities"]))
brels = [r["relation"] for r in b["relations"]]
check("appeared_in_breaches", "appeared_in_breaches" in brels)
check("breach conf<1", all(r["confidence"] < 1.0 for r in b["relations"]))
check("risk warning", any(nt.get("severity") == "warning" for nt in b["notes"]))

print()
print("=" * 72)
print("[4] Email pattern adapter normalize")
print("=" * 72)
em_raw = {
    "module": "email", "target": "example.com", "status": "success",
    "data": {"domain": "example.com", "provider": "Google Workspace",
             "provider_evidence": "spf include _spf.google.com",
             "detected_pattern": "{first}.{last}", "pattern_confidence": 0.7,
             "role_emails": ["support@example.com"],
             "personal_emails": ["j.doe@example.com"],
             "suggested_formats": ["{first}.{last}@example.com"]},
}
em = EmailAdapter().normalize(em_raw, "example.com")
check("email domain entity", any(e["type"] == "domain" and e["value"] == "example.com"
                                 for e in em["entities"]))
emrels = [r["relation"] for r in em["relations"]]
check("uses_email_provider", "uses_email_provider" in emrels)
check("email_pattern", "email_pattern" in emrels)
check("role_email_associated_with", "role_email_associated_with" in emrels)
check("email_associated_with", "email_associated_with" in emrels)
priv = [r for r in em["relations"] if r["relation"] == "email_associated_with"]
check("personal conf 0.3 (candidate)", priv and priv[0]["confidence"] == 0.3)

print()
print("=" * 72)
print("[5] Pipeline uçtan uca — eligibility + context yazımı (ağsız)")
print("=" * 72)
ctx = ContextManager()
pipe = PerceptionPipeline(context=ctx, register_defaults=False)


class StubGithubAdapter(SourceAdapter):
    def __init__(self):
        self.source = SourceDeclaration(source_id="github", kind="http", auth_level="authorized")
    def fetch(self, target, **params):
        return gh_raw
    def normalize(self, raw, target):
        return GithubAdapter().normalize(raw, target)


pipe.register(StubGithubAdapter())
res = pipe.perceive("github", "tbagci")
check("perceive ok", res.ok, f"({res.error})")
check("written>0", res.eligibility["written"] >= 1,
      f"(written={res.eligibility['written']})")
check("social_profile context", any(k.startswith("social_profile:") for k in ctx.data.get("entities", {})))
check("email context", any(k.startswith("email:") for k in ctx.data.get("entities", {})))

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)
check("secret warning notu", any(nt.get("severity") == "warning" for nt in g["notes"]))