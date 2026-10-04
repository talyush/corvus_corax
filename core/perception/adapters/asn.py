"""Corvus Perception — ASN SourceAdapter (Wrapper).

Mevcut modules/asn.py modülünü Perception pipeline'a bağlar.
IP -> belongs_to_asn / owned_by(organization) / in_cidr(network) normalize
edilir. ASN sahiplikleri KANDİDAT ilişkidir (Similarity != Identity korunur).
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class AsnAdapter(ModuleSourceAdapter):
    """ASN Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.asn import ASNModule

        source = SourceDeclaration(
            source_id="asn",
            kind="http",
            auth_level="public",
            base_url="http://ip-api.com/json",
            rate_limit=45.0,
        )
        super().__init__(
            module_cls=ASNModule,
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

        as_number = data.get("as_number")
        asn_label = data.get("asn")
        org = data.get("organization") or data.get("org")
        isp = data.get("isp")
        cidr = data.get("cidr")

        entities = []
        relations = []
        notes = []

        # IP varlığı
        entities.append({
            "type": "ip",
            "value": ip,
            "properties": {
                "asn": asn_label,
                "as_number": as_number,
                "cidr": cidr,
                "isp": isp,
                "country": data.get("country"),
                "timezone": data.get("timezone"),
                "related_count": data.get("related_count"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # ASN varlığı + ilişki
        if as_number:
            entities.append({
                "type": "asn",
                "value": str(as_number),
                "properties": {"label": asn_label},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "belongs_to_asn",
                "dst": {"type": "asn", "value": str(as_number)},
                "confidence": 0.9,
            })

        # Organization (sahip) — KANDİDAT (whois/ASN tek başına kesin değil)
        if org:
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "owned_by",
                "dst": {"type": "organization", "value": org},
                "confidence": 0.7,
            })

        # CIDR / network
        if cidr:
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "in_cidr",
                "dst": {"type": "network", "value": cidr},
                "confidence": 1.0,
            })

        if org:
            notes.append({
                "text": f"ASN {asn_label} ({org}) — CIDR: {cidr}",
                "severity": "info",
                "confidence": 0.9,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}