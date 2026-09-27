"""Corvus Perception — Whois SourceAdapter (Wrapper).

Mevcut modules/whois_lookup.py modülünü Perception pipeline'a bağlar.
Modülün kaynak kodu değişmez: SourceDeclaration + normalize + provenance
sarmalanır; world model'e yazım Pipeline'ın eligibility gate'inden geçer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class WhoisAdapter(ModuleSourceAdapter):
    """WHOIS modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        # Geç import: mevcut modül yüklenir (yeni sistem, yeni değil)
        from modules.whois_lookup import WhoisLookupModule

        source = SourceDeclaration(
            source_id="whois",
            kind="registry",
            auth_level="public",
            base_url="whois.iana.org",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=WhoisLookupModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        """Modül ham çıktısını kanonik forma çevirir.

        ContextManager.add_entity / add_relation imzalarıyla uyumlu:
          entities: [ {type, value, properties} ]
          relations:[ {src, relation, dst, confidence} ]
        """
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}

        entities = []
        relations = []

        # Hedef varlık (domain/ip)
        src_type = "domain" if ("." in target and not target.replace(".", "").isdigit()) else "ip"
        entities.append({
            "type": src_type,
            "value": target,
            "properties": {
                "iana_server": data.get("iana_server"),
                "referral_server": data.get("referral_server"),
                "server_used": data.get("server_used"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Kaynak sunucu ilişkisi (gözlemsel kanıt)
        relations.append({
            "src": {"type": src_type, "value": target},
            "relation": "queried_via_whois",
            "dst": {"type": "whois_server", "value": data.get("server_used") or data.get("referral_server") or "unknown"},
            "confidence": 1.0,
        })

        notes = []
        if data.get("raw"):
            notes.append({
                "text": f"WHOIS raw yanıt ({len(str(data['raw']))} bayt) — provenance hash ile saklanır",
                "severity": "info",
                "confidence": 1.0,
            })

        return {
            "entities": entities,
            "relations": relations,
            "notes": notes,
            "data": data,
        }