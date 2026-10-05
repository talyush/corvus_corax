"""Corvus Perception — GitHub SourceAdapter (Wrapper).

Mevcut modules/github_intel.py modülünü Perception pipeline'a bağlar.
GitHub profili, repo listesi, commit email korelasyonları ve repo secret
tarama bulgularını normalize eder.

Kural: github_email_correlation ve github_profile_candidate KANDİDAT
ilişkileridir (Similarity != Identity korunur, conf < 1.0).
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class GithubAdapter(ModuleSourceAdapter):
    """GitHub Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.github_intel import GithubIntelModule

        source = SourceDeclaration(
            source_id="github",
            kind="http",
            auth_level="authorized",   # GitHub API rate limit — opsiyonel token
            base_url="https://api.github.com",
            requires_key=False,
            rate_limit=2.0,
        )
        super().__init__(
            module_cls=GithubIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        username = data.get("username") or target
        user_info = data.get("user_info", {}) or {}
        repos = data.get("repos", []) or []
        commit_emails = data.get("commit_emails", []) or []
        secrets = data.get("secret_findings", []) or []
        person = data.get("person_candidate")

        entities = []
        relations = []
        notes = []

        # GitHub profili
        entities.append({
            "type": "social_profile",
            "value": f"github/{username}",
            "properties": {
                "name": user_info.get("name"),
                "bio": user_info.get("bio"),
                "repo_count": len(repos),
                "public_repos": user_info.get("public_repos"),
                "followers": user_info.get("followers"),
            },
            "provenance": {"source": "corvus", "status": "discovered"},
        })
        entities.append({
            "type": "github_profile",
            "value": username,
            "properties": {"name": user_info.get("name")},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        # Repolar
        for repo in repos:
            name = repo.get("name")
            if not name:
                continue
            entities.append({
                "type": "repository",
                "value": name,
                "properties": {"language": repo.get("language"),
                               "stars": repo.get("stars"),
                               "url": repo.get("url")},
                "provenance": {"source": "corvus", "status": "discovered"},
            })

        # Kişi (candidate)
        if person:
            entities.append({
                "type": "person",
                "value": person,
                "properties": {},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "person", "value": person},
                "relation": "github_profile_candidate",
                "dst": {"type": "social_profile", "value": f"github/{username}"},
                "confidence": 0.6,
            })

        # Email korelasyonu (candidate)
        for email in commit_emails[:5]:
            entities.append({
                "type": "email",
                "value": email,
                "properties": {"via": "github_commits"},
                "provenance": {"source": "corvus", "status": "discovered"},
            })
            relations.append({
                "src": {"type": "social_profile", "value": f"github/{username}"},
                "relation": "github_email_correlation",
                "dst": {"type": "email", "value": email},
                "confidence": 0.6,
            })

        # Secret bulguları -> warning not
        for finding in secrets:
            notes.append({
                "text": f"GitHub repo {finding.get('repo')} exposes "
                        f"{finding.get('type')}: {finding.get('value')}",
                "severity": "warning" if finding.get("type") == "possible_secret" else "info",
                "confidence": 0.7,
            })

        notes.append({
            "text": f"GitHub {username}: {len(repos)} repo, {len(commit_emails)} email korrele edildi",
            "severity": "info",
            "confidence": 0.8,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}