"""Corvus Corax Abstract Graph Service Interface.

Decoupled Command and Intelligence-Level Query interface.
"""
from abc import ABC, abstractmethod


class AbstractGraphService(ABC):
    """Soyut Graf Servis Arayüzü (Abstract Graph Service Interface)."""

    # --- COMMANDS (C) ---

    @abstractmethod
    def add_entity(self, entity_type: str, entity_value: str, properties: dict = None) -> str:
        """Graf veritabanına yeni bir Varlık (Node) ekler."""
        pass

    @abstractmethod
    def add_relationship(self, src_value: str, dst_value: str, relation_type: str,
                         confidence: float = 0.8, evidence_ids: list = None, properties: dict = None) -> bool:
        """Graf veritabanında iki varlık arasında 1. Sınıf İlişki (Edge) kurar."""
        pass

    @abstractmethod
    def bind_asset(self, owner_value: str, asset_type: str, asset_value: str, properties: dict = None) -> bool:
        """Bir varlığa ait kaynak/varlık (Asset) bağlar."""
        pass

    # --- INTELLIGENCE-LEVEL QUERIES (Q) ---

    @abstractmethod
    def query_paths(self, src_value: str, dst_value: str, max_depth: int = 4) -> list:
        """İki varlık arasındaki istihbarat yollarını ve bağlantı zincirini bulur."""
        pass

    @abstractmethod
    def query_clusters(self, entity_value: str, depth: int = 2) -> dict:
        """Bir varlığın etrafındaki altyapı ve kimlik kümesini (Cluster) çıkarır."""
        pass

    @abstractmethod
    def query_timeline(self, entity_value: str = None) -> list:
        """Olayların gerçekleşme sırası ve zaman kronolojisini (Timeline) çıkarır."""
        pass

    @abstractmethod
    def get_entity_summary(self, entity_value: str) -> dict:
        """Gözlemleri yığmak yerine varlığın detaylı sentezlenmiş özetini üretir."""
        pass

    @abstractmethod
    def find_correlations(self, entity1: str, entity2: str) -> dict:
        """İki varlık arasındaki ortak kaynak ve altyapı korelasyonunu bulur."""
        pass
