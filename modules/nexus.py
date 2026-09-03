"""Corvus Corax v1.1 - Nexus & Inference Engine CLI Module.
"""
from core.module_base import BaseModule
from core.graph.providers.neo4j_provider import Neo4jGraphService
from core.nexus.reasoning import GraphReasoningEngine
from core.nexus.timeline import TemporalTimelineEngine
from core.nexus.assets import AssetManager
from core.evidence.extractor import EvidenceExtractor
from core.evidence.validator import EvidenceValidator
from core.evidence.corroboration import Corroborator
from core.inference.orchestrator import InferenceOrchestrator


class NexusModule(BaseModule):
    """
    v1.1 - Nexus Intelligence & Inference Command Suite.
    """
    name = "nexus"

    def execute(self):
        args = self.target or []
        action = args[0] if args else "summary"
        target = args[1] if len(args) > 1 else "target"

        inv = self.begin_investigation(
            f"Nexus Inference Engine execution ({action.upper()})",
            ["GRAPH SYNC", "INFERENCE ORCHESTRATION", "SYNTHESIS"]
        )

        graph_service = Neo4jGraphService()
        reasoning_engine = GraphReasoningEngine(graph_service)
        timeline_engine = TemporalTimelineEngine(graph_service)
        asset_manager = AssetManager(graph_service)
        orchestrator = InferenceOrchestrator(graph_service)

        # Context'teki varlık ve ilişkileri Graf Servisine yükleyelim
        entities = self.context.data.get("entities", {})
        relations = self.context.data.get("relations", [])

        with inv.phase(0):
            self.status_step(f"Syncing central context graph state ({len(entities)} entities, {len(relations)} relations)")
            for k, ent in entities.items():
                graph_service.add_entity(ent.get("type", "unknown"), ent.get("value", k))
            for rel in relations:
                src = rel.get("src", {}).get("value")
                dst = rel.get("dst", {}).get("value")
                if src and dst:
                    graph_service.add_relationship(src, dst, rel.get("relation", "relates_to"), rel.get("confidence", 0.8))

        with inv.phase(1):
            self.status_step(f"Executing Inference Action '{action}'")

        # 1. Full Inference Pipeline: nexus infer <entity>
        if action in ("infer", "hypotheses", "competing", "uncertainty", "counterfactual", "why"):
            # Context'ten kanıtları topla
            extractor = EvidenceExtractor()
            validator = EvidenceValidator()
            corroborator = Corroborator()

            raw_evidences = []
            for res in self.context.data.get("module_results", []):
                evs = extractor.extract_evidence_from_result(res)
                for e in evs:
                    validator.validate_evidence(e)
                raw_evidences.extend(evs)
            
            validated_evs, _ = corroborator.corroborate_evidence_list(raw_evidences)
            modules_run = [r.get("module") for r in self.context.data.get("module_results", []) if r.get("module")]

            inference_result = orchestrator.run_inference(
                entity_value=target,
                evidence_list=validated_evs,
                relationships=relations,
                modules_run=modules_run
            )

            data = {
                "action": action,
                "target": target,
                "inference": inference_result,
            }
            return self.success(target=target, data=data)

        # 2. Dynamic Bridge Query: nexus bridge <src> <dst>
        elif action == "bridge" and len(args) > 2:
            src_val = args[1]
            dst_val = args[2]
            bridge_analysis = orchestrator.bridge_engine.analyze(src_val, dst_val)
            data = {
                "action": "bridge",
                "src": src_val,
                "dst": dst_val,
                "bridge": bridge_analysis,
            }
            return self.success(target=f"{src_val}<->{dst_val}", data=data)

        # 3. Path Discovery: nexus query paths <src> <dst>
        elif action == "query" and len(args) > 2 and args[1] == "paths":
            src_val = args[2]
            dst_val = args[3] if len(args) > 3 else target
            paths = graph_service.query_paths(src_val, dst_val)
            data = {
                "action": "paths",
                "src": src_val,
                "dst": dst_val,
                "paths": paths,
            }
            return self.success(target=target, data=data)

        # 4. Cluster Discovery: nexus query clusters <target>
        elif action == "query" and len(args) > 2 and args[1] == "clusters":
            cluster_val = args[2]
            cluster_data = graph_service.query_clusters(cluster_val)
            data = {
                "action": "clusters",
                "target": cluster_val,
                "cluster": cluster_data,
            }
            return self.success(target=cluster_val, data=data)

        # 5. Temporal Timeline: nexus timeline <target>
        elif action == "timeline":
            timeline_data = timeline_engine.build_timeline(target if len(args) > 1 else None)
            data = {
                "action": "timeline",
                "target": target,
                "timeline": timeline_data,
            }
            return self.success(target=target, data=data)

        # 6. Correlation: nexus correlation <e1> <e2>
        elif action == "correlation" and len(args) > 2:
            e1 = args[1]
            e2 = args[2]
            corr = graph_service.find_correlations(e1, e2)
            data = {
                "action": "correlation",
                "e1": e1,
                "e2": e2,
                "correlation": corr,
            }
            return self.success(target=f"{e1}<->{e2}", data=data)

        # Default: Summary
        reasoning = reasoning_engine.synthesize_reasoning_statement(target)
        summary = graph_service.get_entity_summary(target)

        data = {
            "action": "summary",
            "target": target,
            "reasoning": reasoning,
            "summary": summary,
        }
        return self.success(target=target, data=data)

