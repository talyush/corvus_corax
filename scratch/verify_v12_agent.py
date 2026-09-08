# -*- coding: utf-8 -*-
"""Corvus Corax Faz C — Agent Layer doğrulama.

Dry-run modunda:
  1. Planner hedef tipini doğru sınıflandırıyor mu (domain/ip/email/person)?
  2. Plan adımları ve araç sırası doğru mu?
  3. SafetyPolicy: local otomatik, network onaylı, denied kısıtlı — doğru karar veriyor mu?
  4. Agent döngüsü (observation->action->observation) limitsiz çalışıyor mu?
"""
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


def main():
    from core.agent.tools import ToolRegistry
    from core.agent.planner import Planner
    from core.agent.policy import SafetyPolicy, Approval, ToolScope
    from core.agent.agent import Agent

    # Sahte module registry — gerçek loader modülleriyle eşleşecek anahtarlar
    FAKE_MODULES = {
        "whois": object, "dns": object, "tech": object, "geoip": object,
        "asn": object, "social": object, "github": object, "academic": object,
        "breach": object, "nexus": object, "resolve": object, "evidence": object,
        "pivot": object, "pol": object, "footprint": object, "cert": object,
        "metadata": object, "subdomain": object, "headers": object, "crawl": object,
        "email": object, "wayback": object, "scan": object, "netscan": object,
    }

    print("=" * 70)
    print("FAZ C — AGENT LAYER DOĞRULAMA")
    print("=" * 70)

    # 1. Registry
    reg = ToolRegistry(FAKE_MODULES)
    print("\n[1] Registry:")
    print("   kullanılabilir araç:", len(reg.available))
    print("   ilk 5:", reg.available[:5])
    assert len(reg.available) >= 20, "araç listesi beklenenden kısa"

    # 2. Sınıflandırma
    planner = Planner()
    print("\n[2] Hedef sınıflandırma:")
    for t in ("example.com", "8.8.8.8", "ali@ornek.com", "ali veli", "+905321234567"):
        print(f"   {t!r:22} -> {planner.classify(t)}")

    # 3. Policy
    pol = SafetyPolicy(approval_mode=Approval.AUTO)
    print("\n[3] Güvenlik kararları (auto-onay):")
    d_local = pol.decide("nexus", reg)
    d_net = pol.decide("whois", reg)
    d_denied = pol.decide("scan", reg)
    print(f"   nexus  -> {d_local.scope.value}  (approved={d_local.approved})")
    print(f"   whois  -> {d_net.scope.value}  (approved={d_net.approved})")
    print(f"   scan   -> {d_denied.scope.value} (approved={d_denied.approved})")
    assert d_local.scope == ToolScope.LOCAL and d_local.approved
    assert d_net.scope == ToolScope.NETWORK and d_net.approved
    assert d_denied.scope == ToolScope.DENIED and not d_denied.approved

    # 4. Plan
    print("\n[4] Plan örneği (example.com):")
    plan = planner.plan("investigate", "example.com", reg, max_steps=5)
    print(plan.to_summary())
    assert len(plan.steps) > 0, "plan boş"

    # 5. Agent döngüsü (dry-run)
    print("\n[5] Agent döngüsü (dry-run):")
    agent = Agent(module_registry=FAKE_MODULES, approval_mode=Approval.AUTO, dry_run=True)
    report = agent.investigate("example.com araştır")
    print("   intent:", report["intent"], "| hedef:", report["target"], "| tip:", report["target_type"])
    print("   plan:", report["plan"])
    print("   executed:", report["executed"])
    print("   özet:", report["summary"])
    assert report["summary"]["total_steps"] > 0, "hiç adım çalışmadı"
    assert report["executed"], "hiç arac icra edilmedi"

    print("\n" + "-" * 70)
    print("OK — Faz C Agent Layer (dry-run) çalışıyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())