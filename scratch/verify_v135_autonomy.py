# -*- coding: utf-8 -*-
"""v1.3.5 — Autonomy doğrulama: dinamik pivot kuyruğu + kaynak bütçesi + rapor.

1. Planner yeni hedef sınıflandırma: @kullanici -> username, "acme inc" -> organization
2. Agent'i gerçek modüllerle değil, SAHTE modüllerle çalıştır:
   - sosyal modül 'talha sağır' icin yeni email varligi dondursun
   - agent bu email'i fark edip OTONOM pivot (breach araci) uretsin ve kuyruga atsin
3. Budget: MAX_NETWORK/MAX_LOCAL limitleri asilmamali
4. Rapor: pivot_path + evidence.corroborated dolu
"""
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


class FakeSocialModule:
    """'talha sağır' icin bir email + username varligi bulur (relationship ile)."""

    @classmethod
    def describe(cls):
        return {}

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target or []

    def execute(self):
        return {
            "status": "success",
            "data": {"profiles": 2},
            "notes": [{"text": "Talha Bagci profili bulundu (ornek)"}],
            "relationships": [
                {"src": {"type": "person", "value": "talha sağır"},
                 "dst": {"type": "email", "value": "talha@ornk.com"}},
                {"src": {"type": "person", "value": "talha sağır"},
                 "dst": {"type": "username", "value": "@tbagci"}},
            ],
        }


class FakeBreachModule:
    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target or []

    def execute(self):
        return {
            "status": "success",
            "data": {"metadata": ["breach-a"]},
            "notes": [{"text": "email 1 sizintida (meta-data)"}],
            "relationships": [],
        }


class FakeEmptyModule:
    """Hic varlik dondurmeyen basit basari modulu."""

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target or []

    def execute(self):
        return {"status": "success", "data": {}, "notes": [], "relationships": []}


def build_fake_modules(extra=None):
    mods = {
        "social": FakeSocialModule,
        "github": FakeEmptyModule,
        "academic": FakeEmptyModule,
        "org": FakeEmptyModule,
        "breach": FakeBreachModule,
        "evidence": FakeEmptyModule,
        "nexus": FakeEmptyModule,
        "resolve": FakeEmptyModule,
        "pivot": FakeEmptyModule,
        "pol": FakeEmptyModule,
        "whois": FakeEmptyModule,
        "dns": FakeEmptyModule,
        "geoip": FakeEmptyModule,
        "asn": FakeEmptyModule,
        "cert": FakeEmptyModule,
        "tech": FakeEmptyModule,
        "headers": FakeEmptyModule,
        "metadata": FakeEmptyModule,
        "footprint": FakeEmptyModule,
        "crawl": FakeEmptyModule,
        "email": FakeEmptyModule,
        "wayback": FakeEmptyModule,
        "subdomain": FakeEmptyModule,
        "discover": FakeEmptyModule,
        "geoint": FakeEmptyModule,
    }
    if extra:
        mods.update(extra)
    return mods
