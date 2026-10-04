"""Corvus Perception — Subdomain SourceAdapter (Wrapper).

Mevcut modules/subdomain_enum.py modülünü Perception pipeline'a bağlar.
Passif kaynaklardan (crt.sh / HackerTarget / RapidDNS / wordlist) bulunan
alt alan adlarını domain entity'lerine + has_subdomain ilişkilerine normalize
eder. Wordlist adayları KANDİDAT'tır (canlı doğrulanmamış).
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class SubdomainAdapter(ModuleSourceAdapter):
    """Subdomain enumeration modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.subdomain_enum import SubdomainEnumModule

        source = SourceDeclaration(
            source_id="subdomain",
            kind="http",
            auth_level="public",
            base_url="https://crt.sh",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=SubdomainEnumModule,
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
        subdomains = data.get("subdomains", []) or []

        entities = []
        relations = []
        notes = []

        # Ana domain (bağlam)
        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {"subdomain_total": data.get("total_count", len(subdomains))},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Alt alan adları — ilişki
        for host in subdomains:
            host = str(host).strip().lower()
            if not host or host == domain:
                continue
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_subdomain",
                "dst": {"type": "domain", "value": host},
                "confidence": 0.9,   # passif kaynak — host canlılığı doğrulanmadı
            })

        if subdomains:
            counts = data.get("counts", {})
            notes.append({
                "text": f"Subdomain enum: {len(subdomains)} unique host "
                        f"(crt.sh={counts.get('crt_sh')}, ht={counts.get('hackertarget')}, "
                        f"rd={counts.get('rapiddns')}, wl={counts.get('wordlist')})",
                "severity": "info",
                "confidence": 0.9,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}