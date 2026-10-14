"""
v1.4 — sürüm/banner/help yüzeyi doğrulaması.

v1.4.0-perception etiketinin help menüsü, banner, version modülü ve
README yüzeylerinde tutarlı olduğunu doğrular (CLI'a dokunmadan).

Koşul:  cd corvus_corax; python scratch/verify_v1411_release_surface.py
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
print("\n== 1) Version module ==")
from modules.version import VersionModule
vm = VersionModule(target=[], config={}, logger=None, context=None)
vd = vm.execute().get("data", {})
check("version v1.4.0-perception", vd.get("version") == "v1.4.0-perception")
check("slogan v1.4", "Unified Perception" in vd.get("slogan", ""))
check("architecture 18 adapters", "18 source adapters" in vd.get("architecture", ""))

# ------------------------------------------------------------------
print("\n== 2) Banner ==")
import core.banner as banner
import inspect
bsrc = inspect.getsource(banner)
check("banner v1.4.0-perception", "v1.4.0-perception" in bsrc)
check("banner eski v1.3.0 kalmadi", "v1.3.0-intelligence" not in bsrc)

# ------------------------------------------------------------------
print("\n== 3) Help module ==")
from modules.help import HelpModule
hm = HelpModule(target=[], config={}, logger=None, context=None)
hd = hm.execute().get("data", "")
check("help basligi v1.4", "CORVUS CORAX v1.4" in hd)
check("help PERCEPTION & INVESTIGATION", "PERCEPTION & INVESTIGATION ENGINE" in hd)
check("breach --no-onion dokumanli", "--no-onion" in hd)
check("XposedOrNot notu", "XposedOrNot" in hd)
check("Ahmia notu", "Ahmia" in hd)
check("dan.me.uk notu", "dan.me.uk" in hd)
check("18 adapter notu", "18 perception source adapters" in hd)
check("system komutu var", "system" in hd)
check("agent komutu var", "agent" in hd)
check("eski v0.9 kalmadi", "v0.9" not in hd)

# ------------------------------------------------------------------
print("\n== 4) ToolSpec tutarli mi ==")
from core.agent.tools import ToolRegistry
reg = ToolRegistry()
check("breach ToolSpec aktif", reg.specs.get("breach") is not None)
spec = reg.specs.get("breach")
check("breach desc v1.4 kaynaklari", spec is not None and "XposedOrNot" in (spec.description or ""))

# ------------------------------------------------------------------
print("\n== 5) README yuzeyi ==")
with open("README.md", encoding="utf-8") as f:
    rd = f.read()
check("README Current Version v1.4", '**v1.4.0 — "Perception"' in rd)
check("README changelog v1.4", "### v1.4.0 — Perception & Investigation Engine" in rd)
check("README command ref v1.4", "CORVUS CORAX v1.4 — PERCEPTION" in rd)
check("README --no-onion", "--no-onion" in rd)

# ------------------------------------------------------------------
print(f"\n== SONUC: {PASS} PASS / {FAIL} FAIL ==")
sys.exit(1 if FAIL else 0)
