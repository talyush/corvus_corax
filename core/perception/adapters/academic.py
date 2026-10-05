"""Corvus Perception — Academic SourceAdapter (Wrapper).

Mevcut modules/academic_intel.py modülünü Perception pipeline'a bağlar.
OpenAlex/Crossref kaynaklı yazar profili, yayınlar ve üniversite
bağlantılarını normalize eder.

Kural: academic_affiliated_with (0.7) ve authored_publication (0.6)
kaynak kaydına dayalıdır ancak doğrulanmış sahiplik değildir (candidate).
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class AcademicAdapter(ModuleSourceAdapter):
    """Academic Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.academic_intel import AcademicIntelModule

        source = SourceDeclaration(
            source_id="academic",
            kind="http",
            auth_level="public",
            base_url="https://api.openalex.org",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=AcademicIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        person_name = (data.get("person")
                       or target.split("@")[0].replace(".", " ").title())
        author = data.get("author_info") or {}
        pubs = data.get("publications", []) or []
        university = data.get("university")
        affils = author.get("affiliations", []) or []

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "person",
            "value": person_name,
            "properties": {"academic": True,
                           "orcid": author.get("orcid"),
                           "h_index": author.get("h_index")},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Akademik profil
        if author:
            prof_name = author.get("display_name") or person_name
            entities.append({
                "type": "academic_profile",
                "value": prof_name,
                "properties": {"orcid": author.get("orcid"),
                               "h_index": author.get("h_index"),
                               "affiliations": affils},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "person", "value": person_name},
                "relation": "has_academic_profile",
                "dst": {"type": "academic_profile", "value": prof_name},
                "confidence": 0.9,
            })

        # Yayınlar (candidate — sorgu yazar onayı değil)
        for pub in pubs:
            title = (pub.get("title") or "Untitled")[:80]
            if not title or title == "Untitled":
                continue
            entities.append({
                "type": "publication",
                "value": title,
                "properties": {"year": pub.get("year"),
                               "doi": pub.get("doi"),
                               "venue": pub.get("venue")},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "person", "value": person_name},
                "relation": "authored_publication",
                "dst": {"type": "publication", "value": title},
                "confidence": 0.6,
            })

        # Üniversite bağlantıları (candidate)
        unis = []
        if university:
            unis.append(university)
        for aff in affils[:3]:
            unis.append(aff)
        for uni in unis:
            entities.append({
                "type": "organization",
                "value": uni,
                "properties": {"org_type": "university"},
                "provenance": {"source": "corvus", "status": "candidate"},
            })
            relations.append({
                "src": {"type": "person", "value": person_name},
                "relation": "academic_affiliated_with",
                "dst": {"type": "organization", "value": uni},
                "confidence": 0.7,
            })

        notes.append({
            "text": f"Academic {person_name}: {len(pubs)} publication, "
                    f"h-index {author.get('h_index') if author else 'N/A'}",
            "severity": "info",
            "confidence": 0.7,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}

    def _target_type(self, normalized: Dict, target: str) -> str:
        return "person"
