"""Corvus Corax v1.1 - Dynamic Bridge Engine.

Grafta doğrudan bağlantısı olmayan iki varlık arasında potansiyel
gizli bağlantı (bridge) hipotezleri üretir.

Bridge Tipleri:
  SHARED_INFRASTRUCTURE - Ortak IP/ASN/CDN/Certificate paylaşımı
  TEMPORAL              - Aynı zaman diliminde aktivite örtüşmesi
  TYPE_BASED            - İlişki tipi boşluğu (bilinen varlık tipleri uyumlu ama bağlantı eksik)
  GEOGRAPHIC            - Coğrafi yakınlık / ortak ISP
"""
from .hypothesis import Hypothesis, HypothesisGenerator
from .bayesian import get_prior


class BridgeCandidate:
    """Tek bir köprü adayı."""

    def __init__(self, bridge_type: str, src_entity: str, dst_entity: str,
                 intermediate_node: str = None, evidence_hints: list = None,
                 candidate_strength: float = 0.25):
        self.bridge_type = bridge_type
        self.src_entity = src_entity
        self.dst_entity = dst_entity
        self.intermediate_node = intermediate_node
        self.evidence_hints = evidence_hints or []
        self.candidate_strength = candidate_strength

    def to_dict(self) -> dict:
        return {
            "bridge_type": self.bridge_type,
            "src": self.src_entity,
            "dst": self.dst_entity,
            "intermediate": self.intermediate_node,
            "evidence_hints": self.evidence_hints,
            "candidate_strength": self.candidate_strength,
        }


