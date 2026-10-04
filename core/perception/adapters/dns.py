"""Corvus Perception — DNS SourceAdapter (Wrapper).

Mevcut modules/dns_intel.py modülünü Perception pipeline'a bağlar.
DNS kayıtlarından (A/AAAA/MX/NS/SPF/DMARC/DKIM) normalize entity + ilişki
üretir; world model'e yazım Pipeline eligibility gate'inden geçer.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class DnsAdapter(ModuleSourceAdapter):
    """DNS Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.dns_intel import DnsIntelModule

        source = SourceDeclaration(
            source_id="dns",
            kind="dns",
            auth_level="public",
            base_url="8.8.8.8",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=DnsIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        domain = data.get("domain") or target

        entities = []
        relations = []
        notes = []

        # Ana domain varlığı
        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {
                "spf": data.get("spf"),
                "dmarc": data.get("dmarc"),
                "spf_weak": data.get("spf_weak"),
                "dmarc_weak": data.get("dmarc_weak"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # A/AAAA -> IP varlıkları
        for ip in (data.get("A") or []) + (data.get("AAAA") or []):
            ip = str(ip)
            entities.append({
                "type": "ip",
                "value": ip,
                "properties": {"resolved_from": domain},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "resolves_to",
                "dst": {"type": "ip", "value": ip},
                "confidence": 1.0,
            })

        # MX sunucuları
        for mx in (data.get("MX") or []) if isinstance(data.get("MX"), list) else []:
            host = mx.get("host") if isinstance(mx, dict) else str(mx)
            if not host:
                continue
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_mx_server",
                "dst": {"type": "domain", "value": host},
                "confidence": 1.0,
            })

        # NS sunucuları
        for ns in (data.get("NS") or []):
            ns_host = str(ns).rstrip(".").lower()
            if not ns_host:
                continue
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_ns_server",
                "dst": {"type": "domain", "value": ns_host},
                "confidence": 1.0,
            })

        # E-posta güvenlik kayıtları (txt)
        if data.get("spf"):
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_spf_record",
                "dst": {"type": "txt", "value": str(data["spf"])},
                "confidence": 1.0,
            })
        if data.get("dmarc"):
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_dmarc_record",
                "dst": {"type": "txt", "value": str(data["dmarc"])},
                "confidence": 1.0,
            })
        for sel, key in (data.get("dkim") or {}).items():
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_dkim_record",
                "dst": {"type": "txt", "value": f"selector:{sel} -> {str(key)[:30]}..."},
                "confidence": 1.0,
            })

        if data.get("dmarc_weak"):
            notes.append({
                "text": f"DMARC policy '{domain}' 'none' — spoofed mail hâlâ iletilebilir",
                "severity": "warning",
                "confidence": 0.9,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}