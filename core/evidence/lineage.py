"""Corvus Corax Evidence Lineage & Provenance Tracker.

Kanıtların ebeveyn-çocuk silsilesini (Provenance Lineage) izler ve
'WHAT CORVUS DOES NOT KNOW' (İstihbarat Boşlukları) raporunu oluşturur.
"""
from core.evidence.model import IntelligenceGaps


class LineageTracker:
    """Silsile izleme ve istihbarat boşlukları motoru."""

    def __init__(self):
        self.evidence_by_id = {}

    def register_evidence(self, evidence):
        self.evidence_by_id[evidence.id] = evidence

    def get_lineage_tree(self, evidence_id: str) -> dict:
        """Belirtilen kanıt kimliğinin ham gözlemden türetilen kanıta kadar silsile ağacını çıkarır."""
        ev = self.evidence_by_id.get(evidence_id)
        if not ev:
            return {"error": f"Evidence ID '{evidence_id}' not found."}

        tree = {
            "evidence_id": ev.id,
            "observed_value": ev.observed_value,
            "source_module": ev.source_module,
            "raw_observation_id": ev.raw_observation_id,
            "parents": [self.get_lineage_tree(pid) for pid in ev.parent_ids],
            "children": [self.get_lineage_tree(cid) for cid in ev.children_ids],
        }
        return tree

    @staticmethod
    def build_intelligence_gaps(target: str, evidence_list: list, hypotheses: list = None) -> IntelligenceGaps:
        """
        'WHAT CORVUS DOES NOT KNOW' istihbarat boşlukları raporunu oluşturur.
        """
        gaps = IntelligenceGaps(target)

        verified_sources = set()
        single_sources = set()

        for ev in evidence_list:
            if len(ev.corroborating_sources) > 1:
                verified_sources.add(ev.source_module)
            else:
                single_sources.add(ev.source_module)

        # 1. Bağımsız doğrulanmamış kimlikler
        if not verified_sources:
            gaps.add_gap("Identity not independently verified")
            gaps.add_gap("No second source available")
            gaps.single_source_dependencies.extend(list(single_sources))

        # 2. Çözülemeyen hipotezler
        if hypotheses:
            for hyp in hypotheses:
                h_dict = hyp.to_dict() if hasattr(hyp, "to_dict") else hyp
                if h_dict.get("status") in ("UNTESTED", "REFUTED"):
                    gaps.unresolved_hypotheses.append(h_dict.get("statement"))
                    gaps.add_gap(f"Hypothesis '{h_dict.get('id')}' remains unresolved")

        if not gaps.gaps:
            gaps.add_gap("No major intelligence gaps identified; multi-source corroboration achieved.")

        return gaps
