"""Verification test for Corvus Corax v1.2 Muninn Memory Core."""
import sys
import os
import shutil
import tempfile

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.muninn.store import MuninnStore
from core.muninn.recall import MuninnRecallEngine
from core.context import ContextManager


def test_muninn():
    print("=== TEST 1: Muninn Memory Core & Drift Detection ===")
    temp_dir = tempfile.mkdtemp(prefix="muninn_test_")
    try:
        store = MuninnStore(base_dir=temp_dir)
        ctx = ContextManager()
        engine = MuninnRecallEngine(store=store, context_manager=ctx)

        # 1. Observation 1
        changes1 = store.record_snapshot(
            entity_id="alpha-corp.com",
            entity_type="domain",
            attributes={"ip": "198.51.100.1", "registrar": "GoDaddy", "status": "active"},
            source_module="dns",
            confidence=0.85
        )
        print(f"[+] Snapshot 1 saved. Changes: {len(changes1)}")
        assert len(changes1) == 0, "First observation should not produce drift"

        # 2. Observation 2 (IP ve Registrar değişti)
        changes2 = store.record_snapshot(
            entity_id="alpha-corp.com",
            entity_type="domain",
            attributes={"ip": "203.0.113.55", "registrar": "Cloudflare", "status": "active"},
            source_module="whois",
            confidence=0.90
        )
        print(f"[+] Snapshot 2 saved. Detected drift changes: {len(changes2)}")
        assert len(changes2) == 2, f"Expected 2 attribute changes, got {len(changes2)}"

        # 3. Deep Recall
        recall = engine.recall_entity("alpha-corp.com")
        print(f"[+] Recall observation count: {recall['observation_count']}")
        assert recall["observation_count"] == 2
        assert recall["attributes"]["ip"] == "203.0.113.55"
        assert recall["attributes"]["registrar"] == "Cloudflare"

        # 4. Report Formatting
        report = engine.format_history_report("alpha-corp.com", lang="tr")
        print("\n--- Formatted History Report ---")
        print(report)
        assert "alpha-corp.com" in report
        assert "203.0.113.55" in report
        assert "Drift" in report

        print("\n[+] MUNINN MEMORY CORE TEST PASSED CLEANLY!")
        return 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(test_muninn())
