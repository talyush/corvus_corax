import re
import urllib.request
import urllib.error
import urllib.parse

from core.module_base import BaseModule

# ---------------------------------------------------------------------------
# Engine version — visible in output as "Deep Fingerprint Engine v2"
# ---------------------------------------------------------------------------
_ENGINE_VERSION = "v2"


class TechDetectModule(BaseModule):
    """
    Corvus Corax v0.8 — Technology Fingerprinting Module (Deep Fingerprint Engine v2).

    Upgraded from the basic 9-pattern scanner to a 4-layer fingerprinting engine:
      Layer 1 — HTTP Headers  : Server, Runtime, Generator, WAF/CDN signals
      Layer 2 — HTML Body     : meta generator, script ?ver= params, framework paths
      Layer 3 — Cookie Names  : session cookie naming conventions (PHP, Java, .NET, Laravel...)
      Layer 4 — URL Structure : path-based CMS & framework detection
    """
    name = "tech"

    # -----------------------------------------------------------------------
    # Layer 1: HTTP Header Signatures
    # -----------------------------------------------------------------------
    WAF_CDN_HEADERS = [
        # (header_name, value_pattern, display_name)
        ("CF-Ray",                    r".+",                   "Cloudflare"),
        ("X-Sucuri-ID",               r".+",                   "Sucuri WAF"),
        ("X-Firewall-Protection",     r".+",                   "Generic WAF"),
        ("X-Powered-By-Plesk",        r".+",                   "Plesk"),
        ("Server",                    r"cloudflare",           "Cloudflare"),
        ("Server",                    r"awselb|AmazonS3",      "AWS"),
        ("Via",                       r"akamai",               "Akamai CDN"),
        ("X-Akamai-Transformed",      r".+",                   "Akamai CDN"),
        ("X-Cache",                   r".+",                   "Cache Proxy"),
        ("X-Varnish",                 r".+",                   "Varnish Cache"),
        ("X-Cdn",                     r".+",                   "CDN Detected"),
        ("Server",                    r"bunny|bunnycdn",       "BunnyCDN"),
        ("X-Powered-By",              r"imperva",              "Imperva WAF"),
        ("X-Iinfo",                   r".+",                   "Imperva Incapsula"),
    ]

    # -----------------------------------------------------------------------
    # Layer 2: HTML Body Patterns
    # -----------------------------------------------------------------------
    # Format: (category, name, pattern, version_group_index_or_None)
    HTML_PATTERNS = [
        # CMS
        ("cms",       "WordPress",          r"wp-content|wp-includes|wordpress",             None),
        ("cms",       "WordPress",          r'<meta[^>]+generator[^>]+WordPress\s*([\d.]+)', 1),
        ("cms",       "Drupal",             r'drupal|/sites/default/files|drupal-settings',   None),
        ("cms",       "Joomla",             r'joomla|/media/system/js/',                      None),
        ("cms",       "Joomla",             r'<meta[^>]+generator[^>]+Joomla!\s*([\d.]+)',    1),
        ("cms",       "Ghost",              r'ghost-url|content="Ghost\s*([\d.]+)',            1),
        ("cms",       "Shopify",            r'cdn\.shopify\.com|Shopify\.theme',              None),
        ("cms",       "Magento",            r'Magento|mage/cookies',                          None),
        ("cms",       "TYPO3",              r'typo3temp|This website is powered by TYPO3',   None),
        ("cms",       "HubSpot CMS",        r'hs-scripts\.com|hsforms\.net',                  None),
        ("cms",       "Webflow",            r'webflow\.com|w-webflow-badge',                  None),
        ("cms",       "Squarespace",        r'squarespace\.com|static\.squarespace\.com',     None),
        ("cms",       "Wix",               r'wix\.com|wixstatic\.com',                       None),

        # JS Frameworks & Libraries
        ("js",        "React",              r'data-reactroot|react(?:\.min)?\.js',            None),
        ("js",        "Vue.js",             r'vue(?:\.runtime)?(?:\.min)?\.js|data-v-[a-f0-9]+', None),
        ("js",        "Angular",            r'ng-version="([\d.]+)"|angular(?:\.min)?\.js',   1),
        ("js",        "Next.js",            r'__next|_next/static/',                          None),
        ("js",        "Nuxt.js",            r'__nuxt|_nuxt/',                                 None),
        ("js",        "Svelte",             r'__svelte|svelte-',                              None),
        ("js",        "Ember.js",           r'ember(?:\.min)?\.js|Ember\.VERSION',             None),
        ("js",        "Backbone.js",        r'backbone(?:\.min)?\.js',                        None),
        ("js",        "jQuery",             r'jquery(?:\.min)?\.js\?ver=([\d.]+)',             1),
        ("js",        "jQuery",             r'jquery[-/]([\d.]+)(?:\.min)?\.js',              1),
        ("js",        "Bootstrap",          r'bootstrap(?:\.min)?\.(?:css|js)\?ver=([\d.]+)', 1),
        ("js",        "Bootstrap",          r'bootstrap[-/]([\d.]+)',                          1),
        ("js",        "Tailwind CSS",       r'tailwind(?:\.min)?\.css',                       None),
        ("js",        "Alpine.js",          r'alpinejs|Alpine\.js',                           None),
        ("js",        "htmx",              r'htmx\.org|hx-get|hx-post',                      None),
        ("js",        "GSAP",              r'gsap(?:\.min)?\.js|TweenMax',                   None),

        # Backend Frameworks (via HTML signals)
        ("framework", "Laravel",            r'laravel_session|/vendor/laravel|laravel',       None),
        ("framework", "Django",             r'csrfmiddlewaretoken|__admin_media_prefix__',    None),
        ("framework", "Ruby on Rails",      r'csrf-token.*rails|action_dispatch',             None),
        ("framework", "Spring",             r'JSESSIONID|spring|thymeleaf',                   None),
        ("framework", "ASP.NET",            r'__VIEWSTATE|WebResource\.axd|ScriptResource\.axd', None),
        ("framework", "Flask",              r'Werkzeug|flask',                                None),
        ("framework", "Symfony",            r'symfony|/bundles/|sf-toolbar',                  None),
        ("framework", "CodeIgniter",        r'ci_session|CodeIgniter',                        None),
        ("framework", "CakePHP",            r'cakephp|CAKEPHP',                               None),
        ("framework", "Yii",               r'yii|YII_PATH',                                  None),
    ]

    # -----------------------------------------------------------------------
    # Layer 3: Cookie-based Backend Detection
    # -----------------------------------------------------------------------
    COOKIE_PATTERNS = [
        ("PHP",           r"PHPSESSID"),
        ("Java/Spring",   r"JSESSIONID"),
        ("Laravel",       r"laravel_session"),
        ("Ruby on Rails", r"_rails_session"),
        ("ASP.NET",       r"ASP\.NET_SessionId|\.ASPXAUTH"),
        ("Django",        r"csrftoken|sessionid"),
        ("WordPress",     r"wordpress_logged_in|wp-settings-"),
        ("WooCommerce",   r"woocommerce_"),
        ("Magento",       r"MAGE_CACHE|frontend"),
        ("CakePHP",       r"cakephp"),
        ("Yii",          r"_csrf"),
        ("Flask",         r"session"),
    ]

    # -----------------------------------------------------------------------
    # Layer 4: URL / Path Structure
    # -----------------------------------------------------------------------
    PATH_PATTERNS = [
        ("WordPress",     r"/wp-content/|/wp-includes/|/wp-json/"),
        ("Drupal",        r"/sites/default/|/sites/all/"),
        ("Joomla",        r"/components/com_|/modules/mod_"),
        ("Magento",       r"/pub/static/|/skin/frontend/"),
        ("PrestaShop",    r"/modules/|/themes/.*prestashop"),
        ("Next.js",       r"/_next/static/"),
        ("Nuxt.js",       r"/_nuxt/"),
        ("Laravel",       r"/storage/framework/|/vendor/"),
    ]

    # -----------------------------------------------------------------------
    # Runtime / Server extraction from headers
    # -----------------------------------------------------------------------
    RUNTIME_PATTERNS = [
        ("PHP",         r"PHP/([\d.]+)"),
        ("Python",      r"Python/([\d.]+)"),
        ("Ruby",        r"Ruby/([\d.]+)"),
        ("Node.js",     r"Node\.js"),
        (".NET",        r"ASP\.NET"),
        ("Java",        r"Java/([\d.]+)"),
    ]

    SERVER_PATTERNS = [
        ("Apache",    r"Apache/([\d.]+)"),
        ("nginx",     r"nginx/([\d.]+)"),
        ("IIS",       r"Microsoft-IIS/([\d.]+)"),
        ("Caddy",     r"Caddy"),
        ("Gunicorn",  r"gunicorn/([\d.]+)"),
        ("Tomcat",    r"Apache-Coyote|Tomcat"),
        ("LiteSpeed", r"LiteSpeed"),
        ("OpenResty", r"openresty/([\d.]+)"),
    ]

    # -----------------------------------------------------------------------
    # HTTP helpers
    # -----------------------------------------------------------------------
    def _build_request(self, url):
        ua = "Mozilla/5.0 (compatible; CorvusCorax/0.8; TechFingerprint)"
        if self.config:
            ua = self.config.get("user_agent", ua)
        return urllib.request.Request(
            url,
            headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*"},
        )

    def _normalize_target(self, raw):
        raw = raw.strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        return f"https://{raw}"

    def _fetch(self, url, timeout):
        try:
            req = self._build_request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read(512000).decode("utf-8", errors="ignore")
                return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            try:
                body = e.read(512000).decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            return e.code, dict(e.headers), body
        except Exception:
            return None, {}, ""

    # -----------------------------------------------------------------------
    # Layer helpers
    # -----------------------------------------------------------------------
    def _extract_server(self, headers):
        server_raw = headers.get("Server", "") or ""
        for name, pat in self.SERVER_PATTERNS:
            m = re.search(pat, server_raw, re.IGNORECASE)
            if m:
                version = m.group(1) if m.lastindex else None
                return name, version, server_raw
        if server_raw:
            return server_raw, None, server_raw
        return None, None, None

    def _extract_runtime(self, headers):
        powered = headers.get("X-Powered-By", "") or ""
        server  = headers.get("Server", "") or ""
        combined = f"{powered} {server}"
        for name, pat in self.RUNTIME_PATTERNS:
            m = re.search(pat, combined, re.IGNORECASE)
            if m:
                version = m.group(1) if m.lastindex else None
                return name, version
        return None, None

    def _detect_waf_cdn(self, headers):
        found = []
        for hdr, val_pat, display in self.WAF_CDN_HEADERS:
            val = headers.get(hdr, "") or ""
            if val and re.search(val_pat, val, re.IGNORECASE):
                if display not in [f["name"] for f in found]:
                    found.append({"name": display, "evidence": f"{hdr}: {val[:60]}"})
        return found

    def _scan_body(self, body, path=""):
        # Merge body + path for pattern matching
        combined = body + " " + path
        hits = {}   # name -> {version, confidence, category}

        # HTML patterns
        for category, name, pat, ver_grp in self.HTML_PATTERNS:
            m = re.search(pat, combined, re.IGNORECASE)
            if m:
                version = None
                if ver_grp and m.lastindex and m.lastindex >= ver_grp:
                    version = m.group(ver_grp)
                key = name
                if key not in hits:
                    hits[key] = {"version": version, "confidence": "HIGH", "category": category}
                elif version and not hits[key]["version"]:
                    hits[key]["version"] = version

        # Path patterns
        for name, pat in self.PATH_PATTERNS:
            if re.search(pat, combined, re.IGNORECASE):
                key = name
                if key not in hits:
                    hits[key] = {"version": None, "confidence": "MEDIUM", "category": "path"}

        return hits

    def _scan_cookies(self, headers):
        set_cookie = headers.get("Set-Cookie", "") or ""
        found = []
        for name, pat in self.COOKIE_PATTERNS:
            if re.search(pat, set_cookie, re.IGNORECASE):
                if name not in found:
                    found.append(name)
        return found

    def _build_stack_profile(self, server_name, runtime_name, body_hits, cookie_hits):
        parts = []
        if server_name:
            parts.append(server_name)
        if runtime_name:
            parts.append(runtime_name)
        # CMS first
        for name, info in body_hits.items():
            if info["category"] == "cms":
                parts.append(name)
                break
        # Frameworks
        for name, info in body_hits.items():
            if info["category"] == "framework" and name not in parts:
                parts.append(name)
        # Cookie-based backend
        for c in cookie_hits:
            if c not in parts:
                parts.append(c)
        # JS frameworks (top 2)
        js_count = 0
        for name, info in body_hits.items():
            if info["category"] == "js" and name not in parts and js_count < 2:
                parts.append(name)
                js_count += 1
        return " + ".join(parts) if parts else "Unknown"

    # -----------------------------------------------------------------------
    # Main execute
    # -----------------------------------------------------------------------
    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: tech <url_or_host>")

        raw_target = args[0]
        timeout = float(self.config.get("timeout", 8.0)) if self.config else 8.0

        # Try HTTPS first, fallback to HTTP
        urls_to_try = [self._normalize_target(raw_target)]
        if urls_to_try[0].startswith("https://"):
            urls_to_try.append("http://" + raw_target.strip().lstrip("https://").lstrip("http://"))

        status, headers, body = None, {}, ""
        final_url = urls_to_try[0]
        for url in urls_to_try:
            s, h, b = self._fetch(url, timeout)
            if s and h:
                status, headers, body, final_url = s, h, b, url
                break

        if not headers:
            return self.error(f"Could not reach {raw_target}", target=raw_target)

        # Extract domain for context key
        parsed = urllib.parse.urlparse(final_url)
        domain = parsed.netloc or raw_target

        # ------------------------------------------------------------------
        # Layer 1: Server & Runtime
        # ------------------------------------------------------------------
        server_name, server_version, server_raw = self._extract_server(headers)
        runtime_name, runtime_version = self._extract_runtime(headers)
        generator = headers.get("X-Generator", "") or headers.get("X-CMS", "") or ""

        # ------------------------------------------------------------------
        # Layer 1b: WAF / CDN detection
        # ------------------------------------------------------------------
        waf_cdn = self._detect_waf_cdn(headers)

        # ------------------------------------------------------------------
        # Layer 2: HTML body analysis
        # ------------------------------------------------------------------
        body_hits = self._scan_body(body, final_url)

        # ------------------------------------------------------------------
        # Layer 3: Cookie-based detection
        # ------------------------------------------------------------------
        cookie_hits = self._scan_cookies(headers)

        # ------------------------------------------------------------------
        # Categorise results
        # ------------------------------------------------------------------
        cms_hits  = {k: v for k, v in body_hits.items() if v["category"] in ("cms", "path") and k in dict(self.PATH_PATTERNS + [(n, p) for _, n, p, _ in self.HTML_PATTERNS if _ == "cms" or True])}
        # Simpler categorisation by category field
        cms_list  = [{"name": k, **v} for k, v in body_hits.items() if v["category"] == "cms"]
        fw_list   = [{"name": k, **v} for k, v in body_hits.items() if v["category"] in ("framework", "path")]
        js_list   = [{"name": k, **v} for k, v in body_hits.items() if v["category"] == "js"]

        stack_profile = self._build_stack_profile(server_name, runtime_name, body_hits, cookie_hits)

        # ------------------------------------------------------------------
        # Notes
        # ------------------------------------------------------------------
        self.add_note(
            f"[Deep Fingerprint {_ENGINE_VERSION}] {domain}: server={server_raw or 'N/A'}, "
            f"runtime={f'{runtime_name}/{runtime_version}' if runtime_version else runtime_name or 'N/A'}, "
            f"stack={stack_profile}",
            severity="info"
        )
        if waf_cdn:
            names = ', '.join(w['name'] for w in waf_cdn)
            self.add_note(f"WAF/CDN detected for {domain}: {names}", severity="info")
        for cms in cms_list:
            ver = f" {cms['version']}" if cms.get("version") else ""
            self.add_note(f"CMS detected: {cms['name']}{ver} on {domain}", severity="info")

        # ------------------------------------------------------------------
        # Relations
        # ------------------------------------------------------------------
        if server_name:
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="uses_server",
                dst_type="server", dst_value=server_raw or server_name,
                evidence=f"Server header: {server_raw}"
            )
        if runtime_name:
            ver_str = f"/{runtime_version}" if runtime_version else ""
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="uses_runtime",
                dst_type="runtime", dst_value=f"{runtime_name}{ver_str}",
                evidence=f"X-Powered-By / Server header"
            )
        for item in cms_list + fw_list + js_list:
            ver_str = f" {item['version']}" if item.get("version") else ""
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="uses_technology",
                dst_type="tech", dst_value=f"{item['name']}{ver_str}".strip(),
                evidence=f"Detected via {item['category']} fingerprint"
            )
        if waf_cdn:
            for w in waf_cdn:
                self.add_relation(
                    src_type="domain", src_value=domain,
                    relation="protected_by",
                    dst_type="waf_cdn", dst_value=w["name"],
                    evidence=w["evidence"]
                )

        # ------------------------------------------------------------------
        # Build result data
        # ------------------------------------------------------------------
        result_data = {
            "url": final_url,
            "domain": domain,
            "engine": f"Deep Fingerprint Engine {_ENGINE_VERSION}",
            "http_status": status,
            "server": server_raw or server_name,
            "server_name": server_name,
            "server_version": server_version,
            "runtime": runtime_name,
            "runtime_version": runtime_version,
            "generator": generator or None,
            "waf_cdn": waf_cdn,
            "cms": cms_list,
            "frameworks": fw_list,
            "js_libraries": js_list,
            "cookie_signals": cookie_hits,
            "stack_profile": stack_profile,
            # Keep old field names for backward compat with existing output block
            "x_powered_by": headers.get("X-Powered-By"),
        }

        # ------------------------------------------------------------------
        # Save to context
        # ------------------------------------------------------------------
        if self.context:
            self.context.add_tech_intel(domain, result_data)

        return self.success(target=raw_target, data=result_data)
