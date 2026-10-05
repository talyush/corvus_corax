"""Corvus Perception — Phone SourceAdapter (Wrapper).

Mevcut modules/phone_intel.py modülünü Perception pipeline'a bağlar.
Numara normalizasyonu (E.164), numara tipi ve operatör prefix tespitini
normalize eder. Ağ çağrısı YOK (config kuralları + format analizi).

Kural: has_number_type (0.9) format kesinliği; possible_operator (0.4)
MNP nedeniyle yalnızca tahmin; phone_candidate_for (0.4) KANDİDAT —
kesin sahiplik kanıtı değildir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class PhoneAdapter(ModuleSourceAdapter):
    """Phone Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.phone_intel import PhoneIntelModule

        source = SourceDeclaration(
            source_id="phone",
            kind="registry",
            auth_level="local",        # format + numaralama planı — ağ çağrısı yok
            base_url=None,
            rate_limit=0.0,
        )
        super().__init__(
            module_cls=PhoneIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        phone = data.get("phone") or target
        ntype = data.get("number_type", "unknown")
        op = data.get("operator_prefix") or {}
        person = data.get("person_candidate")

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "phone",
            "value": phone,
            "properties": {"country_code": data.get("country_code"),
                           "local_number": data.get("local_number"),
                           "number_type": ntype},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        relations.append({
            "src": {"type": "phone", "value": phone},
            "relation": "has_number_type",
            "dst": {"type": "number_type", "value": ntype},
            "confidence": 0.9,
        })

        # Operatör prefix — MNP nedeniyle yalnızca tahmin
        possible = op.get("possible_operator")
        if possible and possible != "Unknown":
            relations.append({
                "src": {"type": "phone", "value": phone},
                "relation": "possible_operator",
                "dst": {"type": "operator", "value": possible},
                "confidence": 0.4,   # numara taşınabilirliği — doğrulanamaz
            })

        # Kişi adayı (candidate)
        if person:
            relations.append({
                "src": {"type": "phone", "value": phone},
                "relation": "phone_candidate_for",
                "dst": {"type": "person", "value": person},
                "confidence": 0.4,   # kanıt doğrulanmadı
            })

        notes.append({
            "text": f"Phone {phone}: type={ntype}, "
                    f"operator={possible or 'unknown'} (conf {op.get('confidence', 0)})",
            "severity": "info",
            "confidence": 0.7,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}

    def _target_type(self, normalized: Dict, target: str) -> str:
        return "phone"
