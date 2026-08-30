"""Corvus Corax v1.0 — Nexus Intelligence CLI Module.
"""
from core.module_base import BaseModule
from core.graph.providers.neo4j_provider import Neo4jGraphService
from core.nexus.reasoning import GraphReasoningEngine
from core.nexus.timeline import TemporalTimelineEngine
from core.nexus.assets import AssetManager


class NexusModule(BaseModule):
    """
    v1.0 — Nexus Intelligence Command Suite.
    """
    name = "nexus"

    def execute(self):
        args = self.target or []
        action = args[0] if args else "summary"
        target = args[1] if len(args) > 1 else "target"

        inv = self.begin_investigation(
            f"Nexus Intelligence Engine execution ({action.upper()})",
            ["GRAPH QUERYING", "GRAPH REASONING", "TEMPORAL TIMELINE"]
        )

        graph_service = Neo4jGraphService()
        reasoning_engine = GraphReasoningEngine(graph_service)
        timeline_engine = TemporalTimelineEngine(graph_service)
        asset_manager = AssetManager(graph_service)

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
            self.status_step(f"Executing Intelligence Query '{action}'")

        if action == "query" and len(args) > 2 and args[1] == "paths":
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

        elif action == "query" and len(args) > 2 and args[1] == "clusters":
            cluster_val = args[2]
            cluster_data = graph_service.query_clusters(cluster_val)
            data = {
                "action": "clusters",
                "target": cluster_val,
                "cluster": cluster_data,
            }
            return self.success(target=cluster_val, data=data)

        elif action == "timeline":
            timeline_data = timeline_engine.build_timeline(target if len(args) > 1 else None)
            data = {
                "action": "timeline",
                "target": target,
                "timeline": timeline_data,
            }
            return self.success(target=target, data=data)

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

        # Default: Detailed Entity Summary & Reasoning
        reasoning = reasoning_engine.synthesize_reasoning_statement(target)
        summary = graph_service.get_entity_summary(target)

        data = {
            "action": "summary",
            "target": target,
            "reasoning": reasoning,
            "summary": summary,
        }
        return self.success(target=target, data=data)
