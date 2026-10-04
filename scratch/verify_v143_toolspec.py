"""Corvus Corax v1.4 — Phase 3: ToolSpec migration doğrulama.

Kapsam:
  - input_schema / output_kind / capabilities alanları ToolSpec'te
  - 24 eski araç: `{}` toleranslı migration (register() ile şemasız YENİ giremez)
  - yeni araç: input_schema zorunlu (register() reddeder)
  - validate_input: JSON Schema benzeri kwargs doğrulaması
  - capabilities: whois/social -> "perception::source"
  - output_kind: Engine capability değerlendirmesi için hazır
  - mevcut agent/planner/policy davranışları bozulmadı
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent.tools import ToolSpec, ToolRegistry

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
print("[1] Eski 24 arac migrasyonu — input_schema {} toleransı")
print("=" * 72)
reg = ToolRegistry()
check("toplam araç", len(reg.specs) >= 24, f"({len(reg.specs)})")
legacy_no_schema = 0
for name, spec in reg.specs.items():
    if spec.input_schema == {}:
        legacy_no_schema += 1
check("boş şema toleransı", legacy_no_schema == len(reg.specs),
      f"({legacy_no_schema}/{len(reg.specs)} toleranslı)")
# all have input_schema attribute (not None)
check("hiçbiri input_schema=None değil",
      all(s.input_schema is not None for s in reg.specs.values()))

print()
print("=" * 72)
print("[2] register() — yeni araç input_schema ZORUNLU")
print("=" * 72)
try:
    reg.register(ToolSpec("fake_no_schema", ["domain"], "şemasız"))
    check("şemasız yeni araç reddedildi", False, "reddedilmedi (hata)")
except ValueError as e:
    check("şemasız yeni araç reddedildi", "input_schema" in str(e), f"({e})")

try:
    reg.register(ToolSpec("fake_with_schema", ["domain"], "şemalı",
                          input_schema={"type": "object", "required": ["target"]}))
    check("şemalı yeni araç kabul", "fake_with_schema" in reg.specs)
except ValueError as e:
    check("şemalı yeni araç kabul", False, f"(beklenmedik hata: {e})")

try:
    reg.register(ToolSpec("whois", ["domain"], "duplike", input_schema={}))
    check("üzerine yazma yasak", False, "duplike kayıt oldu")
except ValueError:
    check("üzerine yazma yasak", True)

print()
print("=" * 72)
print("[3] validate_input — JSON Schema benzeri kwargs doğrulaması")
print("=" * 72)
spec_target = ToolSpec(
    "smart", ["domain"],
    input_schema={
        "type": "object",
        "required": ["target"],
        "properties": {"target": {"type": "string"}, "depth": {"type": "integer"}},
    })
reg.register(spec_target)
check("zorunlu eksik -> hata", reg.validate_input("smart", {}) is not None)
check("uygun kwargs -> geçer", reg.validate_input("smart", {"target": "x.com"}) is None)
check("type hatalı -> hata",
      reg.validate_input("smart", {"target": "x.com", "depth": "deep"}) is not None)
check("schema yok -> tolerans geçer", reg.validate_input("dns", {}) is None,
      "(dns migration {} toleransı)")

print()
print("=" * 72)
print("[4] capabilities — perception::source bağlantısı")
print("=" * 72)
check("whois perception::source", reg.has_capability("whois", "perception::source"))
check("social perception::source", reg.has_capability("social", "perception::source"))
check("dns perception::source (batch1)", reg.has_capability("dns", "perception::source"))
check("cert perception::source (batch1)", reg.has_capability("cert", "perception::source"))
check("subdomain perception::source (batch2)", reg.has_capability("subdomain", "perception::source"))
check("tech perception::source (batch2)", reg.has_capability("tech", "perception::source"))
check("academic perception::source değil", not reg.has_capability("academic", "perception::source"))
check("bilinmeyen capability False", not reg.has_capability("whois", "bogus"))

print()
print("=" * 72)
print("[5] output_kind — Investigation Engine capability metadata")
print("=" * 72)
check("whois -> evidence", reg.output_kind_for("whois") == "evidence")
check("social -> evidence", reg.output_kind_for("social") == "evidence")
check("dns -> evidence (ağ toplayıcı)", reg.output_kind_for("dns") == "evidence")
check("crawl -> data (ham içerik)", reg.output_kind_for("crawl") == "data")
check("scan -> data", reg.output_kind_for("scan") == "data")
check("nexus -> report_fragment", reg.output_kind_for("nexus") == "report_fragment")
check("evidence tool -> report_fragment", reg.output_kind_for("evidence") == "report_fragment")
kinds = {reg.output_kind_for(n) for n in reg.specs}
check("yalnızca 3 bilinen tür", kinds <= {"evidence", "data", "report_fragment"}, f"({kinds})")

print()
print("=" * 72)
print("[6] mevcut davranış korundu — tools_for_target / is_network")
print("=" * 72)
domain_tools = reg.tools_for_target("domain")
check("domain hedefli araçlar mevcut", "whois" in domain_tools and "dns" in domain_tools)
check("network önce gelir",
      domain_tools.index("whois") < domain_tools.index("resolve"))
reg.sync_with_modules({"whois": object(), "dns": object()})
check("available senkronu", "whois" in reg.available and "dns" in reg.available)
check("is_network", reg.is_network("whois") and not reg.is_network("resolve"))

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)