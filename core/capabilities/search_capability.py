"""Corvus Corax Web Search & Dorking Capability.

Kamuya açık web arama motoru probu (DuckDuckGo HTML / OSINT Dorking).
Arama motorları üzerinden ad-soyad, e-posta, tel no ve sosyal profil keşfi yapar.
"""
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class _SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)

    def handle_data(self, data):
        data_str = data.strip()
        if data_str:
            self.text_chunks.append(data_str)

    def get_text(self):
        return " ".join(self.text_chunks)


class SearchCapability:
    """Arama motoru OSINT ve Dorking yeteneği."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    @staticmethod
    def search_duckduckgo(query: str, max_results: int = 10, timeout: float = 8.0) -> dict:
        """DuckDuckGo HTML arama motoru üzerinden pasif sorgu çalıştırır."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": SearchCapability.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html_raw = resp.read().decode("utf-8", errors="ignore")

            parser = _SimpleHTMLParser()
            parser.feed(html_raw)

            # DuckDuckGo HTML sonuç URL'lerini temizle
            clean_links = []
            for link in parser.links:
                if "/l/?" in link or "uddg=" in link:
                    match = re.search(r"uddg=([^&]+)", link)
                    if match:
                        clean_url = urllib.parse.unquote(match.group(1))
                        if clean_url.startswith("http") and "duckduckgo.com" not in clean_url:
                            clean_links.append(clean_url)

            # E-posta ve telefon desenlerini metinden süz
            full_text = parser.get_text()
            emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text)))
            phones = list(set(re.findall(r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", full_text)))

            return {
                "status": "success",
                "query": query,
                "urls": clean_links[:max_results],
                "discovered_emails": emails,
                "discovered_phones": phones,
                "snippet_summary": full_text[:500],
            }

        except Exception as e:
            return {"status": "error", "query": query, "error": str(e), "urls": [], "discovered_emails": [], "discovered_phones": []}

    @staticmethod
    def generate_osint_dorks(target_name: str, domain: str = None) -> list:
        """Hedef kişi veya kurum için etkili OSINT dork sorguları türetir."""
        name_clean = target_name.strip()
        dorks = [
            f'"{name_clean}"',
            f'"{name_clean}" linkedin OR twitter OR instagram OR facebook',
            f'"{name_clean}" email OR contact OR ozgecmis OR cv',
        ]
        if domain:
            dorks.append(f'site:{domain} "{name_clean}"')
            dorks.append(f'site:linkedin.com/in/ "{name_clean}"')
        return dorks
