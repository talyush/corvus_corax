"""Verification test for Corvus Corax v1.2 Huginn-Muninn Synergy & Decision Core."""
import sys
import os
import shutil
import tempfile

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.decision.corvus_mind import CorvusDecisionCore
from core.muninn.store import MuninnStore
from core.context import ContextManager


def test_synergy():
    print("=== TEST 3: Huginn & Muninn Synergy (Corvus Decides) ===")
    temp_dir = tempfile.mkdtemp(prefix="synergy_test_")
    try:
        store = MuninnStore(base_dir=temp_dir)
        ctx = ContextManager()
        
        ctx.add_entity("domain", "omega-intel.org")
        ctx.add_relation("domain", "omega-intel.org", "hosted_on", "ip", "192.0.2.1", confidence=0.85)

        # Muninn'e geçmiş 2 gözlem kaydet
        store.record_snapshot("omega-intel.org", "domain", {"ip": "192.0.2.1", "cdn": "Cloudflare"}, source_module="dns")
        store.record_snapshot("omega-intel.org", "domain", {"ip": "198.51.100.77", "cdn": "Akamai"}, source_module="whois")

        decision_core = CorvusDecisionCore(
            context_manager=ctx,
            muninn_store=store
        )

        # 1. Evaluate Target
        eval_res = decision_core.evaluate_target("omega-intel.org")
        print(f"[+] Evaluated target: {eval_res['target']}")
        print(f"[+] Corvus Decision: {eval_res['corvus_decision']}")
        assert "degisim" in eval_res["corvus_decision"] or "omega-intel.org" in eval_res["corvus_decision"]

        # 2. Explain with History
        full_rep = decision_core.explain_with_history("omega-intel.org", lang="tr")
        print("\n--- Full Synergy Report ---")
        print(full_rep)
        assert "MUNINN HAFIZA KAYDI" in full_rep
        assert "HUGINN REASONING EXPLANATION" in full_rep
        assert "CORVUS NIHAI KARAR VE SONRAKI ADIM" in full_rep

        # 3. Why Conclusion Changed (Drift Analysis)
        drift_rep = decision_core.why_conclusion_changed("omega-intel.org", lang="tr")
        print("\n--- Drift Analysis Report ---")
        print(drift_rep)
        assert "degisti" in drift_rep

        print("\n[+] HUGINN-MUNINN SYNERGY TEST PASSED CLEANLY!")
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(test_synergy())