def main():
    from core.agent.planner import Planner
    from core.agent.agent import Agent
    from core.agent.policy import Approval

    print("=" * 72)
    print("v1.3.5 — AUTONOMY: DİNAMİK PİVOT + KAYNAK BÜTÇESİ DOĞRULAMA")
    print("=" * 72)

    # --- 1) Yeni hedef sınıflandırma ---
    planner = Planner()
    cases = [
        ("talha sağır", "person"),
        ("example.com", "domain"),
        ("8.8.8.8", "ip"),
        ("ali@ornek.com", "email"),
        ("@tbagci", "username"),
        ("acme inc", "organization"),
    ]
    print("\n[1] Hedef sınıflandırma (v1.3.5):")
    for t, expect in cases:
        got = planner.classify(t)
        mark = "OK" if got == expect else "FAIL"
        print(f"   {t!r:22} -> {got!r:14} (beklenen {expect!r}) {mark}")
        assert got == expect, f"classify({t!r})={got!r}, beklenen {expect!r}"

    # --- 2) Dinamik pivot akışı: sosyal email bulursa breach otonom pivot olur ---
    print("\n[2] Otonom pivot (observation -> yeni PlanStep):")
    mods = build_fake_modules()
    agent = Agent(module_registry=mods, approval_mode=Approval.AUTO, learning=False)
    report = agent.investigate("talha sağır")

    executed = report.get("executed", [])
    print("   çalıştırılan araçlar:", executed)
    print("   summary:", report["summary"])
    print("   pivot_path:", report.get("pivot_path", []))

    assert "social" in executed, "social aracı çalışmalıydı"
    assert report["summary"]["pivots"] >= 1, "yeni varlıktan pivot üretilmeliydi"
    pivot_tools = [st["tool"] for pp in report.get("pivot_path", []) for st in pp.get("steps", [])]
    assert any(t == "breach" for t in pivot_tools), f"email varlığı breach pivotu üretmeliydi ({pivot_tools})"

    # plan + pivotlar toplamda budget'ı aşmamalı
    net_run = sum(1 for t in executed if agent.registry.is_network(t))
    local_run = sum(1 for t in executed if not agent.registry.is_network(t))
    print(f"   NET kullanım: {net_run}/{agent.policy.MAX_NETWORK_TOOLS_PER_TASK}, "
          f"LOCAL: {local_run}/{agent.policy.MAX_LOCAL_TOOLS_PER_TASK}")
    assert net_run <= agent.policy.MAX_NETWORK_TOOLS_PER_TASK
    assert local_run <= agent.policy.MAX_LOCAL_TOOLS_PER_TASK
    assert len(report["observations"]) <= agent.policy.MAX_ITERATIONS

    # --- 3) Evidence / çapraz doğrulama rapor alanı ---
    evidence = report.get("evidence", {})
    print("\n[3] Evidence özeti:", evidence)
    assert "entities_found" in evidence and "corroborated" in evidence
    assert any("email" in e for e in evidence["entities_found"]), "email varlığı kaydedilmeliydi"

    # --- 4) Budget davranışı: ağ limitini düşürünce kalan ağ araçları ATLANIR ---
    print("\n[4] Kaynak bütçesi (düşük limit):")
    agent2 = Agent(module_registry=mods, approval_mode=Approval.AUTO, learning=False)
    agent2.policy.MAX_NETWORK_TOOLS_PER_TASK = 1  # sadece 1 ağ çağrısına izin
    report2 = agent2.investigate("talha sağır")
    skipped_msgs = [o for o in report2["observations"] if o.get("status") == "skipped"]
    print("   executed:", report2["executed"])
    print("   skipped:", len(skipped_msgs))
    print("   örnek atlanma:", skipped_msgs[0]["summary"] if skipped_msgs else "-")
    net2 = sum(1 for t in report2["executed"] if agent2.registry.is_network(t))
    assert net2 <= 1, f"ağ bütçesi 1 olmalıydı, koşan: {net2}"

    # --- 5) Tekrar koruması: aynı (tool,target) bir kez koşar ---
    print("\n[5] Tekrar koruması:")
    seen = set()
    dup = False
    for t, trg in ((o["tool"], o["target"]) for o in report["observations"]):
        k = (t, trg.strip().lower())
        if k in seen:
            dup = True
        seen.add(k)
    print("   tekrar eden adım:", dup)
    assert not dup, "aynı (tool,target) birden fazla kez koşmamalı"

    # --- 6) ASK modunda ağ pivotu onay bekler (AUTO değil) ---
    print("\n[6] ASK modu (ağ çağrısı onay ister):")
    agent3 = Agent(module_registry=mods, approval_mode=Approval.ASK, learning=False,
                   ask_callback=lambda q: False)
    report3 = agent3.investigate("talha sağır")
    denied_net = [o for o in report3["observations"] if o.get("status") == "denied"]
    print("   onaylanmayan araç sayısı:", len(denied_net))
    assert denied_net, "ASK modda ağ araçları onay istemeliydi"

    print("\n" + "-" * 72)
    print("OK — v1.3.5 Autonomy: dinamik pivot kuyruğu, budget, evidence raporu çalışıyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())