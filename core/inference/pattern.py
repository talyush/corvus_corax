"""Corvus Corax v1.1 - Pattern Extraction Engine.

Evidence listesinden OSINT örüntülerini (pattern) tespit eder.
Her pattern, bir HypothesisGenerator seed'i olarak kullanılır.

Pattern Tipleri:
  OWNERSHIP             - Bir kişi/org'un bir domain/IP/cert'e sahip olduğunu gösteriyor
  INFRASTRUCTURE_CLUSTER - Birden fazla IP/domain/cert aynı altyapıyı paylaşıyor
  IDENTITY_ANCHOR       - Birden fazla kanıt aynı kişiye işaret ediyor
  TEMPORAL_BURST        - Kısa sürede yoğun aktivite, şüpheli pattern
  GEOGRAPHIC_CONCENTRATION - Coğrafi olarak yoğunlaşmış aktivite
  MULTI_SOURCE_CORROBORATION - Farklı bağımsız modüllerden teyit
"""
from collections import defaultdict, Counter


class DetectedPattern:
    """Tespit Edilmiş Örüntü."""

    def __init__(self, pattern_type: str, entities: list, evidence_ids: list,
                 strength: float = 0.5, description: str = ""):
        self.pattern_type = pattern_type
        self.entities = entities  # İlgili varlık değerleri
        self.evidence_ids = evidence_ids
        self.strength = round(float(strength), 4)  # [0.0 - 1.0]
        self.description = description

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "entities": self.entities,
            "evidence_ids": self.evidence_ids,
            "strength": self.strength,
            "description": self.description,
        }


