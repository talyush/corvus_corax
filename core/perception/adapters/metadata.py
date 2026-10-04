"""Corvus Perception — Metadata SourceAdapter (Wrapper).

Mevcut modules/metadata_intel.py modülünü Perception pipeline'a bağlar.
robots.txt / sitemap / security.txt / humans.txt / favicon hash bilgilerini
normalize eder; staff email'leri ve favicon hash'i ilişki olarak verir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class MetadataAdapter(ModuleSourceAdapter):
    """Metadata envanter modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.metadata_intel import MetadataIntelModule

        source = SourceDeclaration(
            source_id="metadata",
            kind="http",
            auth_level="public",
            base_url="https://",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=MetadataIntelModule,
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

        # Ana domain
        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {
                "robots_txt": bool(data.get("robots_txt")),
                "sitemap_xml": bool(data.get("sitemap_xml")),
                "security_txt": bool(data.get("security_txt")),
                "humans_txt": bool(data.get("humans_txt")),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # security.txt — contact emailleri
        security = data.get("security_txt") if isinstance(data.get("security_txt"), dict) else {}
        for email in security.get("emails", []) or []:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_security_contact",
                "dst": {"type": "email", "value": email},
                "confidence": 0.9,
            })

        # humans.txt — staff emailleri
        humans = data.get("humans_txt") if isinstance(data.get("humans_txt"), dict) else {}
        for email in humans.get("emails", []) or []:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_staff_email",
                "dst": {"type": "email", "value": email},
                "confidence": 0.8,
            })

        # Favicon hash (Shodan pivot)
        favicon = data.get("favicon")
        if isinstance(favicon, dict) and favicon.get("shodan_hash") is not None:
            entities.append({
                "type": "favicon_hash",
                "value": str(favicon["shodan_hash"]),
                "properties": {"md5": favicon.get("md5"),
                               "url": favicon.get("url")},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_favicon_hash",
                "dst": {"type": "favicon_hash", "value": str(favicon["shodan_hash"])},
                "confidence": 1.0,
            })

        notes.append({
            "text": f"Metadata {domain}: robots={bool(data.get('robots_txt'))}, "
                    f"sitemap={bool(data.get('sitemap_xml'))}, "
                    f"sec={bool(data.get('security_txt'))}",
            "severity": "info",
            "confidence": 0.9,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}