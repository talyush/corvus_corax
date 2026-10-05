"""Corvus Perception — Email Pattern SourceAdapter (Wrapper).

Mevcut modules/email_intel.py modülünü Perception pipeline'a bağlar.
Domain'in email sağlayıcısı, isimlendirme kalıbı ve rol/personel emaillerini
normalize eder.

Kural: email_associated_with (conf 0.3) ve role_email ilişkileri KANDİDAT —
kesin sahiplik kanıtı değildir.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class EmailAdapter(ModuleSourceAdapter):
    """Email Pattern modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.email_intel import EmailIntelModule

        source = SourceDeclaration(
            source_id="email",
            kind="registry",
            auth_level="local",        # DNS context'i okur (ağ çağrısı kendi yapmaz)
            base_url=None,
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=EmailIntelModule,
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
        provider = data.get("provider")
        pattern = data.get("detected_pattern")
        pattern_conf = data.get("pattern_confidence", 0.5)
        role_emails = data.get("role_emails", []) or []
        personal = data.get("personal_emails", []) or []
        suggested = data.get("suggested_formats", []) or []

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "domain",
            "value": domain,
            "properties": {"email_provider": provider,
                           "pattern": pattern,
                           "pattern_confidence": pattern_conf,
                           "suggested_formats": suggested},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        if provider:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "uses_email_provider",
                "dst": {"type": "provider", "value": provider},
                "confidence": 0.9,
            })

        if pattern:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "email_pattern",
                "dst": {"type": "pattern", "value": pattern},
                "confidence": pattern_conf if pattern_conf > 0 else 0.5,
            })

        # Rol/system emailleri (candidate)
        for email in role_emails:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "role_email_associated_with",
                "dst": {"type": "email", "value": email},
                "confidence": 0.5,
            })

        # Kişisel emailler (candidate — düşük güven)
        for email in personal:
            relations.append({
                "src": {"type": "domain", "value": domain},
                "relation": "email_associated_with",
                "dst": {"type": "email", "value": email},
                "confidence": 0.3,
            })

        notes.append({
            "text": f"Email {domain}: provider={provider or 'N/A'}, "
                    f"pattern={pattern or 'N/A'} (conf {pattern_conf})",
            "severity": "info",
            "confidence": 0.8,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}