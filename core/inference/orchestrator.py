"""Corvus Corax v1.1 - Inference Orchestrator.

Tüm çıkarım motorunu (Bayesian, Pattern, Hypothesis, Dynamic Bridge, Uncertainty,
Counterfactual, Temporal, Negative Evidence) koordine eden ana orkestratör.

Pipeline Akışı:
  Evidence List + Relationships
    -> 1. Pattern Extraction (PatternExtractor)
    -> 2. Hypothesis Generation & Competing Hypotheses (HypothesisGenerator)
    -> 3. Bayesian Sequential Updating (BayesianUpdater)
    -> 4. Negative Evidence / Absence Reasoning (NegativeEvidenceEngine)
    -> 5. Lifecycle Status Advance (HypothesisLifecycle)
    -> 6. Dynamic Bridge Exploration (DynamicBridgeEngine)
    -> 7. Uncertainty & Shannon Entropy Quantification (UncertaintyEngine)
    -> 8. Counterfactual & Alternative Explanations (CounterfactualEngine)
    -> 9. Temporal Sequencing & Bursts (TemporalReasoningEngine)
    -> 10. Synthesized Intelligence Report
"""
from typing import Dict, List, Any
from .bayesian import BayesianUpdater
from .pattern import PatternExtractor
from .hypothesis import Hypothesis, HypothesisGenerator, HypothesisLifecycle
from .dynamic_bridge import DynamicBridgeEngine
from .uncertainty import UncertaintyEngine
from .counterfactual import CounterfactualEngine
from .temporal_reasoner import TemporalReasoningEngine
from .negative_evidence import NegativeEvidenceEngine
from .evidence_weight import EvidenceWeighter


