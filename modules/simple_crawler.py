from html.parser import HTMLParser
from urllib.parse import urljoin
import urllib.request
from core.module_base import BaseModule


class _SimplePageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title_parts = []
        self.links = []
        self.forms = []
        self._current_form = None

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)

        if tag == "title":
            self.in_title = True
        elif tag == "a":
            href = attr_map.get("href")
            if href:
                self.links.append(href.strip())
        elif tag == "form":
            self._current_form = {
                "action": attr_map.get("action", "").strip(),
                "method": (attr_map.get("method", "GET") or "GET").upper(),
                "inputs": [],
            }
            self.forms.append(self._current_form)
        elif tag == "input" and self._current_form is not None:
            self._current_form["inputs"].append(
                {
                    "name": attr_map.get("name"),
                    "type": attr_map.get("type", "text"),
                }
            )

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "form":
            self._current_form = None

    def handle_data(self, data):
        if self.in_title and data:
            self.title_parts.append(data.strip())

    def get_title(self):
        return " ".join(p for p in self.title_parts if p).strip() or None


class SimpleCrawlerModule(BaseModule):
    name = "crawl"

    def _normalize_target(self, target):
        target = target.strip()
        if target.startswith("http://") or target.startswith("https://"):
            return target
        return f"http://{target}"

    def _build_request(self, url):
        user_agent = "CorvusCorax/0.3"
        if self.config:
            user_agent = self.config.get("user_agent", user_agent)
        return urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: crawl <url_or_host>")

        raw_target = args[0]
        base_url = self._normalize_target(raw_target)
        timeout = float(self.config.get("timeout", 3.0)) if self.config else 3.0

        last_error = None
        urls_to_try = [base_url]
        if base_url.startswith("http://"):
            urls_to_try.append("https://" + raw_target.strip().replace("http://", ""))

        for url in urls_to_try:
            try:
                request = self._build_request(url)
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    status_code = response.getcode()
                    final_url = response.geturl()
                    html = response.read(400000).decode("utf-8", errors="ignore")

                parser = _SimplePageParser()
                parser.feed(html)

                normalized_links = sorted(
                    {urljoin(final_url, href) for href in parser.links if href}
                )

                normalized_forms = []
                for form in parser.forms:
                    normalized_forms.append(
                        {
                            "action": urljoin(final_url, form.get("action") or ""),
                            "method": form.get("method", "GET"),
                            "inputs": form.get("inputs", []),
                        }
                    )

                title = parser.get_title()
                if title:
                    self.add_relation(
                        src_type="url",
                        src_value=final_url,
                        relation="has_title",
                        dst_type="title",
                        dst_value=title,
                        evidence="web crawl"
                    )

                for link in normalized_links[:20]:
                    self.add_relation(
                        src_type="url",
                        src_value=final_url,
                        relation="links_to",
                        dst_type="url",
                        dst_value=link,
                        evidence="web crawl"
                    )

                for form in normalized_forms:
                    self.add_relation(
                        src_type="url",
                        src_value=final_url,
                        relation="has_form",
                        dst_type="form",
                        dst_value=f"{form.get('method')} -> {form.get('action')}",
                        evidence="web crawl"
                    )

                self.add_note(
                    text=f"Web page crawl completed for {final_url}: status={status_code}, title='{title or ''}', discovered {len(normalized_links)} links & {len(normalized_forms)} forms",
                    severity="info"
                )

                return self.success(
                    target=raw_target,
                    data={
                        "url": final_url,
                        "status_code": status_code,
                        "title": parser.get_title(),
                        "links": normalized_links,
                        "forms": normalized_forms,
                    },
                )
            except Exception as e:
                last_error = e

        return self.error(last_error or "crawl failed", target=raw_target)
