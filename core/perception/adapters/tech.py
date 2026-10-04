"""Corvus Perception — Tech SourceAdapter (Wrapper).

Mevcut modules/tech_detect.py (Deep Fingerprint Engine v2) modülünü
Perception pipeline'a bağlar. Domain'in teknoloji yığınını (server,
runtime, CMS, framework, WAF/CDN, JS kütüphaneleri) normalize ilişkilere
çevirir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class TechAdapter(ModuleSourceAdapter):
    """Technology fingerprint modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.tech_detect import TechDetectModule

        source = SourceDeclaration(
            source_id="tech",
            kind="http",
            auth_level="public",
            base_url="https://",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=TechDetectModule,
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
            "properties": {"http_status": data.get("http_status"),
                           "stack_profile": data.get("stack_profile")},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Server
        server_raw = data.get("server")
        if server_raw:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_server",
                "dst": {"type": "server", "value": server_raw},
                "confidence": 0.9,
            })

        # Runtime
        runtime = data.get("runtime")
        runtime_ver = data.get("runtime_version")
        if runtime:
            val = f"{runtime}/{runtime_ver}" if runtime_ver else runtime
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_runtime",
                "dst": {"type": "runtime", "value": val},
                "confidence": 0.8,
            })

        # CMS / Framework / JS
        for item in (data.get("cms") or []) + (data.get("frameworks") or []) + (data.get("js_libraries") or []):
            name = item.get("name") if isinstance(item, dict) else str(item)
            if not name:
                continue
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_technology",
                "dst": {"type": "tech", "value": name},
                "confidence": 0.7,   # fingerprint — kesin iddia değil
            })

        # WAF / CDN
        for w in (data.get("waf_cdn") or []):
            wname = w.get("name") if isinstance(w, dict) else str(w)
            if not wname:
                continue
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "protected_by",
                "dst": {"type": "waf_cdn", "value": wname},
                "confidence": 0.8,
            })

        if server_raw:
            notes.append({
                "text": f"Tech {domain}: server={server_raw}, runtime={runtime or 'N/A'}, "
                        f"stack={data.get('stack_profile')}",
                "severity": "info",
                "confidence": 0.9,
            })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}