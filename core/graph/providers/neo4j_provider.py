"""Corvus Corax Neo4j Graph Provider.

Cypher sorgularını içsel olarak çalıştıran Neo4j Bolt sürücü entegrasyonu.
Bağlantı hatası durumunda otomatik olarak dahili In-Memory sağlayıcıya düşer.
"""
from core.graph.interface import AbstractGraphService
from core.graph.providers.memory_provider import InMemoryGraphService


class Neo4jGraphService(AbstractGraphService):
    """Neo4j Veritabanı Sağlayıcısı (Bolt Protocol Engine)."""

    def __init__(self, uri="bolt://localhost:7687", auth=("neo4j", "corvuscorax123")):
        self.uri = uri
        self.auth = auth
        self.driver = None
        self.memory_fallback = InMemoryGraphService()
        self.connected = False
        self._connect()

    def _connect(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
        except Exception:
            self.connected = False

    def add_entity(self, entity_type: str, entity_value: str, properties: dict = None) -> str:
        self.memory_fallback.add_entity(entity_type, entity_value, properties)
        if not self.connected:
            return entity_value

        cypher = """
        MERGE (e:Entity {value: $value})
        ON CREATE SET e.type = $type, e.first_seen = datetime(), e.last_seen = datetime()
        ON MATCH SET e.last_seen = datetime()
        """
        try:
            with self.driver.session() as session:
                session.run(cypher, value=entity_value, type=entity_type)
        except Exception:
            pass
        return entity_value

    def add_relationship(self, src_value: str, dst_value: str, relation_type: str,
                         confidence: float = 0.8, evidence_ids: list = None, properties: dict = None) -> bool:
        self.memory_fallback.add_relationship(src_value, dst_value, relation_type, confidence, evidence_ids, properties)
        if not self.connected:
            return True

        cypher = """
        MATCH (a:Entity {value: $src}), (b:Entity {value: $dst})
        MERGE (a)-[r:CONNECTED_TO {type: $relation}]->(b)
        ON CREATE SET r.confidence = $confidence, r.evidence_ids = $evidence_ids, r.timestamp = datetime()
        """
        try:
            with self.driver.session() as session:
                session.run(cypher, src=src_value, dst=dst_value, relation=relation_type,
                            confidence=confidence, evidence_ids=evidence_ids or [])
        except Exception:
            pass
        return True

    def bind_asset(self, owner_value: str, asset_type: str, asset_value: str, properties: dict = None) -> bool:
        self.memory_fallback.bind_asset(owner_value, asset_type, asset_value, properties)
        if not self.connected:
            return True

        cypher = """
        MATCH (o:Entity {value: $owner})
        MERGE (a:Asset {value: $asset, type: $type})
        MERGE (o)-[r:OWNS]->(a)
        ON CREATE SET r.timestamp = datetime()
        """
        try:
            with self.driver.session() as session:
                session.run(cypher, owner=owner_value, asset=asset_value, type=asset_type)
        except Exception:
            pass
        return True

    def query_paths(self, src_value: str, dst_value: str, max_depth: int = 4) -> list:
        if not self.connected:
            return self.memory_fallback.query_paths(src_value, dst_value, max_depth)

        cypher = f"""
        MATCH p = shortestPath((a:Entity {{value: $src}})-[*..{max_depth}]-(b:Entity {{value: $dst}}))
        RETURN [n IN nodes(p) | n.value] AS path
        """
        try:
            with self.driver.session() as session:
                result = session.run(cypher, src=src_value, dst=dst_value)
                return [record["path"] for record in result]
        except Exception:
            return self.memory_fallback.query_paths(src_value, dst_value, max_depth)

    def query_clusters(self, entity_value: str, depth: int = 2) -> dict:
        return self.memory_fallback.query_clusters(entity_value, depth)

    def query_timeline(self, entity_value: str = None) -> list:
        return self.memory_fallback.query_timeline(entity_value)

    def get_entity_summary(self, entity_value: str) -> dict:
        return self.memory_fallback.get_entity_summary(entity_value)

    def find_correlations(self, entity1: str, entity2: str) -> dict:
        return self.memory_fallback.find_correlations(entity1, entity2)

    def close(self):
        if self.driver:
            self.driver.close()
