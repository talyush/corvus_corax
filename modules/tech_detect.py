import re
import urllib.request
from core.module_base import BaseModule


class TechDetectModule(BaseModule):
    name = "tech"

    FRAMEWORK_PATTERNS = {
        "wordpress": r"wp-content|wp-includes|wordpress",
        "drupal": r"drupal-settings-json|/sites/default/|drupal",
        "joomla": r"/media/system/js/|joomla",
        "laravel": r"laravel_session|/vendor/laravel|laravel",
        "django": r"csrfmiddlewaretoken|__admin_media_prefix__|django",
        "react": r"data-reactroot|react(?:\.min)?\.js|_next/static/",
        "vue": r"vue(?:\.runtime)?(?:\.min)?\.js|data-v-[a-f0-9]+",
        "angular": r"ng-version|angular(?:\.min)?\.js",
        "nextjs": r"__next|_next/static/",
    }

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

    def _detect_frameworks(self, html_text, headers):
        found = set()
        text = (html_text or "").lower()
        generator = headers.get("X-Generator", "") or headers.get("Generator", "")
        if generator:
            text += " " + str(generator).lower()

        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.add(framework)
        return sorted(found)

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: tech <url_or_host>")

        raw_target = args[0]
        timeout = float(self.config.get("timeout", 3.0)) if self.config else 3.0

        urls_to_try = [self._normalize_target(raw_target)]
        if urls_to_try[0].startswith("http://"):
            urls_to_try.append("https://" + raw_target.strip().replace("http://", ""))

        last_error = None
        for url in urls_to_try:
            try:
                request = self._build_request(url)
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    body = response.read(300000).decode("utf-8", errors="ignore")
                    headers = response.headers

                server = headers.get("Server")
                powered_by = headers.get("X-Powered-By")
                frameworks = self._detect_frameworks(body, headers)

                if self.context:
                    self.context.add_note(
                        text=f"tech detection completed for {url}",
                        source="tech",
                        severity="info",
                    )

                return self.success(
                    target=raw_target,
                    data={
                        "url": url,
                        "server": server,
                        "x_powered_by": powered_by,
                        "frameworks": frameworks,
                    },
                )
            except Exception as e:
                last_error = e

        return self.error(last_error or "detection failed", target=raw_target)
