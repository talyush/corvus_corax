from core.module_base import BaseModule


class PivotModule(BaseModule):
    """
    v0.9/Faz 5.5 — Cross-Entity Pivoting (Zincirleme Keşif).

    Bir varlıktan başlayarak ilişkiler üzerinden BFS derinleşme yapar.
    Tek bir ipucundan tüm şirket altyapısını keşfedebilir:
      phone:+90532... → person:ahmet → organization:Acme → domain:acme.com → ip:8.8.8.8
    """
    name = "pivot"

    def _get_relations(self):
        """Ham ve türetilmiş tüm ilişkileri döndürür."""
        relations = self.context.data.get("relations", [])
        derived = self.context.data.get("derived_relations", [])
        return relations + derived

    def _build_graph(self):
        """
        İlişki grafiğini komşuluk listesi olarak kurar.
        Returns: {entity_key: [(neighbor_key, relation_type, confidence)]}
        """
        graph = {}
        for rel in self._get_relations():
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            src_key = f"{src.get('type')}:{src.get('value')}"
            dst_key = f"{dst.get('type')}:{dst.get('value')}"
            if not src.get("value") or not dst.get("value"):
                continue
            # İki yönlü bağla
            graph.setdefault(src_key, []).append((dst_key, rel.get("relation", ""), rel.get("confidence", 1.0)))
            graph.setdefault(dst_key, []).append((src_key, rel.get("relation", ""), rel.get("confidence", 1.0)))
        return graph

    def _bfs_edges(self, start_key, depth, graph):
        """
        BFS ile start'tan itibaren depth kadar derinliğe iner.
        Returns: list of edges {src, dst, relation, confidence, depth}
        """
        edges = []
        visited = {start_key}
        queue = [(start_key, 0)]

        while queue:
            current, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue
            for neighbor, relation, confidence in graph.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                edges.append({
                    "src": current,
                    "dst": neighbor,
                    "relation": relation,
                    "confidence": confidence,
                    "depth": current_depth + 1,
                })
                queue.append((neighbor, current_depth + 1))

        return edges

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: pivot <entity> [--depth=N]")

        entity = args[0]
        # --depth=N flag'ini parse et
        depth = 3
        for arg in args[1:]:
            if arg.startswith("--depth="):
                try:
                    depth = int(arg.split("=", 1)[1])
                except ValueError:
                    pass

        # Entity key oluştur — "person:ahmet" veya sadece "ahmet"
        entity_key = entity
        if ":" not in entity:
            # Context'te hangi türde olduğunu bul
            entities = self.context.data.get("entities", {})
            for key, ent in entities.items():
                if ent.get("value") == entity:
                    entity_key = key
                    break

        # Grafiği kur
        graph = self._build_graph()

        # BFS derinleşme
        edges = self._bfs_edges(entity_key, depth, graph)

        # Keşfedilen varlıkları context'e ekle
        discovered = set()
        for edge in edges:
            discovered.add(edge["dst"])

        self.add_note(
            f"Pivot from {entity_key}: {len(edges)} edges discovered at depth {depth}",
            severity="info",
        )

        data = {
            "start_entity": entity_key,
            "depth": depth,
            "edge_count": len(edges),
            "discovered_entities": sorted(discovered),
            "edges": edges,
        }
        return self.success(target=entity, data=data)