"""Corvus Corax Temporal Timeline Engine.

Olayların zaman sırasını (Chronological Sequence) ve 'Ne zaman ve hangi sırayla oldu?'
sorularını analiz eder.
"""


class TemporalTimelineEngine:
    """Zaman Çizelgesi Motoru (Temporal Timeline Engine)."""

    def __init__(self, graph_service):
        self.graph_service = graph_service

    def build_timeline(self, entity_value: str = None) -> list:
        """
        Zaman çizelgesi kayıtlarını kronolojik sırayla oluşturur.
        """
        raw_timeline = self.graph_service.query_timeline(entity_value)

        formatted_sequence = []
        for idx, entry in enumerate(raw_timeline, 1):
            formatted_sequence.append({
                "sequence_num": idx,
                "timestamp": entry.get("timestamp"),
                "event": entry.get("event"),
                "confidence": entry.get("confidence"),
                "evidence_ids": entry.get("evidence_ids"),
            })

        return formatted_sequence
