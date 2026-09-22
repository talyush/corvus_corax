"""Verification test for Corvus Corax v1.2 Huginn Reasoning Core."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.huginn.explainer import HuginnExplainer
from core.context import ContextManager


def test_huginn():
    print("=== TEST 2: Huginn Reasoning Core & Analytical Explainer ===")
    ctx = ContextManager()
    
    # Context'e bazı ilişkiler ve varlıklar ekleyelim
    ctx.add_entity("domain", "target-corp.com")
    ctx.add_entity("ip", "198.51.100.99")
    ctx.add_relation("domain", "target-corp.com", "resolves_to", "ip", "198.51.100.99", confidence=0.9)

    explainer = HuginnExplainer(context_manager=ctx)

    # 1. Build Trace
    trace = explainer.build_trace_for_target("target-corp.com")
    print(f"[+] Reasoning Trace built for '{trace.target}' with {len(trace.steps)} steps.")
    assert len(trace.steps) >= 4, "Trace should contain Observation, Interpretation, Hypothesis, and Decision steps"
    assert trace.final_decision is not None

    # 2. Explain
    explanation = explainer.explain("target-corp.com", lang="tr")
    print("\n--- Huginn Explanation ---")
    print(explanation)
    assert "HUGINN REASONING EXPLANATION" in explanation
    assert "target-corp.com" in explanation

    # 3. Why (Gerekçelendirme)
    why_rep = explainer.why("target-corp.com", lang="tr")
    print("\n--- Huginn Why Report ---")
    print(why_rep)
    assert "Gerekcelendirme" in why_rep

    print("\n[+] HUGINN REASONING CORE TEST PASSED CLEANLY!")
    return 0


if __name__ == "__main__":
    sys.exit(test_huginn())
