"""Corvus Perception — GeoIP SourceAdapter (Wrapper).

Mevcut modules/geoip.py modülünü Perception pipeline'a bağlar.
IP -> konum (located_in) + ISP/org ilişkileri normalize edilir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class GeoipAdapter(ModuleSourceAdapter):
    """GeoIP modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.geoip import GeoipModule

        source = SourceDeclaration(
            source_id="geoip",
            kind="http",
            auth_level="public",
            base_url="http://ip-api.com/json",
            rate_limit=45.0,   # ip-api.com ücretsiz limiti (dakikada ~45)
        )
        super().__init__(
            module_cls=GeoipModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        ip = data.get("ip") or target

        country = data.get("country", "")
        region = data.get("region", "")
        city = data.get("city", "")
        isp = data.get("isp", "")
        org = data.get("org", "")

        entities = []
        relations = []
        notes = []

        # IP varlığı + coğrafi özellikler
        entities.append({
            "type": "ip",
            "value": ip,
            "properties": {
                "country": country,
                "region": region,
                "city": city,
                "isp": isp,
                "org": org,
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Konum varlığı + ilişki
        location_label = f"{city}, {region}, {country}".strip(", ")
        if location_label and location_label != ",":
            entities.append({
                "type": "location",
                "value": location_label,
                "properties": {"latitude": data.get("lat"), "longitude": data.get("lon")},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "located_in",
                "dst": {"type": "location", "value": location_label},
                "confidence": 0.9,
            })

        if org:
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "operated_by",
                "dst": {"type": "organization", "value": org},
                "confidence": 0.8,   # ISP org bilgisi — kesin sahiplik değil
            })

        if isp:
            notes.append({
                "text": f"GeoIP {ip}: {city}, {country} (ISP: {isp})",
                "severity": "info",
                "confidence": 1.0,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}