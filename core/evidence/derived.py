"""Corvus Corax Derived Evidence Engine.

Düşük seviyeli atomik kanıtlardan yüksek seviyeli türetilmiş istihbarat üretir ve
Key Finding kartlarını inşa eder.
"""
from core.evidence.model import Evidence, KeyFinding


class DerivedEvidenceEngine:
    """Türetilmiş kanıt ve Key Finding inşa motoru."""

    @staticmethod
    def derive_key_findings(evidence_list: list) -> list:
        """
        Kanıt listesini analiz ederek yapılandırılmış KeyFinding kartları üretir.
        """
        key_findings = []

        for ev in evidence_list:
            if ev.status in ("VALIDATED", "DERIVED") or ev.confidence >= 0.5:
                sources = list(ev.corroborating_sources)
                obs_ids = [ev.raw_observation_id] if ev.raw_observation_id else []

                kf = KeyFinding(
                    relationship_str=str(ev.observed_value),
                    status="VERIFIED" if len(sources) > 1 or ev.confidence >= 0.8 else "CANDIDATE",
                    confidence=ev.confidence,
                    supporting_sources=sources,
                    corroboration_count=len(sources),
                    observation_ids=obs_ids,
                )
                key_findings.append(kf)

        return key_findings
