import re
import base64
import hashlib
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

from core.module_base import BaseModule


# ---------------------------------------------------------------------------
# Pure-Python MurmurHash3_x86_32 (Shodan favicon hash compatible)
# No external dependencies required.
# ---------------------------------------------------------------------------
def _murmur3_x86_32(data: bytes, seed: int = 0) -> int:
    length = len(data)
    h1 = seed & 0xFFFFFFFF
    c1 = 0xcc9e2d51
    c2 = 0x1b873593

    nblocks = length // 4
    for i in range(nblocks):
        k1 = int.from_bytes(data[i * 4:i * 4 + 4], "little")
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF
        h1 ^= k1
        h1 = ((h1 << 13) | (h1 >> 19)) & 0xFFFFFFFF
        h1 = (h1 * 5 + 0xe6546b64) & 0xFFFFFFFF

    tail = data[nblocks * 4:]
    k1 = 0
    tail_len = length & 3
    if tail_len >= 3:
        k1 ^= tail[2] << 16
    if tail_len >= 2:
        k1 ^= tail[1] << 8
    if tail_len >= 1:
        k1 ^= tail[0]
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF
        h1 ^= k1

    h1 ^= length
    h1 ^= (h1 >> 16)
    h1 = (h1 * 0x85ebca6b) & 0xFFFFFFFF
    h1 ^= (h1 >> 13)
    h1 = (h1 * 0xc2b2ae35) & 0xFFFFFFFF
    h1 ^= (h1 >> 16)

    # Return signed 32-bit integer (matches Shodan / mmh3 default)
    return h1 if h1 <= 0x7FFFFFFF else h1 - 0x100000000


def _favicon_hash(raw_bytes: bytes) -> int:
    """Compute Shodan-compatible favicon hash (base64 RFC-2045 + MurmurHash3)."""
    b64 = base64.encodebytes(raw_bytes)   # adds \n every 76 chars (RFC 2045)
    return _murmur3_x86_32(b64)


