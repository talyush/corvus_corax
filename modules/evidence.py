"""Corvus Corax v0.9.5 — Evidence Engine CLI Module.
"""
from core.module_base import BaseModule
from core.evidence.extractor import EvidenceExtractor
from core.evidence.validator import EvidenceValidator
from core.evidence.corroboration import Corroborator
from core.evidence.derived import DerivedEvidenceEngine
from core.evidence.lineage import LineageTracker


class EvidenceModule(BaseModule):
    """
    v0.9.5 — Evidence Engine Pipeline.
    """
    name = "evidence"

    def execute(self):
        args = self.target or []
        action = args[0] if args else "list"
        target = args[1] if len(args) > 1 else "target"

        inv = self.begin_investigation(
            f"Evidence Engine Pipeline execution ({action.upper()})",
            ["OBSERVATION EXTRACTION", "VALIDATION & CORROBORATION", "LINEAGE SYNTHESIS"]
        )

        extractor = EvidenceExtractor()
        validator = EvidenceValidator()
        corroborator = Corroborator()
        lineage = LineageTracker()

        # Context'ten mevcut sonuçları tarayalım
        raw_results = self.context.data.get("module_results", [])
        all_evidence = []

        with inv.phase(0):
            self.status_step(f"Extracting raw observations & atomic evidence for action '{action}'")
            for res in raw_results:
                evs = extractor.extract_evidence_from_result(res)
                for ev in evs:
                    validator.validate_evidence(ev)
                    lineage.register_evidence(ev)
                    all_evidence.append(ev)

        with inv.phase(1):
            self.status_step("Executing cross-source corroboration & conflict detection")
            all_evidence, conflicts = corroborator.corroborate_evidence_list(all_evidence)

        if action == "gaps":
            gaps = lineage.build_intelligence_gaps(target, all_evidence)
            data = {
                "action": "gaps",
                "target": target,
                "gaps": gaps.gaps,
                "unverified_identities": gaps.unverified_identities,
                "single_sources": gaps.single_source_dependencies,
            }
            return self.success(target=target, data=data)

        elif action in ("findings", "key_findings"):
            key_findings = DerivedEvidenceEngine.derive_key_findings(all_evidence)
            kf_dicts = [kf.to_dict() for kf in key_findings]
            data = {
                "action": "findings",
                "target": target,
                "key_findings": kf_dicts,
            }
            return self.success(target=target, data=data)

        elif action == "lineage" and len(args) > 1:
            evidence_id = args[1]
            tree = lineage.get_lineage_tree(evidence_id)
            data = {
                "action": "lineage",
                "evidence_id": evidence_id,
                "tree": tree,
            }
            return self.success(target=evidence_id, data=data)

        # Default summary
        validated_count = sum(1 for e in all_evidence if e.status == "VALIDATED")
        data = {
            "action": "list",
            "total_evidence": len(all_evidence),
            "validated_count": validated_count,
            "conflict_count": len(conflicts),
        }
        return self.success(target=target, data=data)
