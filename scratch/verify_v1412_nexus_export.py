"""
v1.4 gozden gecirme onarimi — Nexus/export baglantisi dogrulamasi.

Kapsam (mimari degisikligi YOK):
  1. `from core.nexus import NexusEngine` (paket golgelemesine ragmen calisir)
  2. `NexusExporter(ctx)` report_data'siz kurulur (generate_report semasi uyumlu)
  3. `nexus export html|json|graph` dallari + yanlis formatta error
  4. `GraphVisualizer(ctx)` tetik yolu (exporter uzerinden)
  5. summary/analyze gerilemesi yok

Kosul:  cd corvus_corax; python scratch/verify_v1412_nexus_export.py
"""
import os
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
print("\n== 1) Legacy engine re-export ==")
from core.context import ContextManager
from core.nexus import NexusEngine
ctx = ContextManager()
ctx.add_entity("domain", "example.com", {})
eng = NexusEngine(ctx)
rep = eng.generate_report()
check("NexusEngine import edilir", True)
check("generate_report semasi", all(k in rep for k in
      ("stats", "risk_distribution", "risk_profiles", "threat_findings")))

# ------------------------------------------------------------------
print("\n== 2) Exporter tetik yolu ==")
from core.exporter import NexusExporter
ex = NexusExporter(ctx)
check("Exporter report_data'siz kurulur", bool(ex.report_data))
check("neo4j nodes uretilir", len(ex.generate_neo4j_data().get("nodes", [])) >= 1)

# ------------------------------------------------------------------
print("\n== 3) nexus export dallari ==")
from core.loader import load_modules
mods = load_modules()
cases = [
    (["export", "html", "logs/_v1412.html"], "html"),
    (["export", "json", "logs/_v1412_neo.json"], "neo4j_json"),
    (["export", "graph", "logs/_v1412_g.json"], "graph_json"),
]
for args, etype in cases:
    r = mods["nexus"](target=args, config={}, logger=None, context=ctx).execute()
    ok = (r.get("status") == "success"
          and r.get("data", {}).get("export_type") == etype
          and os.path.isfile(r.get("data", {}).get("filepath", "")))
    check(f"nexus {' '.join(args[1:2])} -> {etype}", ok)

rbad = mods["nexus"](target=["export", "pdf"], config={}, logger=None, context=ctx).execute()
check("bilinmeyen format error verir", rbad.get("status") == "error")
for f in ("logs/_v1412.html", "logs/_v1412_neo.json", "logs/_v1412_g.json"):
    if os.path.isfile(f):
        os.remove(f)

# ------------------------------------------------------------------
print("\n== 4) Gerileme: summary/analyze + visualizer ==")
rs = mods["nexus"](target=["summary"], config={}, logger=None, context=ctx).execute()
ra = mods["nexus"](target=["analyze"], config={}, logger=None, context=ctx).execute()
check("nexus summary calisir", rs.get("status") == "success")
check("nexus analyze calisir", ra.get("status") == "success")
from core.visualizer import GraphVisualizer
viz = GraphVisualizer(ctx)
check("GraphVisualizer exporter uzerinden kurulur",
      len(viz.graph_data.get("nodes", [])) >= 1)

# ------------------------------------------------------------------
print(f"\n== SONUC: {PASS} PASS / {FAIL} FAIL ==")
sys.exit(1 if FAIL else 0)
