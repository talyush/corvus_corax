"""Corvus Corax Asset Intelligence Modeling.

Varlıkların sahip olduğu kaynakları (Certificates, DNS records, Subnets, Repos)
1. sınıf istihbarat varlığı (Asset) olarak işler.
"""


class AssetManager:
    """Varlık Kaynak Yöneticisi (Asset Intelligence Manager)."""

    def __init__(self, graph_service):
        self.graph_service = graph_service

    def register_asset(self, owner_entity: str, asset_type: str, asset_value: str, metadata: dict = None) -> bool:
        """Bir varlığa ait kaynak kaydeder."""
        return self.graph_service.bind_asset(owner_entity, asset_type, asset_value, metadata)

    def get_assets_by_owner(self, owner_entity: str) -> list:
        summary = self.graph_service.get_entity_summary(owner_entity)
        return summary.get("assets", [])