class MetadataIntelModule(BaseModule):
    """
    Corvus Corax v0.8 — Metadata Collection & Analysis Module.

    Fetches and parses common metadata files from a web target:
      - robots.txt       : disallowed paths, sitemaps
      - sitemap.xml      : URL count, structural hints
      - security.txt     : security contacts, PGP keys, policy links
      - humans.txt       : author credits, technology comments
      - favicon.ico      : Shodan-compatible MurmurHash3 fingerprint
    """
    name = "metadata"

    # Paths known to reveal sensitive directories in robots.txt
    SENSITIVE_KEYWORDS = [
        "admin", "backup", "bak", "dev", "test", "staging", "api",
        "config", "conf", "database", "db", "debug", "internal",
        "private", "secret", "tmp", "temp", "upload", "uploads",
        "manage", "management", "panel", "cpanel", "wp-admin",
        "phpmyadmin", "git", "svn", ".env", "credentials"
    ]

    # ---------------------------------------------------------------------------
    # HTTP helpers
    # ---------------------------------------------------------------------------
    def _fetch(self, url: str, timeout: int = 8) -> tuple:
        """GET url, return (status_code, text_or_none, bytes_or_none)."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; CcorvusCorax/0.8; Metadata)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                try:
                    text = raw.decode("utf-8", errors="replace")
                except Exception:
                    text = None
                return resp.status, text, raw
        except urllib.error.HTTPError as e:
            return e.code, None, None
        except Exception:
            return None, None, None

    # ---------------------------------------------------------------------------
    # Parsers
    # ---------------------------------------------------------------------------
    def _parse_robots(self, text: str) -> dict:
        disallowed = []
        allowed = []
        sitemaps = []
        sensitive = []

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path and path != "/":
                    disallowed.append(path)
                    # Check for sensitive paths
                    path_lower = path.lower()
                    for kw in self.SENSITIVE_KEYWORDS:
                        if kw in path_lower:
                            sensitive.append(path)
                            break
            elif lower.startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path and path != "/":
                    allowed.append(path)
            elif lower.startswith("sitemap:"):
                loc = line.split(":", 1)[1].strip()
                # Preserve full URL including http:
                full_loc = line[line.lower().index("sitemap:") + 8:].strip()
                if full_loc:
                    sitemaps.append(full_loc)

        return {
            "disallowed": list(dict.fromkeys(disallowed)),  # deduplicate
            "allowed": list(dict.fromkeys(allowed)),
            "sitemaps": list(dict.fromkeys(sitemaps)),
            "sensitive_paths": list(dict.fromkeys(sensitive)),
        }

    def _parse_sitemap(self, text: str) -> dict:
        urls = []
        try:
            # Strip namespace for simpler parsing
            text_clean = re.sub(r' xmlns[^"]*"[^"]*"', "", text)
            root = ET.fromstring(text_clean)
            # Handle both <urlset><url><loc> and <sitemapindex><sitemap><loc>
            for elem in root.iter():
                tag = elem.tag.lower().split("}")[-1]
                if tag == "loc" and elem.text:
                    urls.append(elem.text.strip())
        except Exception:
            # Fallback: regex extraction
            urls = re.findall(r"<loc>(.*?)</loc>", text, re.IGNORECASE)

        return {
            "total_urls": len(urls),
            "urls": urls[:50],  # cap at 50 for context size
        }

    def _parse_security_txt(self, text: str) -> dict:
        contacts = []
        pgp_keys = []
        policy = None
        acknowledgments = None
        expires = None

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lower = line.lower()
            if lower.startswith("contact:"):
                val = line.split(":", 1)[1].strip()
                contacts.append(val)
            elif lower.startswith("encryption:"):
                val = line.split(":", 1)[1].strip()
                pgp_keys.append(val)
            elif lower.startswith("policy:"):
                policy = line.split(":", 1)[1].strip()
            elif lower.startswith("acknowledgments:") or lower.startswith("acknowledgements:"):
                acknowledgments = line.split(":", 1)[1].strip()
            elif lower.startswith("expires:"):
                expires = line.split(":", 1)[1].strip()

        # Extract raw email addresses from contacts
        emails = []
        for c in contacts:
            if c.startswith("mailto:"):
                emails.append(c[7:])
            elif "@" in c and not c.startswith("http"):
                emails.append(c)

        return {
            "contacts": contacts,
            "emails": emails,
            "pgp_keys": pgp_keys,
            "policy": policy,
            "acknowledgments": acknowledgments,
            "expires": expires,
        }

    def _parse_humans_txt(self, text: str) -> dict:
        raw = text.strip()
        emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", raw)
        # Look for technology lines
        tech_lines = []
        for line in raw.splitlines():
            ll = line.lower()
            if any(kw in ll for kw in ["language:", "software:", "doctype:", "ide:", "standards:", "components:"]):
                tech_lines.append(line.strip())
        return {
            "raw": raw[:1000],      # cap size
            "emails": list(set(emails)),
            "tech_hints": tech_lines,
        }

    # ---------------------------------------------------------------------------
    # Main execute
    # ---------------------------------------------------------------------------
    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: metadata <url_or_host>")

        raw_target = args[0].strip()
        timeout = 8

        # Normalise to base URL
        if not raw_target.startswith("http"):
            base_url = f"https://{raw_target}"
        else:
            base_url = raw_target.rstrip("/")

        # Extract domain for context keying
        parsed = urllib.parse.urlparse(base_url)
        domain = parsed.netloc or raw_target

        inv = self.begin_investigation(
            f"Discover hidden administrative metadata, robots.txt & favicon hashes for {domain}",
            ["ENDPOINT DISCOVERY", "METADATA HARVESTING", "FAVICON HASH FINGERPRINTING"]
        )

        result_data = {
            "domain": domain,
            "base_url": base_url,
            "robots": None,
            "sitemap": None,
            "security_txt": None,
            "humans_txt": None,
            "favicon": None,
        }

        status, text = None, None
        with inv.phase(0):
            def harvest_metadata():
                nonlocal status, text
                status, text, _ = self._fetch(f"{base_url}/robots.txt", timeout)
                if status == 200 and text:
                    robots = self._parse_robots(text)
                    result_data["robots"] = robots
                    if robots["sensitive_paths"]:
                        self.analyst_log(f"Robots.txt exposes {len(robots['sensitive_paths'])} sensitive path(s) on {domain}")

            self.status_step(f"Probing /robots.txt, /sitemap.xml & /security.txt for {domain}", work=harvest_metadata)

        if status == 200 and text:
            robots = self._parse_robots(text)
            result_data["robots"] = robots
            if robots["sensitive_paths"]:
                for sp in robots["sensitive_paths"]:
                    self.add_note(
                        f"Sensitive path found in robots.txt for {domain}: {sp}",
                        severity="warning"
                    )
                self.add_relation(
                    src_type="domain", src_value=domain,
                    relation="exposes_sensitive_paths",
                    dst_type="file", dst_value="robots.txt",
                    evidence=f"{len(robots['sensitive_paths'])} sensitive path(s) found: {', '.join(robots['sensitive_paths'][:5])}"
                )
            self.add_note(
                f"robots.txt found for {domain}: {len(robots['disallowed'])} Disallow rules, "
                f"{len(robots['sitemaps'])} Sitemap(s)",
                severity="info"
            )
        else:
            self.add_note(f"robots.txt not found for {domain} (HTTP {status if status else 'N/A'})", severity="info")

        # ------------------------------------------------------------------
        # 2. sitemap.xml (also pick up URLs from robots if found)
        # ------------------------------------------------------------------
        sitemap_urls = []
        if result_data["robots"] and result_data["robots"]["sitemaps"]:
            sitemap_urls = result_data["robots"]["sitemaps"]
        else:
            sitemap_urls = [f"{base_url}/sitemap.xml"]

        sitemap_combined = {"total_urls": 0, "urls": []}
        for sm_url in sitemap_urls[:3]:  # try up to 3
            # Ensure full URL
            if sm_url.startswith("/"):
                sm_url = base_url + sm_url
            sm_status, sm_text, _ = self._fetch(sm_url, timeout)
            if sm_status == 200 and sm_text:
                parsed_sm = self._parse_sitemap(sm_text)
                sitemap_combined["total_urls"] += parsed_sm["total_urls"]
                sitemap_combined["urls"].extend(parsed_sm["urls"])
        if sitemap_combined["total_urls"] > 0:
            result_data["sitemap"] = sitemap_combined
            self.add_note(
                f"sitemap.xml found for {domain}: {sitemap_combined['total_urls']} URL(s) indexed",
                severity="info"
            )

        # ------------------------------------------------------------------
        # 3. security.txt
        # ------------------------------------------------------------------
        for sec_path in ["/.well-known/security.txt", "/security.txt"]:
            st_status, st_text, _ = self._fetch(f"{base_url}{sec_path}", timeout)
            if st_status == 200 and st_text and "contact:" in st_text.lower():
                sec = self._parse_security_txt(st_text)
                result_data["security_txt"] = sec
                # Register contacts as relations
                for email in sec["emails"]:
                    self.add_relation(
                        src_type="domain", src_value=domain,
                        relation="has_security_contact",
                        dst_type="email", dst_value=email,
                        evidence=f"Extracted from security.txt at {sec_path}"
                    )
                    self.add_note(
                        f"Security contact found in security.txt: {email}",
                        severity="info"
                    )
                if sec["policy"]:
                    self.add_note(
                        f"Security policy URL for {domain}: {sec['policy']}",
                        severity="info"
                    )
                break
        else:
            self.add_note(f"security.txt not found for {domain}", severity="info")

        # ------------------------------------------------------------------
        # 4. humans.txt
        # ------------------------------------------------------------------
        h_status, h_text, _ = self._fetch(f"{base_url}/humans.txt", timeout)
        if h_status == 200 and h_text:
            humans = self._parse_humans_txt(h_text)
            result_data["humans_txt"] = humans
            self.add_note(
                f"humans.txt found for {domain}: {len(humans['emails'])} email(s), "
                f"{len(humans['tech_hints'])} technology hint(s)",
                severity="info"
            )
            for email in humans["emails"]:
                self.add_relation(
                    src_type="domain", src_value=domain,
                    relation="has_staff_email",
                    dst_type="email", dst_value=email,
                    evidence="Extracted from humans.txt"
                )
        else:
            self.add_note(f"humans.txt not found for {domain}", severity="info")

        # ------------------------------------------------------------------
        # 5. favicon.ico — Shodan hash
        # ------------------------------------------------------------------
        # First try to find the favicon path from HTML (crude approach)
        fav_path = "/favicon.ico"
        fav_url = f"{base_url}{fav_path}"
        fav_status, _, fav_bytes = self._fetch(fav_url, timeout)

        favicon_data = None
        if fav_status == 200 and fav_bytes:
            fhash = _favicon_hash(fav_bytes)
            fmd5 = hashlib.md5(fav_bytes).hexdigest()
            fsha1 = hashlib.sha1(fav_bytes).hexdigest()
            favicon_data = {
                "url": fav_url,
                "size_bytes": len(fav_bytes),
                "md5": fmd5,
                "sha1": fsha1,
                "shodan_hash": fhash,
                "shodan_query": f"http.favicon.hash:{fhash}",
            }
            result_data["favicon"] = favicon_data

            self.add_note(
                f"Favicon collected from {domain}: Shodan hash = {fhash}",
                severity="info"
            )
            self.add_note(
                f"Shodan pivot query: http.favicon.hash:{fhash}",
                severity="info"
            )
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="has_favicon_hash",
                dst_type="favicon_hash", dst_value=str(fhash),
                evidence=f"MurmurHash3 of base64-encoded favicon bytes from {fav_url}"
            )
        else:
            self.add_note(f"favicon.ico not found for {domain} (HTTP {fav_status})", severity="info")

        # ------------------------------------------------------------------
        # 6. Save to context
        # ------------------------------------------------------------------
        if self.context:
            self.context.add_metadata_intel(domain, result_data)

        return self.success(target=domain, data=result_data)
