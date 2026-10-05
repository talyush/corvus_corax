"""Corvus Perception — Wayback SourceAdapter (Wrapper).

Mevcut modules/wayback_intel.py modülünü Perception pipeline'a bağlar.
Internet Archive web geçmişini (snapshot + CDX) normalize ilişkilere çevirir.
web_history_correlation ilişkisi "possible" politikasıdır (conf 0.4).
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class WaybackAdapter(ModuleSourceAdapter):
    """Wayback Machine modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.wayback_intel import WaybackIntelModule

        source = SourceDeclaration(
            source_id="wayback",
            kind="http",
            auth_level="public",
            base_url="https://web.archive.org",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=WaybackIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        url = data.get("url") or target
        domain = "unknown"
        if "//" in url:
            domain = url.split("//")[1].split("/")[0]
        snapshot = data.get("snapshot") or {}
        cdx = data.get("historical_records", []) or []

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {"record_count": data.get("record_count", len(cdx))},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        if snapshot.get("available") and snapshot.get("url"):
            entities.append({
                "type": "web_snapshot",
                "value": str(snapshot.get("url")),
                "properties": {"original_url": url,
                               "timestamp": snapshot.get("timestamp"),
                               "status": snapshot.get("status")},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "has_web_history",
                "dst": {"type": "web_snapshot", "value": str(snapshot.get("url"))},
                "confidence": 1.0,
            })
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "web_history_correlation",
                "dst": {"type": "web_snapshot", "value": str(snapshot.get("url"))},
                "confidence": 0.4,   # possible politikası
            })

        notes.append({
            "text": f"Wayback {url}: {snapshot.get('timestamp') if snapshot.get('available') else 'yok'} "
                    f"({len(cdx)} kayıt)",
            "severity": "info",
            "confidence": 0.8,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}