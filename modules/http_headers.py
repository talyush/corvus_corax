import urllib.request
import urllib.parse
import urllib.error
import re
from core.module_base import BaseModule

class HttpHeadersModule(BaseModule):
    """
    Corvus Corax v0.8 — HTTP Header Intelligence Module.
    Queries a web target, extracts detailed header fields, analyzes security configurations,
    evaluates CORS/Cache/Cookie flags, and profiles technology stacks.
    """
    name = "headers"

    def _normalize_target(self, target):
        target = target.strip()
        if target.startswith("http://") or target.startswith("https://"):
            return target
        return f"https://{target}"  # Prefer HTTPS for security header evaluation

    def _parse_cookie_header(self, cookie_str):
        parts = [p.strip() for p in cookie_str.split(";")]
        if not parts:
            return None
        
        name_val = parts[0].split("=", 1)
        name = name_val[0] if name_val else "Unknown"
        value = name_val[1] if len(name_val) > 1 else ""
        
        httponly = False
        secure = False
        samesite = None
        
        for part in parts[1:]:
            part_lower = part.lower()
            if part_lower == "httponly":
                httponly = True
            elif part_lower == "secure":
                secure = True
            elif part_lower.startswith("samesite="):
                samesite = part.split("=", 1)[1]
                
        return {
            "name": name,
            "value": value[:20] + "..." if len(value) > 20 else value,
            "httponly": httponly,
            "secure": secure,
            "samesite": samesite
        }

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: headers <url_or_host>")

        raw_target = args[0]
        timeout = float(self.config.get("timeout", 5.0)) if self.config else 5.0

        url = self._normalize_target(raw_target)
        user_agent = (self.config or {}).get("user_agent", "CorvusCorax/0.8")

        inv = self.begin_investigation(
            f"Audit HTTP security response posture & cookie attributes for {url}",
            ["HTTP PROBE", "SECURITY COMPLIANCE AUDIT", "COOKIE & CORS EVALUATION"]
        )

        headers = None
        final_url = url
        with inv.phase(0):
            def fetch_headers():
                nonlocal headers, final_url
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    }
                )
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        headers = response.headers
                        final_url = response.url
                except urllib.error.HTTPError as e:
                    headers = e.headers
                    final_url = url
                except Exception as e:
                    if url.startswith("https://"):
                        fallback_url = url.replace("https://", "http://", 1)
                        req_fallback = urllib.request.Request(
                            fallback_url,
                            headers={"User-Agent": user_agent}
                        )
                        try:
                            with urllib.request.urlopen(req_fallback, timeout=timeout) as response:
                                headers = response.headers
                                final_url = response.url
                        except urllib.error.HTTPError as e_fb:
                            headers = e_fb.headers
                            final_url = fallback_url
                        except Exception as ex:
                            raise ex
                    else:
                        raise e

            try:
                self.status_step(f"Dispatching HTTP GET request to {url}", work=fetch_headers)
            except Exception as ex:
                return self.error(f"Failed to connect: {ex}", target=raw_target)

        with inv.phase(1):
            self.status_step("Evaluating security compliance headers (CSP, HSTS, XFO, XCTO)")

        # Parse key fields
        server = headers.get("Server")
        powered_by = headers.get("X-Powered-By")
        aspnet_ver = headers.get("X-AspNet-Version")
        
        csp = headers.get("Content-Security-Policy")
        hsts = headers.get("Strict-Transport-Security")
        xfo = headers.get("X-Frame-Options")
        xcto = headers.get("X-Content-Type-Options")
        referrer_policy = headers.get("Referrer-Policy")
        
        acao = headers.get("Access-Control-Allow-Origin")
        acac = headers.get("Access-Control-Allow-Credentials")
        
        cache_control = headers.get("Cache-Control")
        content_encoding = headers.get("Content-Encoding")
        vary = headers.get("Vary")
        
        # Cookies
        cookie_headers = headers.get_all("Set-Cookie") or []
        parsed_cookies = []
        for cookie_str in cookie_headers:
            parsed = self._parse_cookie_header(cookie_str)
            if parsed:
                parsed_cookies.append(parsed)

        missing_security_headers = []
        if not csp:
            missing_security_headers.append("Content-Security-Policy")
        if not hsts:
            missing_security_headers.append("Strict-Transport-Security")
        if not xfo:
            missing_security_headers.append("X-Frame-Options")
        if not xcto:
            missing_security_headers.append("X-Content-Type-Options")

        # --- Notes Generation (existing risk engine parsing support) ---
        for sh in missing_security_headers:
            # Matches exactly: "Missing security header: Content-Security-Policy (CSP)"
            sh_display = sh
            if sh == "Content-Security-Policy":
                sh_display = "Content-Security-Policy (CSP)"
            elif sh == "Strict-Transport-Security":
                sh_display = "Strict-Transport-Security (HSTS)"
            
            self.add_note(
                text=f"Missing security header: {sh_display}",
                severity="warning"
            )

        if hsts:
            self.add_note(
                text=f"Strict-Transport-Security (HSTS) enabled: {hsts}",
                severity="info"
            )

        # Cookie compliance notes
        for cookie in parsed_cookies:
            warnings = []
            if not cookie["httponly"]:
                warnings.append("HttpOnly flag missing")
            if not cookie["secure"]:
                warnings.append("Secure flag missing")
            
            if warnings:
                self.add_note(
                    text=f"Cookie '{cookie['name']}' security warning: {', '.join(warnings)}",
                    severity="warning"
                )

        if acao == "*":
            self.add_note(
                text=f"CORS Wildcard enabled (Access-Control-Allow-Origin: *) on {raw_target}",
                severity="info"
            )

        # --- Relations ---
        if server:
            self.add_relation(
                src_type="domain",
                src_value=raw_target,
                relation="uses_server",
                dst_type="server",
                dst_value=server,
                evidence=f"HTTP Server Header from {final_url}"
            )
        if powered_by:
            self.add_relation(
                src_type="domain",
                src_value=raw_target,
                relation="uses_technology",
                dst_type="tech",
                dst_value=powered_by,
                evidence="HTTP X-Powered-By Header"
            )
        if aspnet_ver:
            self.add_relation(
                src_type="domain",
                src_value=raw_target,
                relation="uses_technology",
                dst_type="tech",
                dst_value=f"ASP.NET {aspnet_ver}",
                evidence="HTTP X-AspNet-Version Header"
            )

        # Push to ContextManager
        dns_or_host = urllib.parse.urlparse(final_url).netloc.split(":")[0] or raw_target
        
        headers_data = {
            "url": final_url,
            "headers": {
                "server": server,
                "x-powered-by": powered_by,
                "x-aspnet-version": aspnet_ver,
                "content-security-policy": csp,
                "strict-transport-security": hsts,
                "x-frame-options": xfo,
                "x-content-type-options": xcto,
                "referrer-policy": referrer_policy,
                "access-control-allow-origin": acao,
                "access-control-allow-credentials": acac,
                "cache-control": cache_control,
                "content-encoding": content_encoding,
                "vary": vary
            },
            "cookies": parsed_cookies,
            "missing_security_headers": missing_security_headers
        }

        if self.context:
            self.context.add_http_headers(dns_or_host, headers_data)
            
            # Map cookies to technologies in context implicitly if they match well-known framework cookie names
            for cookie in parsed_cookies:
                cname = cookie["name"].lower()
                if cname == "laravel_session":
                    self.add_relation(
                        src_type="domain",
                        src_value=raw_target,
                        relation="uses_technology",
                        dst_type="tech",
                        dst_value="laravel",
                        evidence="Laravel session cookie detected"
                    )
                elif cname in ("phpsessid", "php_session"):
                    self.add_relation(
                        src_type="domain",
                        src_value=raw_target,
                        relation="uses_technology",
                        dst_type="tech",
                        dst_value="php",
                        evidence="PHP session cookie detected"
                    )
                elif cname == "django":
                    self.add_relation(
                        src_type="domain",
                        src_value=raw_target,
                        relation="uses_technology",
                        dst_type="tech",
                        dst_value="django",
                        evidence="Django cookie detected"
                    )

        return self.success(
            target=raw_target,
            data=headers_data
        )
