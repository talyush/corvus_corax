"""Corvus Corax Graph Reasoning Engine.

Graf üzerindeki ilişkileri ve kanıt silsilelerini analiz ederek insan-okunabilir
istihbarat çıkarım cümleleri üretir.
"""


class GraphReasoningEngine:
    """Graf Mantık Yürütme Motoru (Graph Reasoning Engine)."""

    def __init__(self, graph_service):
        self.graph_service = graph_service

    def synthesize_reasoning_statement(self, entity_value: str) -> dict:
        """
        Bir varlığın tüm graf bağlamını sorgular ve sentezlenmiş mantık çıkarımı oluşturur:
        'A ile B arasında X ilişkisi gözlemlendi, ilişki N kanıtla destekleniyor, C ve D ile bağlantılı...'
        """
        summary = self.graph_service.get_entity_summary(entity_value)
        rels = summary.get("relationships", [])
        assets = summary.get("assets", [])

        statements = []
        verified_count = 0
        unverified_count = 0

        for r in rels:
            src = r.get("src")
            dst = r.get("dst")
            rel_type = r.get("relation")
            conf = r.get("confidence", 0.8)
            ev_count = len(r.get("evidence_ids", []))
            other = dst if src == entity_value else src

            if conf >= 0.75:
                verified_count += 1
                st = f"Relationship '{rel_type}' observed between '{entity_value}' and '{other}' (confidence: {conf:.2f}), supported by {ev_count} evidence record(s)."
            else:
                unverified_count += 1
                st = f"Candidate relationship '{rel_type}' linking '{entity_value}' to '{other}' remains UNVERIFIED (confidence: {conf:.2f}). Conclusion is NOT treated as definitive."

            statements.append(st)

        # Asset çıkarımı
        if assets:
            asset_types = set(a.get("type") for a in assets)
            statements.append(f"Target '{entity_value}' holds {len(assets)} verified infrastructure asset(s) across types: {', '.join(asset_types)}.")

        overall_assessment = "CONFIRMED" if verified_count > unverified_count else "CANDIDATE_UNVERIFIABLE"

        return {
            "entity": entity_value,
            "overall_assessment": overall_assessment,
            "verified_relationships": verified_count,
            "unverified_relationships": unverified_count,
            "total_assets": len(assets),
            "reasoning_statements": statements,
        }
