"""Corvus Perception — Headers SourceAdapter (Wrapper).

Mevcut modules/http_headers.py modülünü Perception pipeline'a bağlar.
HTTP güvenlik başlıkları, eksik başlıklar, sunucu ve teknoloji bilgilerini
normalize eder.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class HeadersAdapter(ModuleSourceAdapter):
    """HTTP Header Audit modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.http_headers import HttpHeadersModule

        source = SourceDeclaration(
            source_id="headers",
            kind="http",
            auth_level="public",
            base_url="https://",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=HttpHeadersModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        # target "example.com" veya "https://example.com" olabilir
        domain = str(target).replace("https://", "").replace("http://", "").split("/")[0]

        hdrs = data.get("headers", {}) or {}
        server = hdrs.get("server")
        powered_by = hdrs.get("x-powered-by")
        missing = data.get("missing_security_headers", []) or []

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {
                "server": server,
                "x-powered-by": powered_by,
                "http_status": data.get("http_status"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        if server:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_server",
                "dst": {"type": "server", "value": server},
                "confidence": 0.9,
            })
        if powered_by:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_technology",
                "dst": {"type": "tech", "value": powered_by},
                "confidence": 0.7,
            })

        # Eksik güvenlik başlıkları -> note (warning)
        for h in missing:
            notes.append({
                "text": f"Eksik güvenlik başlığı: {h} ({domain})",
                "severity": "warning",
                "confidence": 0.9,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}