"""
v1.4 Phase 5 — Breach Intelligence genişletme doğrulaması.

Yeni kamuya açık kaynaklar:
  1. XposedOrNot check-email  -> hızlı breach listesi
  2. XposedOrNot breach-analytics -> detaylı kırılım + paste summary
  3. Ahmia -> .onion arama (token akışlı)
  4. dan.me.uk torlist -> Tor exit node eşleştirme (context'teki IP'lerle)

Etik kural: yalnızca meta-veri (hangi kaynaklarda görünüyor / kaç .onion / tor-exit IP).
Ham şifre ve kayıt içeriği asla yazılmaz.

Koşul:  cd corvus_corax; python scratch/verify_v1410_breach_sources.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


# ------------------------------------------------------------------
print("\n== 1) Modül import ==")
from modules.breach_intel import BreachIntelModule
check("BreachIntelModule import edildi", callable(BreachIntelModule))
for meth in ("_check_xposedornot", "_check_xposedornot_analytics",
             "_check_ahmia", "_check_tor_exit_nodes"):
    check(f"yeni metod: {meth}", hasattr(BreachIntelModule, meth))

# ------------------------------------------------------------------
print("\n== 2) Kaynak metotları (canlı API) ==")
m = BreachIntelModule(target=["test@example.com"], config={}, logger=None, context=None)

# 2a. XposedOrNot check-email
x = m._check_xposedornot("test@example.com")
check("check-email ok", x.get("ok") is True)
check("check-email breach listesi dolu", len(x.get("breaches", [])) > 10)

# 2b. XposedOrNot breach-analytics
a = m._check_xposedornot_analytics("test@example.com")
check("analytics ok", a.get("ok") is True)
check("analytics breach listesi", len(a.get("breaches", [])) > 10)
check("analytics pastes_summary dict", isinstance(a.get("pastes_summary", {}), dict))

# 2c. Ahmia (.onion)
on = m._check_ahmia("test@example.com")
check("ahmia ok", on.get("ok") is True)
check("ahmia onion yapisi list", isinstance(on.get("onions", []), list))

# 2d. Tor exit node (context yok -> bos aday IP -> ok false beklenebilir)
t = m._check_tor_exit_nodes([])
check("tor exit dict dondu", isinstance(t, dict) and "total_nodes" in t)

# ------------------------------------------------------------------
print("\n== 3) Modül entegrasyonu ==")
from core.context import ContextManager
c = ContextManager()
c.add_ip("8.8.8.8")  # tor exit aday listesine girmesi icin bir IP
m2 = BreachIntelModule(target=["test@example.com"], config={}, logger=None, context=c)
r = m2.execute()
check("execute status success", r.get("status") == "success")
d = r.get("data", {})
check("source_breakdown mevcut", isinstance(d.get("source_breakdown", {}), dict))
check("xposedornot kaynagi pozitif", d.get("source_breakdown", {}).get("xposedornot", 0) > 10)
check("onion_links alani var", isinstance(d.get("onion_links", []), list))
check("tor_exit alani var", isinstance(d.get("tor_exit", {}), dict))
check("risk seviyesi hesaplandi", d.get("risk_level") in ("Low", "Medium", "High", "Critical"))

# ------------------------------------------------------------------
print("\n== 4) Perception adapter ==")
from core.perception.adapters.breach import BreachAdapter
ad = BreachAdapter(config={}, logger=None, context=c)
pr = ad.perceive("test@example.com")
check("perceive ok", pr.ok is True)
check("source_id=breach", pr.source.source_id == "breach")
n = pr.normalized or {}
ent_types = {e.get("type") for e in n.get("entities", [])}
check("email entity normalize", "email" in ent_types)
rels = [rel.get("relation") for rel in n.get("relations", [])]
check("appeared_in_breaches rel", "appeared_in_breaches" in rels)

# ------------------------------------------------------------------
print("\n== 5) ToolSpec ==")
from core.agent.tools import ToolRegistry
reg = ToolRegistry()
spec = reg.specs.get("breach")
check("breach ToolSpec tanimli", spec is not None)
if spec:
    check("capability perception::source", "perception::source" in (spec.capabilities or []))
    check("output_kind evidence", spec.output_kind == "evidence")

# ------------------------------------------------------------------
print(f"\n== SONUC: {PASS} PASS / {FAIL} FAIL ==")
sys.exit(1 if FAIL else 0)