class PatternExtractor:
    """OSINT Örüntü Çıkarma Motoru."""

    # Bir OWNERSHIP pattern için min kanıt eşiği
    OWNERSHIP_MIN_EVIDENCE = 1
    # INFRASTRUCTURE_CLUSTER için min paylaşılan node sayısı
    CLUSTER_MIN_SHARED = 2
    # TEMPORAL_BURST için zaman penceresi (saniye)
    BURST_WINDOW_SECONDS = 3600  # 1 saat

    def extract_patterns(self, evidence_list: list, relationships: list = None) -> list:
        """Evidence ve ilişki listesinden pattern'ları tespit eder.

        Args:
            evidence_list: Evidence nesneleri listesi
            relationships: İsteğe bağlı, context'ten gelen ilişki dicts listesi

        Returns:
            list[DetectedPattern]
        """
        patterns = []
        relationships = relationships or []

        patterns.extend(self._detect_ownership(evidence_list, relationships))
        patterns.extend(self._detect_multi_source_corroboration(evidence_list))
        patterns.extend(self._detect_infrastructure_cluster(relationships))
        patterns.extend(self._detect_identity_anchor(relationships))
        patterns.extend(self._detect_temporal_burst(evidence_list))

        # Strength'e göre sırala
        patterns.sort(key=lambda p: p.strength, reverse=True)
        return patterns

    def _detect_ownership(self, evidence_list: list, relationships: list) -> list:
        """Domain/IP/Cert sahipliği gösteren evidence pattern'ları."""
        patterns = []
        ownership_rels = [
            r for r in relationships
            if any(kw in r.get("relation", "").lower()
                   for kw in ("owns", "registered", "registrant", "whois", "admin"))
        ]

        for rel in ownership_rels:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            src_val = src.get("value", "") if isinstance(src, dict) else str(src)
            dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
            conf = rel.get("confidence", 0.5)

            # Destekleyen kanıtları bul
            supporting = [
                getattr(ev, "id", "?") for ev in evidence_list
                if (getattr(ev, "target", "") == dst_val or
                    getattr(ev, "observed_value", "") == dst_val)
            ]

            if len(supporting) >= self.OWNERSHIP_MIN_EVIDENCE or conf >= 0.7:
                strength = min(1.0, conf + len(supporting) * 0.05)
                patterns.append(DetectedPattern(
                    pattern_type="OWNERSHIP",
                    entities=[src_val, dst_val],
                    evidence_ids=supporting,
                    strength=strength,
                    description=f"'{src_val}' shows ownership indicators over '{dst_val}'"
                ))

        return patterns

    def _detect_multi_source_corroboration(self, evidence_list: list) -> list:
        """Aynı değeri birden fazla bağımsız modülün teyit ettiği pattern."""
        patterns = []
        # (target, type, value) -> sources
        grouped = defaultdict(set)
        ev_map = defaultdict(list)

        for ev in evidence_list:
            key = (
                getattr(ev, "target", "?"),
                getattr(ev, "evidence_type", "?"),
                getattr(ev, "observed_value", "?"),
            )
            grouped[key].add(getattr(ev, "source_module", "unknown"))
            ev_map[key].append(getattr(ev, "id", "?"))

        for (target, ev_type, value), sources in grouped.items():
            if len(sources) >= 2:
                strength = min(1.0, 0.5 + len(sources) * 0.15)
                patterns.append(DetectedPattern(
                    pattern_type="MULTI_SOURCE_CORROBORATION",
                    entities=[target, value],
                    evidence_ids=ev_map[(target, ev_type, value)],
                    strength=strength,
                    description=(
                        f"'{value}' corroborated by {len(sources)} independent sources: "
                        f"{', '.join(sorted(sources))}"
                    )
                ))

        return patterns

    def _detect_infrastructure_cluster(self, relationships: list) -> list:
        """Birden fazla varlığı ortak bir node'a bağlayan altyapı kümesi."""
        patterns = []
        node_connections = defaultdict(set)

        for rel in relationships:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            src_val = src.get("value", "") if isinstance(src, dict) else str(src)
            dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
            if src_val and dst_val:
                node_connections[src_val].add(dst_val)
                node_connections[dst_val].add(src_val)

        for node, neighbors in node_connections.items():
            if len(neighbors) >= self.CLUSTER_MIN_SHARED:
                strength = min(1.0, 0.4 + len(neighbors) * 0.08)
                patterns.append(DetectedPattern(
                    pattern_type="INFRASTRUCTURE_CLUSTER",
                    entities=[node] + sorted(neighbors),
                    evidence_ids=[],
                    strength=strength,
                    description=(
                        f"'{node}' is a cluster hub connected to "
                        f"{len(neighbors)} entities: {', '.join(sorted(neighbors))}"
                    )
                ))

        return patterns

    def _detect_identity_anchor(self, relationships: list) -> list:
        """Birden fazla kanıtın aynı kişi/org'a işaret ettiği anchor pattern."""
        patterns = []
        person_rels = defaultdict(list)

        for rel in relationships:
            src = rel.get("src", {})
            src_type = src.get("type", "") if isinstance(src, dict) else ""
            src_val = src.get("value", "") if isinstance(src, dict) else str(src)
            if src_type in ("person", "email", "username", "org") and src_val:
                dst = rel.get("dst", {})
                dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
                person_rels[src_val].append(dst_val)

        for person, targets in person_rels.items():
            if len(targets) >= 2:
                strength = min(1.0, 0.45 + len(targets) * 0.10)
                patterns.append(DetectedPattern(
                    pattern_type="IDENTITY_ANCHOR",
                    entities=[person] + targets,
                    evidence_ids=[],
                    strength=strength,
                    description=(
                        f"Identity anchor: '{person}' links to "
                        f"{len(targets)} entities across multiple relationship types"
                    )
                ))

        return patterns

    def _detect_temporal_burst(self, evidence_list: list) -> list:
        """Kısa zaman diliminde yoğunlaşan kanıtlar -> Temporal burst."""
        patterns = []
        if len(evidence_list) < 3:
            return patterns

        # Timestamp'e göre sırala
        timed = []
        for ev in evidence_list:
            ts = getattr(ev, "timestamp", None)
            if ts:
                timed.append((ts, ev))
        timed.sort(key=lambda x: x[0])

        if len(timed) < 3:
            return patterns

        # Pencere analizi: ardışık 3+ kanıt aynı saatte mi?
        from datetime import datetime, timezone
        window = []
        for ts_str, ev in timed:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                window.append((ts, ev))
            except Exception:
                continue

        if len(window) >= 3:
            first_ts = window[0][0]
            last_ts = window[-1][0]
            span_seconds = (last_ts - first_ts).total_seconds()
            if span_seconds <= self.BURST_WINDOW_SECONDS:
                ev_ids = [getattr(e, "id", "?") for _, e in window]
                strength = min(1.0, 0.4 + (len(window) / 10))
                patterns.append(DetectedPattern(
                    pattern_type="TEMPORAL_BURST",
                    entities=[getattr(e, "target", "?") for _, e in window],
                    evidence_ids=ev_ids,
                    strength=strength,
                    description=(
                        f"{len(window)} evidence records detected within "
                        f"{int(span_seconds/60)} minutes - potential coordinated activity"
                    )
                ))

        return patterns
