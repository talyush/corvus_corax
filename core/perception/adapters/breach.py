"""Corvus Perception — Breach SourceAdapter (Wrapper).

Mevcut modules/breach_intel.py modülünü Perception pipeline'a bağlar.
Email'in hangi breach kaynaklarında göründüğünü (meta-data) normalize eder.

ETİK KURAL: Hiçbir zaman ham şifre/kimlik verisi yazılmaz; yalnızca
"bu email X kaynaklarında görünüyor" bilgisi dünya modeline girer.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class BreachAdapter(ModuleSourceAdapter):
    """Breach Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.breach_intel import BreachIntelModule

        source = SourceDeclaration(
            source_id="breach",
            kind="http",
            auth_level="public",
            base_url="https://monitor.firefox.com",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=BreachIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        email = data.get("email") or target
        sources = data.get("breach_sources", []) or []
        risk = data.get("risk_level", "Low")
        count = data.get("breach_count", len(sources))

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "email",
            "value": email,
            "properties": {"breach_count": count,
                           "risk_level": risk},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        if count > 0:
            relations.append({
                "src": {"type": "email", "value": email},
                "relation": "appeared_in_breaches",
                "dst": {"type": "breach_record", "value": f"{count} sources"},
                "confidence": 0.7,   # kaynak meta-verisi — kesinlik değil
            })

        notes.append({
            "text": f"Email {email} — {count} breach kaynağı, risk: {risk}",
            "severity": "warning" if risk != "Low" else "info",
            "confidence": 0.7,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}