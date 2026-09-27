"""Corvus Perception — Social SourceAdapter (Wrapper).

Mevcut modules/social_intel.py modülünü Perception pipeline'a bağlar.
Modül değişmez: kanıt (verified profiller) normalize edilir, provenance
eklenir; world model'e yazım Pipeline eligibility gate'inden geçer.

DİKKAT: Sosyal medya profilleri KANDİDAT bilgidir (aynı username farklı
kişilere ait olabilir) — ilişki güveni 1.0 DEĞİLDİR, kanıt zinciri
Similarity != Identity prensibiyle korunur.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class SocialAdapter(ModuleSourceAdapter):
    """Social (username tarama) modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.social_intel import SocialIntelModule

        source = SourceDeclaration(
            source_id="social",
            kind="http",
            auth_level="public",
            base_url="https://social-platforms",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=SocialIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        """Modül ham çıktısını kanonik forma çevirir.

        Verified profiller -> social_profile entity + username entity +
        ilişkiler. Username eşleşmesi CANDIDATE olarak işaretlenir.
        """
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}

        handle = data.get("username") or target
        person_candidate = data.get("person_candidate")
        verified = data.get("verified_profiles", []) or []
        confidence = float(data.get("correlation_confidence", 0.0))
        platforms_found = data.get("platforms_found", []) or []

        entities = []
        relations = []
        notes = []

        # Username varlığı — korelasyon grup anahtarı
        entities.append({
            "type": "username",
            "value": handle,
            "properties": {
                "platforms_found": platforms_found,
                "total_platforms_checked": data.get("platforms_checked", 0),
                "verified_count": len(verified),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Verified sosyal profiller — KANDİDAT (açıkça)
        for pr in verified:
            platform = pr.get("platform", "unknown")
            url = pr.get("url", "")
            entities.append({
                "type": "social_profile",
                "value": f"{platform}/{handle}",
                "properties": {
                    "url": url,
                    "verified": bool(pr.get("verified")),
                    "weight": pr.get("weight", 0.5),
                },
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "username", "value": handle},
                "relation": "username_present_on",
                "dst": {"type": "social_profile", "value": f"{platform}/{handle}"},
                "confidence": 1.0,  # profil URL varlığı — gözlemsel kesin
            })

        # Olası aynı kişi eşleşmesi — CANDIDATE, KESİN DEĞİL
        if person_candidate:
            entities.append({
                "type": "person",
                "value": person_candidate,
                "properties": {},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "person", "value": person_candidate},
                "relation": "possible_username_match",
                "dst": {"type": "username", "value": handle},
                "confidence": max(confidence, 0.15),  # politika tabanlı düşük güven
            })

        if verified:
            notes.append({
                "text": f"'{handle}' {len(verified)} platformda doğrulandı — "
                        f"korelasyon (aynı kişi DEĞİL, olası eşleşme) güven: {confidence:.2f}",
                "severity": "info",
                "confidence": confidence,
            })

        return {
            "entities": entities,
            "relations": relations,
            "notes": notes,
            "data": data,
        }