class InferenceOrchestrator:
    """Çıkarım ve Akıl Yürütme Orkestratörü."""

    def __init__(self, graph_service):
        self.graph_service = graph_service
        self.weighter = EvidenceWeighter()
        self.updater = BayesianUpdater()
        self.pattern_extractor = PatternExtractor()
        self.generator = HypothesisGenerator()
        self.lifecycle = HypothesisLifecycle()
        self.bridge_engine = DynamicBridgeEngine(graph_service)
        self.uncertainty_engine = UncertaintyEngine()
        self.counterfactual_engine = CounterfactualEngine()
        self.temporal_engine = TemporalReasoningEngine()
        self.negative_engine = NegativeEvidenceEngine(self.updater)

    def run_inference(self, entity_value: str, evidence_list: List[Any],
                      relationships: List[Dict[str, Any]] = None,
                      modules_run: List[str] = None,
                      max_depth: int = 3,
                      confidence_target: float = 0.85) -> Dict[str, Any]:
        """
        Bir hedef varlık için tam çıkarım pipeline'ını baştan sona çalıştırır:
        Evidence -> Pattern -> Hypothesis -> Graph/Path Exploration -> Bayesian Update
        -> Competing Hypotheses -> Uncertainty/Confidence -> Explanation.

        Args:
            entity_value: Hedef varlık
            evidence_list: Doğrulanmış kanıtlar
            relationships: Graf ilişkileri
            modules_run: Çalıştırılan modüller
            max_depth: Çıkarım bütçesi / çok sıçramalı (multi-hop) graf derinlik limiti
            confidence_target: Erken tamamlama / onaylanma hedef güven eşiği (default: 0.85)
        """
        relationships = relationships or []
        modules_run = modules_run or []

        # 1. Pattern Extraction
        patterns = self.pattern_extractor.extract_patterns(evidence_list, relationships)

        # 2. Hypothesis Generation & Competing Hypotheses
        hypotheses = self.generator.generate_competing_hypotheses(
            entity=entity_value,
            relationships=relationships,
            patterns=patterns
        )

        # 3. Multi-Hop Graph & Path Exploration (Inference Budget & Depth Control)
        graph_paths = []
        for rel in relationships:
            dst = rel.get("dst", {})
            dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
            if dst_val and dst_val != entity_value:
                # Bütçe kontrollü çok sıçramalı yol keşfi
                discovered_paths = self.graph_service.query_paths(entity_value, dst_val, max_depth=max_depth)
                if discovered_paths:
                    graph_paths.extend(discovered_paths)

        # Eğer hiç pattern bulunamadıysa varlık bazlı default hipotez oluşturmayı dene
        if not hypotheses and relationships:
            for rel in relationships:
                src = rel.get("src", {})
                dst = rel.get("dst", {})
                src_val = src.get("value", "") if isinstance(src, dict) else str(src)
                dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
                if src_val == entity_value or dst_val == entity_value:
                    h = Hypothesis(
                        hypothesis_type="ASSOCIATION",
                        claim=f"'{src_val}' has relationship '{rel.get('relation')}' with '{dst_val}'",
                        src_entity=src_val,
                        dst_entity=dst_val,
                        prior=rel.get("confidence", 0.4),
                    )
                    hypotheses.append(h)

        # 3. Bayesian Updating
        for h in hypotheses:
            self.lifecycle.register(h)
            # İlgili kanıtları eşle ve uygula
            relevant_evs = [
                ev for ev in evidence_list
                if (getattr(ev, "target", "") in (h.src_entity, h.dst_entity) or
                    getattr(ev, "observed_value", "") in (h.src_entity, h.dst_entity))
            ]
            for ev in relevant_evs:
                h.supporting_evidence_ids.append(getattr(ev, "id", "ev-gen"))
            if relevant_evs:
                self.updater.batch_update(h.belief, relevant_evs)

        # 4. Negative Evidence Reasoning
        observed_types = {getattr(ev, "evidence_type", "") for ev in evidence_list}
        absent_records = self.negative_engine.assess_expected_but_absent(
            entity_value=entity_value,
            modules_run=modules_run,
            observed_evidence_types=observed_types
        )
        self.negative_engine.batch_apply_negative_evidence(hypotheses, absent_records)

        # 5. Lifecycle Status Advancement
        for h in hypotheses:
            self.lifecycle.advance(h)

        confirmed_hypotheses = self.lifecycle.get_confirmed()
        active_hypotheses = self.lifecycle.get_active()
        refuted_hypotheses = self.lifecycle.get_refuted()

        # 6. Uncertainty Quantification
        uncertainty_report = self.uncertainty_engine.generate_uncertainty_report(hypotheses)
        knowledge_gaps = self.uncertainty_engine.generate_knowledge_gaps(
            hypotheses=hypotheses,
            entity=entity_value,
            modules_run=modules_run
        )

        # 7. Counterfactual & Alternative Explanations
        counterfactuals = []
        for h in hypotheses:
            cf_confirm = self.counterfactual_engine.what_would_confirm(h)
            cf_refute = self.counterfactual_engine.what_would_refute(h)
            counterfactuals.append({
                "hypothesis_id": h.hypothesis_id,
                "confirm_path": cf_confirm,
                "refute_path": cf_refute,
            })
        alternative_explanations = self.counterfactual_engine.generate_alternative_explanations(
            confirmed_hypotheses=confirmed_hypotheses,
            all_hypotheses=hypotheses
        )

        # 8. Temporal Reasoning
        timeline = self.graph_service.query_timeline(entity_value)
        temporal_bursts = self.temporal_engine.detect_temporal_bursts(timeline)
        temporal_order = self.temporal_engine.infer_temporal_ordering(hypotheses)

        # 9. Dynamic Bridge Exploration (Bağlantısız varlıklar için)
        bridges = []
        for rel in relationships:
            dst = rel.get("dst", {})
            dst_val = dst.get("value", "") if isinstance(dst, dict) else str(dst)
            if dst_val and dst_val != entity_value:
                # İkincil varlıkların etrafına köprü var mı bak
                b_res = self.bridge_engine.analyze(entity_value, dst_val)
                if b_res.get("bridge_needed"):
                    bridges.append(b_res)

        return {
            "entity": entity_value,
            "patterns": [p.to_dict() for p in patterns],
            "total_hypotheses": len(hypotheses),
            "confirmed_count": len(confirmed_hypotheses),
            "active_count": len(active_hypotheses),
            "refuted_count": len(refuted_hypotheses),
            "hypotheses": [h.to_dict() for h in hypotheses],
            "confirmed_hypotheses": [h.to_dict() for h in confirmed_hypotheses],
            "active_hypotheses": [h.to_dict() for h in active_hypotheses],
            "refuted_hypotheses": [h.to_dict() for h in refuted_hypotheses],
            "uncertainty_report": uncertainty_report,
            "knowledge_gaps": knowledge_gaps,
            "counterfactuals": counterfactuals,
            "alternative_explanations": alternative_explanations,
            "temporal_bursts": temporal_bursts,
            "temporal_order": temporal_order,
            "dynamic_bridges": bridges,
            "absent_evidence": absent_records,
            "graph_paths": graph_paths,
            "inference_budget": {
                "max_depth": max_depth,
                "confidence_target": confidence_target,
            },
        }
