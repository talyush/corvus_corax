"""Corvus Corax v1.4 — Phase 2: ToolResult canonical refactor doğrulama.

Amaç:
- ToolExecutor.execute() -> ToolResult (canonical dönüş)
- Observation, observation_ref üzerinden bağlanır
- evidence, mevcut Evidence modeliyle üretilir (yeni model YOK)
- Eski run() deprecated wrapper — uyumluluk korunur
- Agent döngüsü execute() kullanır, davranış bozulmaz
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent.executor import ToolExecutor, ToolResult, Observation
from core.evidence.model import Evidence
from core.agent import ToolResult as TR_export


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


# ---------------------------------------------------------------------
# Test modülleri — gerçek ağ çağrısı yok
# ---------------------------------------------------------------------
class FakeSuccessModule:
    """Başarı döndüren ve yeni varlık içeren sahte modül."""
    def __init__(self, target, config=None, logger=None, context=None):
        self.target = target

    def execute(self):
        return {
            "module": "whois", "target": self.target[0], "status": "success",
            "data": {"query": self.target[0]},
            "notes": [{"text": "registrar bulundu"}],
            "relationships": [
                {"src": {"type": "domain", "value": self.target[0]},
                 "relation": "queried_via_whois",
                 "dst": {"type": "whois_server", "value": "whois.verisign.com"},
                 "confidence": 1.0},
            ],
        }


class FakeFailModule:
    def __init__(self, target, config=None, logger=None, context=None):
        self.target = target

    def execute(self):
        return {"module": "x", "target": self.target[0], "status": "error",
                "error": "boş yanıt"}


class FakeRaiseModule:
    def __init__(self, target, config=None, logger=None, context=None):
        self.target = target

    def execute(self):
        raise RuntimeError("patladı")


REGISTRY = {
    "whois": FakeSuccessModule,
    "fail": FakeFailModule,
    "raise": FakeRaiseModule,
}

print("=" * 72)
print("[1] Canonical execute() -> ToolResult")
print("=" * 72)
ex = ToolExecutor(dry_run=False)
res = ex.execute("whois", "example.com", REGISTRY)

check("ToolResult tipi", isinstance(res, ToolResult))
check("res.ok", res.ok)
check("res.tool", res.tool == "whois")
check("res.data.query", res.data.get("query") == "example.com")
check("observation bağlandı", isinstance(res.observation, Observation))
check("observation_ref == obs_id", res.observation_ref == res.observation.obs_id)
check("observation durumu success", res.observation.status == "success")
check("yeni varlık algılandı", "domain:example.com" in res.observation.new_entities)
check("whois_server varlığı", any("whois_server:" in e for e in res.observation.new_entities))
print(f"   obs_id={res.observation_ref} new_entities={res.observation.new_entities}")

print()
print("=" * 72)
print("[2] evidence — mevcut Evidence modeli (yeni model YOK)")
print("=" * 72)
check("evidence listesi", isinstance(res.evidence, list) and len(res.evidence) >= 1,
      f"({len(res.evidence)})")
check("Evidence nesneleri", all(isinstance(e, Evidence) for e in res.evidence))
first = res.evidence[0]
check("evidence.to_dict çalışıyor", isinstance(first.to_dict(), dict) and first.to_dict().get("id"))
check("evidence.source_module", first.source_module == "whois")
check("evidence.raw_observation_id bağlı", first.raw_observation_id == res.observation_ref)
print(f"   evidence[0]: {first.to_dict().get('type')}={first.to_dict().get('value')} "
      f"(obs: {first.raw_observation_id})")

print()
print("=" * 72)
print("[3] Hata yolları — ok=False + observation bağlı")
print("=" * 72)
res_fail = ex.execute("fail", "x", REGISTRY)
check("fail ok=False", not res_fail.ok)
check("fail error", res_fail.error is not None, f"({res_fail.error})")
check("fail observation durumu error", res_fail.observation.status == "error")

res_raise = ex.execute("raise", "y", REGISTRY)
check("raise ok=False", not res_raise.ok)
check("raise istisna yakalanır", "patladı" in (res_raise.error or ""))
check("raise observation error", res_raise.observation.status == "error")
print(f"   fail.error={res_fail.error} | raise.error={res_raise.error}")

print()
print("=" * 72)
print("[4] Eski run() — deprecated uyumluluk wrapper'ı")
print("=" * 72)
obs_legacy = ex.run("whois", "example.com", REGISTRY)
check("run() hala Observation döner", isinstance(obs_legacy, Observation))
check("legacy obs_id atanır", obs_legacy.obs_id.startswith("obs-"))
check("legacy davranış korundu",
      obs_legacy.status == "success" and "domain:example.com" in obs_legacy.new_entities)

print()
print("=" * 72)
print("[5] dry_run modu korunur")
print("=" * 72)
ex_dry = ToolExecutor(dry_run=True)
res_dry = ex_dry.execute("social", "tbagci", REGISTRY)
check("dry-run ok=True", res_dry.ok)
check("dry-run observation status success", res_dry.observation.status == "success")
check("dry-run evidence boş", res_dry.evidence == [])

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)