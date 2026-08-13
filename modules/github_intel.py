import re
import json
import urllib.request
import urllib.parse
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class GithubIntelModule(BaseModule):
    """
    v0.9 — GitHub Intelligence Module.

    GitHub kullanıcı adı/email analizi:
    - Kullanıcı profili (kamuya açık GitHub API)
    - Repo listesi ve dil dağılımı
    - Email korelasyonu (commit'lerdeki email — candidate)
    - Kod sızıntısı tespiti (repo içeriğinde email/API anahtarı arama)
    """
    name = "github"

    def _fetch_json(self, url, timeout=10):
        """GitHub API'den JSON verisi çeker."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CorvusCorax/0.9 (+https://github.com/corvus-corax/project)",
                "Accept": "application/vnd.github+json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _fetch_user(self, username, timeout=10):
        """GitHub kullanıcı profilini çeker."""
        return self._fetch_json(f"https://api.github.com/users/{username}", timeout)

    def _fetch_repos(self, username, timeout=10):
        """Kullanıcının repo listesini çeker."""
        data = self._fetch_json(f"https://api.github.com/users/{username}/repos?per_page=30", timeout)
        return data if isinstance(data, list) else []

    def _fetch_commits(self, username, timeout=10):
        """Kullanıcının son commit'lerini çeker (email korelasyonu için)."""
        data = self._fetch_json(f"https://api.github.com/users/{username}/events/public?per_page=30", timeout)
        if not isinstance(data, list):
            return []
        emails = set()
        for event in data:
            payload = event.get("payload", {})
            commits = payload.get("commits", [])
            for commit in commits:
                author = commit.get("author", {})
                email = author.get("email")
                if email:
                    emails.add(email)
        return list(emails)

    def _scan_repo_for_secrets(self, repo_name, timeout=10):
        """
        Repo içeriğinde email/API anahtarı taraması yapar.
        Sadece kamuya açık repo içerikleri taranır.
        """
        # Repo README'sini çek
        readme_url = f"https://api.github.com/repos/{repo_name}/readme"
        data = self._fetch_json(readme_url, timeout)
        if not data or "content" not in data:
            return []
        import base64
        try:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            return []

        findings = []
        # Email tespiti
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
        for email in emails[:5]:
            findings.append({"type": "email", "value": email})
        # API anahtarı tespiti (basit pattern)
        api_keys = re.findall(r"(?:api[_-]?key|secret|token)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{16,})", content, re.IGNORECASE)
        for key in api_keys[:5]:
            findings.append({"type": "possible_secret", "value": key[:8] + "..."})
        return findings

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: github <username> [person]")

        username = args[0].strip()
        person = args[1] if len(args) >= 2 else None

        self.begin_investigation(
            goal=f"GitHub Intelligence — {username}",
            phases=[
                (1, "PROFILE DISCOVERY"),
                (2, "REPOSITORY ANALYSIS"),
                (3, "EMAIL CORRELATION"),
            ],
        )

        # 1. Kullanıcı profili
        def run_profile():
            return self._fetch_user(username)

        self.status_step(f"Fetching GitHub profile for '{username}'", work=run_profile)
        user = self._fetch_user(username)

        if not user or user.get("message") == "Not Found":
            return self.error(f"GitHub user not found: {username}")

        user_info = {
            "name": user.get("name"),
            "login": user.get("login"),
            "bio": user.get("bio"),
            "company": user.get("company"),
            "location": user.get("location"),
            "blog": user.get("blog"),
            "email": user.get("email"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "created_at": user.get("created_at"),
            "profile_url": user.get("html_url"),
        }

        # 2. Repo listesi
        self.status_step("Fetching repositories")
        repos = self._fetch_repos(username)
        repo_info = []
        for repo in repos[:15]:
            repo_info.append({
                "name": repo.get("name"),
                "language": repo.get("language"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo.get("html_url"),
            })

        # 3. Email korelasyonu (commit'lerden)
        self.status_step("Correlating emails from public commits")
        commit_emails = self._fetch_commits(username)

        # 4. Repo secret taraması (ilk 3 repo)
        self.status_step("Scanning top repos for exposed emails/secrets")
        secret_findings = []
        for repo in repos[:3]:
            repo_full = repo.get("full_name")
            if repo_full:
                findings = self._scan_repo_for_secrets(repo_full)
                for f in findings:
                    f["repo"] = repo_full
                    secret_findings.append(f)

        # --- Varlık Kayıtları ---
        self.add_social_profile("github", username, properties=user_info)
        self.add_entity("github_profile", username, user_info)

        # Repo varlıkları
        for repo in repo_info:
            self.add_entity("repository", repo["name"], repo)

        # --- Temporal Olaylar ---
        self.log_event("github_profile_found", entity=f"social_profile:github/{username}",
                       metadata={"name": user_info.get("name"), "repos": len(repo_info)})

        # --- İlişkiler ---
        # Kişi bağlama (candidate)
        if person:
            self.add_person(person)
            self.add_relation(
                "person", person, "github_profile_candidate", "social_profile", f"github/{username}",
                evidence=f"User-provided association: {person} linked to GitHub profile {username}",
                confidence=0.6,
            )
            self.log_event("github_person_candidate", entity=f"person:{person}",
                           metadata={"username": username, "confidence": 0.6})

        # Email korelasyonu (candidate)
        for email in commit_emails[:5]:
            self.add_email(email)
            self.add_relation(
                "social_profile", f"github/{username}", "github_email_correlation", "email", email,
                evidence=f"Email '{email}' found in public GitHub commit history for {username}",
                confidence=0.6,
            )
            self.log_event("github_email_correlated", entity=f"email:{email}",
                           metadata={"username": username, "confidence": 0.6})

        # Secret bulguları
        for finding in secret_findings:
            self.add_note(
                f"GitHub repo {finding.get('repo')} exposes {finding['type']}: {finding['value']}",
                severity="warning" if finding["type"] == "possible_secret" else "info",
            )

        self.add_note(
            f"GitHub profile {username}: {len(repo_info)} repos, {len(commit_emails)} emails correlated",
            severity="info", confidence=0.8,
        )

        data = {
            "username": username,
            "user_info": user_info,
            "repos": repo_info,
            "commit_emails": commit_emails,
            "secret_findings": secret_findings,
            "person_candidate": person,
        }
        return self.success(target=username, data=data)