class DynamicBridgeEngine:
    """Dinamik Köprü Motoru.

    query_paths() boş döndüğünde veya doğrudan `nexus bridge` çağrıldığında
    çalışır. Grafta var olmayan ama olası bağlantıları hipotez olarak modeller.
    """

    def __init__(self, graph_service):
        self.graph_service = graph_service
        self.generator = HypothesisGenerator()

    def find_bridge_candidates(self, src_entity: str, dst_entity: str) -> list:
        """İki varlık arasında bridge adayları üretir.

        1. Shared Infrastructure Bridge - ortak 3. node analizi (k=2 hop)
        2. Temporal Bridge - timeline örtüşmesi
        3. Type-Based Bridge - bilinen tip uyumluluğu

        Args:
            src_entity: Kaynak varlık değeri
            dst_entity: Hedef varlık değeri

        Returns:
            list[BridgeCandidate]
        """
        candidates = []

        # Önce doğrudan yol var mı kontrol et
        direct_paths = self.graph_service.query_paths(src_entity, dst_entity, max_depth=4)
        if direct_paths:
            # Doğrudan bağlantı var - bridge gerekmez
            return []

        # 1. Shared Infrastructure Bridge
        shared_bridge = self._detect_shared_infrastructure(src_entity, dst_entity)
        candidates.extend(shared_bridge)

        # 2. Temporal Bridge
        temporal_bridge = self._detect_temporal_bridge(src_entity, dst_entity)
        candidates.extend(temporal_bridge)

        # 3. Type-Based Bridge
        type_bridge = self._detect_type_based_bridge(src_entity, dst_entity)
        candidates.extend(type_bridge)

        # Strength'e göre sırala
        candidates.sort(key=lambda c: c.candidate_strength, reverse=True)
        return candidates

    def candidates_to_hypotheses(self, candidates: list) -> list:
        """Bridge adaylarını Hypothesis nesnelerine dönüştürür."""
        hypotheses = []
        for cand in candidates:
            h = self.generator.generate_bridge_hypothesis(
                src_entity=cand.src_entity,
                dst_entity=cand.dst_entity,
                bridge_type=cand.bridge_type,
                intermediate_node=cand.intermediate_node,
            )
            # Bridge candidate strength'i prior'ı hafif etkilesin
            adjusted_prior = min(0.45, h.belief.prior + cand.candidate_strength * 0.10)
            h.belief.prior = round(adjusted_prior, 4)
            h.belief.posterior = round(adjusted_prior, 4)
            hypotheses.append(h)
        return hypotheses

    def analyze(self, src_entity: str, dst_entity: str) -> dict:
        """Tam bridge analizi - adaylar + hipotezler.

        Returns:
            dict with candidates, hypotheses, analysis_summary
        """
        candidates = self.find_bridge_candidates(src_entity, dst_entity)
        hypotheses = self.candidates_to_hypotheses(candidates)

        if not candidates:
            # Doğrudan bağlantı var
            direct = self.graph_service.query_paths(src_entity, dst_entity)
            return {
                "src": src_entity,
                "dst": dst_entity,
                "bridge_needed": False,
                "direct_paths": direct,
                "candidates": [],
                "hypotheses": [],
                "analysis_summary": (
                    f"Direct connection found between '{src_entity}' and '{dst_entity}'. "
                    f"No bridge hypothesis needed."
                ),
            }

        return {
            "src": src_entity,
            "dst": dst_entity,
            "bridge_needed": True,
            "direct_paths": [],
            "candidates": [c.to_dict() for c in candidates],
            "hypotheses": [h.to_dict() for h in hypotheses],
            "analysis_summary": (
                f"No direct path found between '{src_entity}' and '{dst_entity}'. "
                f"{len(candidates)} bridge candidate(s) generated: "
                f"{', '.join(c.bridge_type for c in candidates[:3])}."
            ),
        }

    # ─── Private Detection Methods ────────────────────────────────────────

    def _detect_shared_infrastructure(self, src_entity: str, dst_entity: str) -> list:
        """k=2 hop ile ortak altyapı node'u arayışı."""
        candidates = []

        try:
            src_cluster = self.graph_service.query_clusters(src_entity, depth=2)
            dst_cluster = self.graph_service.query_clusters(dst_entity, depth=2)

            src_nodes = {n.get("value", n) if isinstance(n, dict) else n
                         for n in (src_cluster.get("nodes") or [])
                         if (n.get("value", n) if isinstance(n, dict) else n) != src_entity}
            dst_nodes = {n.get("value", n) if isinstance(n, dict) else n
                         for n in (dst_cluster.get("nodes") or [])
                         if (n.get("value", n) if isinstance(n, dict) else n) != dst_entity}

            shared = src_nodes.intersection(dst_nodes)

            for node in sorted(shared)[:3]:  # Max 3 shared intermediate
                strength = 0.40 + len(shared) * 0.05
                candidates.append(BridgeCandidate(
                    bridge_type="SHARED_INFRASTRUCTURE",
                    src_entity=src_entity,
                    dst_entity=dst_entity,
                    intermediate_node=str(node),
                    evidence_hints=[
                        f"'{src_entity}' is connected to '{node}'",
                        f"'{dst_entity}' is connected to '{node}'",
                        f"Shared node '{node}' may represent common infrastructure",
                    ],
                    candidate_strength=round(min(0.75, strength), 4),
                ))
        except Exception:
            pass

        return candidates

    def _detect_temporal_bridge(self, src_entity: str, dst_entity: str) -> list:
        """Zaman damgası örtüşme analizi."""
        candidates = []

        try:
            src_timeline = self.graph_service.query_timeline(src_entity)
            dst_timeline = self.graph_service.query_timeline(dst_entity)

            if not src_timeline or not dst_timeline:
                return candidates

            src_timestamps = [e.get("timestamp", "") for e in src_timeline if e.get("timestamp")]
            dst_timestamps = [e.get("timestamp", "") for e in dst_timeline if e.get("timestamp")]

            if not src_timestamps or not dst_timestamps:
                return candidates

            src_start, src_end = min(src_timestamps), max(src_timestamps)
            dst_start, dst_end = min(dst_timestamps), max(dst_timestamps)

            # Örtüşme var mı?
            overlap = (src_start <= dst_end) and (dst_start <= src_end)
            if overlap:
                candidates.append(BridgeCandidate(
                    bridge_type="TEMPORAL",
                    src_entity=src_entity,
                    dst_entity=dst_entity,
                    intermediate_node=None,
                    evidence_hints=[
                        f"'{src_entity}' active: {src_start[:10]} - {src_end[:10]}",
                        f"'{dst_entity}' active: {dst_start[:10]} - {dst_end[:10]}",
                        "Activity windows overlap - potential coordinated timing",
                    ],
                    candidate_strength=0.22,
                ))
        except Exception:
            pass

        return candidates

    def _detect_type_based_bridge(self, src_entity: str, dst_entity: str) -> list:
        """Entity tip uyumluluğuna dayalı bridge hipotezi.

        Bilinen varlık tiplerine göre aralarında hangi ilişki türü
        mümkün olabilirdi ama grafta yoktur?
        """
        candidates = []

        try:
            src_node = self.graph_service.get_entity_summary(src_entity)
            dst_node = self.graph_service.get_entity_summary(dst_entity)

            src_type = (src_node.get("entity") or {}).get("type", "unknown")
            dst_type = (dst_node.get("entity") or {}).get("type", "unknown")

            # Type çiftine göre missing link türü öner
            type_bridge_map = {
                ("person",  "ip"):      "person -> domain -> ip (missing domain hop)",
                ("ip",      "person"):  "ip -> domain -> person (missing domain hop)",
                ("domain",  "person"):  "domain -> registrant -> person (missing registrant record)",
                ("email",   "ip"):      "email -> domain -> ip (missing domain resolution)",
                ("person",  "cert"):    "person -> domain -> cert (missing domain anchor)",
            }

            bridge_key = (src_type.lower(), dst_type.lower())
            if bridge_key in type_bridge_map:
                hint = type_bridge_map[bridge_key]
                prior_for_type = get_prior(src_type, dst_type)
                candidates.append(BridgeCandidate(
                    bridge_type="TYPE_BASED",
                    src_entity=src_entity,
                    dst_entity=dst_entity,
                    intermediate_node=None,
                    evidence_hints=[
                        f"Entity type pair ({src_type}, {dst_type}) suggests: {hint}",
                        "Type-inferred bridge - no direct edge in current graph",
                        "Run DNS, WHOIS, or Certificate recon to populate missing hop",
                    ],
                    candidate_strength=round(prior_for_type * 0.6, 4),
                ))
        except Exception:
            pass

        return candidates
