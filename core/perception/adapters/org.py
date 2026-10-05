"""Corvus Perception — Organization SourceAdapter (Wrapper).

Mevcut modules/org_intel.py modülünü Perception pipeline'a bağlar.
Organizasyon varlığını kaydeder; domain/person/parent bağlarını normalize
eder. Tüm bağlar kullanıcı sağladığı ilişkilerden gelir → KANDİDAT.

Kural: org_owns_domain (0.6) ve owns_subsidiary (0.5) zayıf kanıt;
employs_candidate (0.4) yalnızca aday — doğrulanmış sahiplik değildir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class OrgAdapter(ModuleSourceAdapter):
    """Organization Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.org_intel import OrgIntelModule

        source = SourceDeclaration(
            source_id="org",
            kind="registry",
            auth_level="local",        # context korelasyonu — ağ çağrısı yok
            base_url=None,
            rate_limit=0.0,
        )
        super().__init__(
            module_cls=OrgIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        org_name = data.get("organization") or target
        domain = data.get("domain")
        person = data.get("person")
        parent = data.get("parent")
        infra = data.get("infra_correlations", []) or []

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "organization",
            "value": org_name,
            "properties": {"infra_correlations": len(infra),
                           "domain_link": domain, "parent": parent},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Domain bağlama (candidate)
        if domain:
            entities.append({"type": "domain", "value": domain,
                             "provenance": {"source": "corvus", "status": "candidate"}})
            relations.append({
                "src": {"type": "organization", "value": org_name},
                "relation": "org_owns_domain",
                "dst": {"type": "domain", "value": domain},
                "confidence": 0.6,
            })

        # Personel bağlama (candidate)
        if person:
            entities.append({"type": "person", "value": person,
                             "provenance": {"source": "corvus", "status": "candidate"}})
            relations.append({
                "src": {"type": "organization", "value": org_name},
                "relation": "employs_candidate",
                "dst": {"type": "person", "value": person},
                "confidence": 0.4,   # candidate — doğrulanmış çalışan değil
            })

        # Parent/child (candidate)
        if parent:
            entities.append({"type": "organization", "value": parent,
                             "provenance": {"source": "corvus", "status": "candidate"}})
            relations.append({
                "src": {"type": "organization", "value": parent},
                "relation": "owns_subsidiary",
                "dst": {"type": "organization", "value": org_name},
                "confidence": 0.5,
            })

        if infra:
            for match in infra[:10]:
                notes.append({"text": f"Infrastructure correlation: {match}",
                              "severity": "info", "confidence": 0.6})
        else:
            notes.append({
                "text": f"Organization {org_name} registered — no infra correlation",
                "severity": "info", "confidence": 0.6,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}

    def _target_type(self, normalized: Dict, target: str) -> str:
        return "organization"
