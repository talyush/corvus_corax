"""Corvus Corax v1.1 - Temporal Reasoning Engine.

Zamansal çıkarım: Timeline analizi, burst tespiti, olay sıralaması ve
nedensellik zinciri.
"""
from datetime import datetime, timezone


class TemporalReasoningEngine:
    """Zamansal Çıkarım Motoru."""

    # Burst için eşik: N dakika içinde M olay
    BURST_WINDOW_MINUTES = 60
    BURST_MIN_EVENTS = 3

    def detect_temporal_bursts(self, timeline: list) -> list:
        """Kısa sürede yoğunlaşan olayları tespit eder.

        Args:
            timeline: [{timestamp, event, confidence, ...}] listesi

        Returns:
            list[dict] - tespit edilen burst periyotları
        """
        bursts = []
        if len(timeline) < self.BURST_MIN_EVENTS:
            return bursts

        # Timestamp'e göre sırala
        timed = []
        for entry in timeline:
            ts_str = entry.get("timestamp", "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                timed.append((ts, entry))
            except Exception:
                continue

        timed.sort(key=lambda x: x[0])
        if len(timed) < self.BURST_MIN_EVENTS:
            return bursts

        # Kayan pencere analizi
        window_seconds = self.BURST_WINDOW_MINUTES * 60
        i = 0
        while i < len(timed):
            window = [timed[i]]
            j = i + 1
            while j < len(timed):
                span = (timed[j][0] - timed[i][0]).total_seconds()
                if span <= window_seconds:
                    window.append(timed[j])
                    j += 1
                else:
                    break

            if len(window) >= self.BURST_MIN_EVENTS:
                bursts.append({
                    "burst_start": timed[i][0].isoformat(),
                    "burst_end": timed[j - 1][0].isoformat() if j > i else timed[i][0].isoformat(),
                    "event_count": len(window),
                    "events": [e.get("event", "?") for _, e in window],
                    "span_minutes": round(
                        (timed[j - 1][0] - timed[i][0]).total_seconds() / 60, 1
                    ) if j > i else 0,
                    "interpretation": (
                        f"{len(window)} events in {self.BURST_WINDOW_MINUTES} min window - "
                        f"potential coordinated or automated activity"
                    ),
                })
                i = j  # Pencereyi ilerlet
            else:
                i += 1

        return bursts

    def compute_temporal_overlap(self, timeline_a: list, timeline_b: list) -> dict:
        """İki varlığın zaman çizelgelerinin örtüşüp örtüşmediğini hesaplar.

        Args:
            timeline_a: Varlık A'nın timeline eventi
            timeline_b: Varlık B'nin timeline eventi

        Returns:
            dict with overlap_found, overlap_start, overlap_end, overlap_days, interpretation
        """
        def extract_range(timeline):
            timestamps = []
            for e in timeline:
                ts_str = e.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        timestamps.append(ts)
                    except Exception:
                        continue
            return (min(timestamps), max(timestamps)) if timestamps else (None, None)

        a_start, a_end = extract_range(timeline_a)
        b_start, b_end = extract_range(timeline_b)

        if not a_start or not b_start:
            return {
                "overlap_found": False,
                "interpretation": "Insufficient temporal data for overlap analysis",
            }

        # Örtüşme kontrolü: max(a_start, b_start) <= min(a_end, b_end)
        overlap_start = max(a_start, b_start)
        overlap_end = min(a_end, b_end)
        overlap_found = overlap_start <= overlap_end

        if overlap_found:
            overlap_days = (overlap_end - overlap_start).days
            return {
                "overlap_found": True,
                "overlap_start": overlap_start.isoformat(),
                "overlap_end": overlap_end.isoformat(),
                "overlap_days": overlap_days,
                "interpretation": (
                    f"Temporal overlap detected: {overlap_days} days "
                    f"({overlap_start.strftime('%Y-%m-%d')} - {overlap_end.strftime('%Y-%m-%d')}). "
                    f"Entities were simultaneously active - potential coordination window."
                ),
            }
        else:
            gap_days = (overlap_start - overlap_end).days
            return {
                "overlap_found": False,
                "gap_days": gap_days,
                "interpretation": (
                    f"No temporal overlap. Activity windows are separated by ~{gap_days} days. "
                    f"Temporal bridge hypothesis is weakened."
                ),
            }

    def infer_temporal_ordering(self, hypotheses: list) -> list:
        """Hipotezlerin zaman sırasını çıkarır (hangi önce gerçekleşti?).

        Args:
            hypotheses: Hypothesis nesneleri listesi

        Returns:
            list[dict] - Zaman sırasına göre sıralanmış hipotez özeti
        """
        ordered = []
        for h in hypotheses:
            first_update = None
            if h.belief.likelihood_history:
                # İlk kanıt uygulandığı zaman
                first_update = h.belief.created_at
            ordered.append({
                "hypothesis_id": h.hypothesis_id,
                "claim": h.claim[:60],
                "status": h.status,
                "generated_at": h.generated_at,
                "first_evidence_at": first_update,
                "last_updated": h.last_updated,
                "posterior": round(h.posterior, 4),
            })

        # Üretilme zamanına göre sırala
        ordered.sort(key=lambda x: x.get("generated_at", ""))
        for i, item in enumerate(ordered):
            item["temporal_order"] = i + 1

        return ordered

    def build_causal_chain(self, timeline: list, hypotheses: list) -> list:
        """Olaylar ve hipotezleri birleştiren nedensellik zinciri üretir.

        Kronolojik olayları hipotez geçişleriyle bağlar:
        Olay -> Hipotez üretildi -> Kanıt uygulandı -> Durum değişti

        Returns:
            list[dict] - nedensellik zinciri adımları
        """
        chain = []

        # Timeline olayları
        for entry in sorted(timeline, key=lambda e: e.get("timestamp", "")):
            chain.append({
                "step_type": "OBSERVATION",
                "timestamp": entry.get("timestamp", ""),
                "description": entry.get("event", ""),
                "confidence": entry.get("confidence", 0.0),
            })

        # Hipotez oluşturma ve güncelleme adımları
        for h in sorted(hypotheses, key=lambda hx: hx.generated_at):
            chain.append({
                "step_type": "HYPOTHESIS_GENERATED",
                "timestamp": h.generated_at,
                "description": f"Hypothesis generated: {h.claim[:60]}",
                "hypothesis_id": h.hypothesis_id,
            })
            for update in h.belief.likelihood_history:
                chain.append({
                    "step_type": "BAYESIAN_UPDATE",
                    "timestamp": h.belief.last_updated,
                    "description": (
                        f"[{h.hypothesis_id}] Evidence '{update['evidence_id']}' applied: "
                        f"{update['prior_before']:.3f} -> {update['posterior_after']:.3f} "
                        f"(delta: {update['delta']:+.3f})"
                    ),
                    "hypothesis_id": h.hypothesis_id,
                    "evidence_id": update["evidence_id"],
                    "delta": update["delta"],
                })
            chain.append({
                "step_type": "HYPOTHESIS_STATUS",
                "timestamp": h.last_updated,
                "description": f"[{h.hypothesis_id}] Status: {h.status} (posterior={h.posterior:.3f})",
                "hypothesis_id": h.hypothesis_id,
                "status": h.status,
            })

        # Kronolojik sıraya göre sırala
        chain.sort(key=lambda s: s.get("timestamp", ""))
        return chain
