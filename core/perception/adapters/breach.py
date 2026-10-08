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
            base_url="https://api.xposedornot.com",
            rate_limit=2.0,   # XposedOrNot 2 req/sn limiti
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
        breakdown = data.get("source_breakdown", {}) or {}
        onion = data.get("onion_links", []) or []
        tor_exit = data.get("tor_exit", {}) or {}
        pastes = data.get("pastes_summary", {}) or {}

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "email",
            "value": email,
            "properties": {"breach_count": count,
                           "risk_level": risk,
                           "breach_sources": breakdown},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        if count > 0:
            relations.append({
                "src": {"type": "email", "value": email},
                "relation": "appeared_in_breaches",
                "dst": {"type": "breach_record", "value": f"{count} sources"},
                "confidence": 0.7,   # kaynak meta-verisi — kesinlik değil
            })

        # v1.4 — .onion / Tor sinyalleri
        onion_total = (breakdown.get("ahmia_onion") or 0) or len(onion)
        if onion:
            entities.append({
                "type": "onion_service",
                "value": onion[0],
                "properties": {"total_mentions": onion_total, "sample": onion[:5]},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "email", "value": email},
                "relation": "mentioned_in_onion_services",
                "dst": {"type": "onion_service", "value": f"{onion_total} services"},
                "confidence": 0.4,
            })

        for ip in (tor_exit.get("matched") or [])[:5]:
            relations.append({
                "src": {"type": "ip", "value": ip},
                "relation": "is_tor_exit_node",
                "dst": {"type": "tor_network", "value": "dan.me.uk list"},
                "confidence": 0.9,
            })

        note_text = f"Email {email} — {count} breach kaynağı, risk: {risk}"
        if onion:
            note_text += f", onion: {len(onion)}"
        if tor_exit.get("matched"):
            note_text += f", tor-exit: {len(tor_exit['matched'])}"
        notes.append({
            "text": note_text,
            "severity": "warning" if risk != "Low" else "info",
            "confidence": 0.7,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}