"""Corvus Perception — Cert SourceAdapter (Wrapper).

Mevcut modules/cert_intel.py modülünü Perception pipeline'a bağlar.
TLS sertifikası -> issued_to(host) / cert_issued_by(issuer) / wildcard_covers
ilişkileri normalize edilir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class CertAdapter(ModuleSourceAdapter):
    """Certificate Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.cert_intel import CertIntelModule

        source = SourceDeclaration(
            source_id="cert",
            kind="tls",
            auth_level="public",
            base_url="https://",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=CertIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        host = data.get("host") or target
        fingerprint = data.get("fingerprint", "")
        issuer = data.get("issuer", "")
        san_list = data.get("san", []) or []
        wildcards = data.get("wildcards", []) or []

        entities = []
        relations = []
        notes = []

        # Sertifika varlığı
        if fingerprint:
            entities.append({
                "type": "certificate",
                "value": fingerprint,
                "properties": {
                    "subject_cn": data.get("subject_cn"),
                    "organization": data.get("organization"),
                    "issuer": issuer,
                    "san": san_list,
                    "wildcard": data.get("wildcard"),
                    "expired": data.get("expired"),
                    "days_remaining": data.get("days_remaining"),
                    "valid_from": data.get("valid_from"),
                    "valid_to": data.get("valid_to"),
                    "serial_number": data.get("serial_number"),
                },
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "certificate", "value": fingerprint},
                "relation": "issued_to",
                "dst": {"type": "host", "value": host},
                "confidence": 1.0,   # TLS uç gözlemi — pratik kesin
            })

        # Host varlığı (bağlam)
        entities.append({
            "type": "host",
            "value": host,
            "properties": {"port": data.get("port")},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Issuer (CA)
        if issuer and fingerprint:
            relations.append({
                "src": {"type": "host", "value": host},
                "relation": "cert_issued_by",
                "dst": {"type": "issuer", "value": issuer},
                "confidence": 0.9,
            })

        # Wildcard kapsamı
        for wc in wildcards:
            relations.append({
                "src": {"type": "certificate", "value": fingerprint},
                "relation": "wildcard_covers",
                "dst": {"type": "wildcard", "value": str(wc)},
                "confidence": 1.0,
            })

        if data.get("expired"):
            notes.append({
                "text": f"CERT {host} expired on {data.get('valid_to')}",
                "severity": "critical",
                "confidence": 1.0,
            })
        elif data.get("days_remaining") is not None and int(data.get("days_remaining", 0)) < 30:
            notes.append({
                "text": f"CERT {host} yakında süresi doluyor ({data.get('days_remaining')} gün)",
                "severity": "warning",
                "confidence": 1.0,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}