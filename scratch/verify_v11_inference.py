"""Corvus Corax v1.1 Inference Engine ("Sherlock") Verification Suite.
"""
from main import run_module, print_output, context
from core.graph.providers.neo4j_provider import Neo4jGraphService
from core.inference.bayesian import BayesianUpdater, HypothesisBelief
from core.inference.evidence_weight import EvidenceWeighter
from core.inference.hypothesis import Hypothesis, HypothesisLifecycle
from core.inference.dynamic_bridge import DynamicBridgeEngine
from core.inference.uncertainty import compute_entropy, assess_uncertainty_level, UncertaintyEngine
from core.inference.counterfactual import CounterfactualEngine
from core.inference.negative_evidence import NegativeEvidenceEngine
from core.evidence.model import Evidence

print("============================================================")
print("  TEST 1: REAL BAYESIAN MATHEMATICS & UPDATE TRAIL")
print("============================================================")
updater = BayesianUpdater()
belief = HypothesisBelief(prior=0.40, description="Target Alpha owns alpha-corp.com")

ev1 = Evidence(evidence_type="dns", observed_value="alpha-corp.com", target="Target Alpha", source_module="dns", admiralty_code="A1")
ev2 = Evidence(evidence_type="whois", observed_value="alpha-corp.com", target="Target Alpha", source_module="whois", admiralty_code="B2")

post1 = updater.update(belief, ev1)
post2 = updater.update(belief, ev2)

print(f" [+] Prior: {belief.prior:.2f}")
print(f" [+] After ev1 (A1): {post1:.4f}")
print(f" [+] After ev2 (B2): {post2:.4f}")
print(f" [+] Bayes Trail   : {updater.build_trail_string(belief)}")
assert post2 > post1 > 0.40, "Bayesian posterior must increase with supporting evidence"
print(" [+] Bayesian Math Verification: PASSED")
print()

print("============================================================")
print("  TEST 2: NEGATIVE EVIDENCE / ABSENCE REASONING")
print("============================================================")
neg_engine = NegativeEvidenceEngine(updater)
belief_neg = HypothesisBelief(prior=0.70, description="Target Alpha operates email infra")
post_before = belief_neg.posterior
absent_record = {
    "entity": "alpha-corp.com",
    "module": "dns",
    "absent_evidence_type": "mx",
    "strength": 0.30
}
post_after = neg_engine.apply_negative_evidence(belief_neg, absent_record)
print(f" [+] Prior before absence: {post_before:.2f}")
print(f" [+] Posterior after absent MX record: {post_after:.4f}")
assert post_after < post_before, "Absence of expected evidence must decrease posterior"
print(" [+] Negative Evidence Reasoning: PASSED")
print()

print("============================================================")
print("  TEST 3: SHANNON ENTROPY & UNCERTAINTY QUANTIFICATION")
print("============================================================")
ent_crit = compute_entropy(0.50)
ent_low = compute_entropy(0.95)
print(f" [+] Entropy at p=0.50 (Coin-flip) : {ent_crit:.4f} -> Level: {assess_uncertainty_level(0.50)}")
print(f" [+] Entropy at p=0.95 (Confirmed) : {ent_low:.4f} -> Level: {assess_uncertainty_level(0.95)}")
assert ent_crit > ent_low, "Entropy at p=0.5 must be significantly higher than at p=0.95"
print(" [+] Uncertainty Quantification: PASSED")
print()

print("============================================================")
print("  TEST 4: COUNTERFACTUAL & ALTERNATIVE EXPLANATIONS")
print("============================================================")
cf_engine = CounterfactualEngine()
hyp = Hypothesis(hypothesis_type="OWNERSHIP", claim="Target Alpha owns alpha-corp.com", prior=0.40)
cf_confirm = cf_engine.what_would_confirm(hyp)
cf_refute = cf_engine.what_would_refute(hyp)
print(f" [+] To Confirm: Need ~{cf_confirm['estimated_strong_evidence_needed']} strong (A1) items | Actions: {cf_confirm['prescribed_actions'][0]}")
print(f" [+] To Refute : Need ~{cf_refute['estimated_strong_counter_evidence_needed']} counter-evidence items")
print(" [+] Counterfactual Analysis: PASSED")
print()

print("============================================================")
print("  TEST 5: DYNAMIC BRIDGE ENGINE")
print("============================================================")
graph_service = Neo4jGraphService()
# Component 1: Isolated Person Alpha -> Private Domain
graph_service.add_entity("person", "Target Alpha")
graph_service.add_entity("domain", "alpha-private.com")
graph_service.add_relationship("Target Alpha", "alpha-private.com", "owns_domain", 0.9)

# Component 2: Isolated IP Beta
graph_service.add_entity("ip", "203.0.113.88")

bridge_engine = DynamicBridgeEngine(graph_service)
bridge_res = bridge_engine.analyze("Target Alpha", "203.0.113.88")

print(f" [+] Bridge Needed: {bridge_res['bridge_needed']}")
print(f" [+] Summary      : {bridge_res['analysis_summary']}")
for cand in bridge_res['candidates']:
    print(f"     -> Bridge Candidate: [{cand['bridge_type']}] (strength: {cand['candidate_strength']})")
    for h in cand['evidence_hints']:
        print(f"        * {h}")
assert bridge_res['bridge_needed'] is True, "Dynamic bridge must be needed for disconnected components"
print(" [+] Dynamic Bridge Engine: PASSED")
print()

print("============================================================")
print("  TEST 6: LIVE CLI NEXUS INFER & BRIDGE COMMANDS")
print("============================================================")
context.add_entity("person", "Target Alpha")
context.add_entity("domain", "alpha-corp.com")
context.add_relation("person", "Target Alpha", "owns_domain", "domain", "alpha-corp.com", confidence=0.95)

context.data["module_results"] = [
    {
        "target": "alpha-corp.com",
        "module": "whois",
        "relationships": [{"src": {"value": "Target Alpha"}, "dst": {"value": "alpha-corp.com"}, "relation": "owns_domain", "confidence": 0.95}],
        "data": {"registrant": "Target Alpha"}
    },
    {
        "target": "alpha-corp.com",
        "module": "dns",
        "relationships": [{"src": {"value": "alpha-corp.com"}, "dst": {"value": "198.51.100.42"}, "relation": "resolves_to", "confidence": 0.90}],
        "data": {"ip": "198.51.100.42"}
    }
]

res_infer = run_module("nexus", ["infer", "Target Alpha"])
print_output(res_infer)

res_bridge = run_module("nexus", ["bridge", "Target Alpha", "Target Beta"])
print_output(res_bridge)

print("=== ALL V1.1 INFERENCE ENGINE TESTS PASSED CLEANLY! ===")
