"""Corvus Corax In-Memory Graph Provider (Fallback Engine).

Neo4j veritabanı kapalı olduğunda sıfır kesintiyle çalışan dahili bellek graf motoru.
"""
from datetime import datetime, timezone
from core.graph.interface import AbstractGraphService


class InMemoryGraphService(AbstractGraphService):
    """Dahili Bellek Graf Sağlayıcısı (In-Memory Fallback)."""

    def __init__(self):
        self.nodes = {}          # value -> {type, value, properties, first_seen, last_seen}
        self.relationships = []  # [{src, dst, relation, confidence, evidence_ids, timestamp}]
        self.assets = []         # [{owner, type, value, timestamp}]

    def add_entity(self, entity_type: str, entity_value: str, properties: dict = None) -> str:
        now = datetime.now(timezone.utc).isoformat()
        if entity_value not in self.nodes:
            self.nodes[entity_value] = {
                "type": entity_type,
                "value": entity_value,
                "properties": properties or {},
                "first_seen": now,
                "last_seen": now,
            }
        else:
            self.nodes[entity_value]["last_seen"] = now
            if properties:
                self.nodes[entity_value]["properties"].update(properties)
        return entity_value

    def add_relationship(self, src_value: str, dst_value: str, relation_type: str,
                         confidence: float = 0.8, evidence_ids: list = None, properties: dict = None) -> bool:
        self.add_entity("unknown", src_value)
        self.add_entity("unknown", dst_value)
        now = datetime.now(timezone.utc).isoformat()
        rel_entry = {
            "src": src_value,
            "dst": dst_value,
            "relation": relation_type,
            "confidence": float(confidence),
            "evidence_ids": evidence_ids or [],
            "properties": properties or {},
            "timestamp": now,
        }
        self.relationships.append(rel_entry)
        return True

    def bind_asset(self, owner_value: str, asset_type: str, asset_value: str, properties: dict = None) -> bool:
        self.add_entity("person_or_org", owner_value)
        self.add_entity("asset", asset_value, {"asset_type": asset_type})
        now = datetime.now(timezone.utc).isoformat()
        self.assets.append({
            "owner": owner_value,
            "type": asset_type,
            "value": asset_value,
            "properties": properties or {},
            "timestamp": now,
        })
        self.add_relationship(owner_value, asset_value, f"owns_{asset_type}", confidence=0.9)
        return True

    def query_paths(self, src_value: str, dst_value: str, max_depth: int = 4) -> list:
        # Simple BFS path finding
        queue = [[src_value]]
        visited = {src_value}
        found_paths = []

        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == dst_value:
                found_paths.append(path)
                if len(found_paths) >= 5:
                    break
                continue

            if len(path) >= max_depth:
                continue

            for rel in self.relationships:
                nxt = None
                if rel["src"] == node and rel["dst"] not in visited:
                    nxt = rel["dst"]
                elif rel["dst"] == node and rel["src"] not in visited:
                    nxt = rel["src"]

                if nxt:
                    visited.add(nxt)
                    queue.append(path + [nxt])

        return found_paths

    def query_clusters(self, entity_value: str, depth: int = 2) -> dict:
        cluster_nodes = {entity_value}
        cluster_edges = []

        for rel in self.relationships:
            if rel["src"] == entity_value or rel["dst"] == entity_value:
                cluster_nodes.add(rel["src"])
                cluster_nodes.add(rel["dst"])
                cluster_edges.append(rel)

        return {
            "root": entity_value,
            "nodes": [self.nodes.get(n, {"value": n, "type": "unknown"}) for n in cluster_nodes],
            "edges": cluster_edges,
        }

    def query_timeline(self, entity_value: str = None) -> list:
        timeline = []
        for rel in self.relationships:
            if not entity_value or rel["src"] == entity_value or rel["dst"] == entity_value:
                timeline.append({
                    "timestamp": rel["timestamp"],
                    "event": f"{rel['src']} ==[{rel['relation']}]==> {rel['dst']}",
                    "confidence": rel["confidence"],
                    "evidence_ids": rel["evidence_ids"],
                })
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline

    def get_entity_summary(self, entity_value: str) -> dict:
        ent = self.nodes.get(entity_value, {"value": entity_value, "type": "unknown"})
        rels = [r for r in self.relationships if r["src"] == entity_value or r["dst"] == entity_value]
        assets = [a for a in self.assets if a["owner"] == entity_value]

        return {
            "entity": ent,
            "total_relationships": len(rels),
            "total_assets": len(assets),
            "relationships": rels,
            "assets": assets,
            "first_seen": ent.get("first_seen"),
            "last_seen": ent.get("last_seen"),
        }

    def find_correlations(self, entity1: str, entity2: str) -> dict:
        c1 = self.query_clusters(entity1)
        c2 = self.query_clusters(entity2)

        nodes1 = {n["value"] for n in c1["nodes"] if n["value"] != entity1}
        nodes2 = {n["value"] for n in c2["nodes"] if n["value"] != entity2}

        shared = list(nodes1.intersection(nodes2))

        return {
            "entity1": entity1,
            "entity2": entity2,
            "shared_nodes_count": len(shared),
            "shared_nodes": shared,
        }
