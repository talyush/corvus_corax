import re
import json
import urllib.request
import urllib.parse
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class AcademicIntelModule(BaseModule):
    """
    v0.9 — Academic Intelligence Module.

    Akademik profilleri ve yayınları analiz eder:
    - OpenAlex API (ücretsiz, anahtar gerektirmez): yazar/yayın/üniversite arama
    - Crossref API (ücretsiz): DOI/yayın meta verisi
    - Üniversite domain tespiti (email domain'inden)
    - Yayın zaman serisi → temporal olaylar (POL katkısı)
    """
    name = "academic"

    def _fetch_json(self, url, timeout=10):
        """Belirli bir URL'den JSON verisi çeker."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CorvusCorax/0.9 (+https://github.com/corvus-corax/project)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _search_openalex_authors(self, name, timeout=10):
        """OpenAlex API ile yazar araması yapar."""
        url = f"https://api.openalex.org/authors?search={urllib.parse.quote(name)}&per-page=5"
        data = self._fetch_json(url, timeout)
        if not data or "results" not in data:
            return []
        return data["results"]

    def _search_openalex_works(self, name, timeout=10):
        """OpenAlex API ile yayın araması yapar."""
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(name)}&per-page=10"
        data = self._fetch_json(url, timeout)
        if not data or "results" not in data:
            return []
        return data["results"]

    def _detect_university_from_email(self, email):
        """Email domain'inden üniversite kurumu çıkarımı yapar."""
        if not email or "@" not in email:
            return None
        domain = email.split("@")[1].lower()
        # Eğitim domain'leri
        if domain.endswith(".edu.tr") or domain.endswith(".edu") or domain.endswith(".ac.uk"):
            # Domain'den kurum adı çıkar
            parts = domain.split(".")
            if len(parts) >= 2:
                return parts[0].upper()
        return None

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: academic <name_or_email>")

        query = args[0]
        is_email = "@" in query
        person_name = query.split("@")[0].replace(".", " ").replace("_", " ").title() if is_email else query

        self.begin_investigation(
            goal=f"Academic Intelligence — {query}",
            phases=[
                (1, "AUTHOR SEARCH"),
                (2, "PUBLICATION DISCOVERY"),
                (3, "AFFILIATION MAPPING"),
            ],
        )

        # 1. OpenAlex yazar arama
        def run_author_search():
            return self._search_openalex_authors(person_name)

        self.status_step(f"Searching OpenAlex for '{person_name}'", work=run_author_search)
        authors = self._search_openalex_authors(person_name)

        author_info = None
        if authors:
            author = authors[0]
            author_info = {
                "name": author.get("display_name", person_name),
                "orcid": author.get("orcid"),
                "h_index": author.get("summary_stats", {}).get("h_index"),
                "works_count": author.get("works_count", 0),
                "affiliations": [inst.get("display_name") for inst in author.get("affiliations", [])],
            }
            self.status_step(f"Found author: {author_info['name']} (h-index: {author_info.get('h_index')})")
        else:
            self.status_step("No OpenAlex author found — trying publication search")

        # 2. Yayın arama
        self.status_step("Searching publications")
        works = self._search_openalex_works(query)
        publications = []
        for work in works[:10]:
            pub = {
                "title": work.get("title", "Untitled"),
                "year": work.get("publication_year"),
                "doi": work.get("doi"),
                "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name"),
                "authors": [a.get("author", {}).get("display_name") for a in work.get("authorships", [])],
            }
            publications.append(pub)

        # 3. Üniversite domain tespiti
        university = None
        if is_email:
            university = self._detect_university_from_email(query)
            if university:
                self.status_step(f"University domain detected: {university}")

        # --- Varlık Kayıtları ---
        self.add_person(person_name, {
            "academic": True,
            "orcid": author_info.get("orcid") if author_info else None,
            "h_index": author_info.get("h_index") if author_info else None,
        })

        # Akademik profil varlığı
        if author_info:
            self.add_entity("academic_profile", person_name, author_info)

        # Yayın varlıkları ve temporal olaylar
        for pub in publications:
            pub_title = pub.get("title", "Untitled")[:80]
            self.add_entity("publication", pub_title, {
                "year": pub.get("year"),
                "doi": pub.get("doi"),
                "venue": pub.get("venue"),
            })
            self.log_event("publication_found", entity=f"person:{person_name}",
                           metadata={"title": pub_title[:50], "year": pub.get("year")})

        # Üniversite bağlantısı (candidate)
        if university:
            self.add_entity("organization", university, {"type": "university"})
            self.add_relation(
                "person", person_name, "academic_affiliated_with", "organization", university,
                evidence=f"Email domain suggests affiliation with {university} — candidate, not confirmed",
                confidence=0.7,
            )
            self.log_event("academic_affiliation_found", entity=f"person:{person_name}",
                           metadata={"university": university, "confidence": 0.7})

        # OpenAlex affiliation (candidate)
        if author_info and author_info.get("affiliations"):
            for aff in author_info["affiliations"][:3]:
                self.add_entity("organization", aff, {"type": "university"})
                self.add_relation(
                    "person", person_name, "academic_affiliated_with", "organization", aff,
                    evidence=f"OpenAlex author record lists affiliation: {aff}",
                    confidence=0.7,
                )
                self.log_event("academic_affiliation_found", entity=f"person:{person_name}",
                               metadata={"university": aff, "confidence": 0.7})

        self.add_note(
            f"Academic profile for {person_name}: {len(publications)} publications, "
            f"h-index: {author_info.get('h_index') if author_info else 'N/A'}",
            severity="info", confidence=0.7,
        )

        data = {
            "person": person_name,
            "is_email": is_email,
            "author_info": author_info,
            "publications": publications,
            "university": university,
        }
        return self.success(target=query, data=data)