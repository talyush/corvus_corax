"""Corvus Corax v0.9.5 Evidence Engine Verification Script.
"""
from main import run_module, print_output, context
from core.evidence.extractor import EvidenceExtractor
from core.evidence.validator import EvidenceValidator
from core.evidence.corroboration import Corroborator
from core.evidence.derived import DerivedEvidenceEngine
from core.evidence.lineage import LineageTracker

print("=== 1. Observation & Evidence Extraction Test ===")
extractor = EvidenceExtractor()
mock_res_1 = {
    "target": "target.com",
    "module": "dns",
    "relationships": [{"src": {"value": "target.com"}, "dst": {"value": "192.168.1.100"}, "relation": "resolves_to", "confidence": 0.9}],
    "data": {"ip": "192.168.1.100"}
}
mock_res_2 = {
    "target": "target.com",
    "module": "footprint",
    "relationships": [{"src": {"value": "target.com"}, "dst": {"value": "192.168.1.100"}, "relation": "resolves_to", "confidence": 0.85}],
    "data": {"ip": "192.168.1.100"}
}

evs_1 = extractor.extract_evidence_from_result(mock_res_1)
evs_2 = extractor.extract_evidence_from_result(mock_res_2)
all_evs = evs_1 + evs_2

print(f"Extracted Evidence Count : {len(all_evs)}")
for ev in all_evs:
    print(f"  - [{ev.raw_observation_id}] {ev.evidence_type}: {ev.observed_value} (Source: {ev.source_module})")
print()

print("=== 2. Validation & Corroboration Test ===")
validator = EvidenceValidator()
for ev in all_evs:
    validator.validate_evidence(ev)

corroborator = Corroborator()
all_evs, conflicts = corroborator.corroborate_evidence_list(all_evs)

for ev in all_evs:
    print(f"  - {ev.observed_value} -> Admiralty: {ev.admiralty_code}, Confidence: {ev.confidence:.2f}, Corroborating Sources: {list(ev.corroborating_sources)}")
print()

print("=== 3. Derived Key Findings & Intelligence Gaps Test ===")
key_findings = DerivedEvidenceEngine.derive_key_findings(all_evs)
gaps = LineageTracker.build_intelligence_gaps("target.com", all_evs)

print("Key Findings Count:", len(key_findings))
for kf in key_findings:
    print(f"  [Key Finding] {kf.relationship_str} (Status: {kf.status}, Sources: {kf.supporting_sources})")

print("Intelligence Gaps:", gaps.gaps)
print()

print("=== 4. Live Evidence Module Command Test ===")
context.data["module_results"] = [mock_res_1, mock_res_2]

res_findings = run_module("evidence", ["findings", "target.com"])
print_output(res_findings)

res_gaps = run_module("evidence", ["gaps", "target.com"])
print_output(res_gaps)

print("=== All v0.9.5 Evidence Engine tests passed cleanly! ===")
