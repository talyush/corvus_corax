import ssl
import socket
import hashlib
import datetime
from core.module_base import BaseModule


class CertIntelModule(BaseModule):
    """
    Corvus Corax v0.8 — Certificate Intelligence Module.
    Fetches and deeply analyzes TLS certificates, extracting structured
    intelligence for use in Nexus correlation (shared/wildcard cert detection).
    """
    name = "cert"

    def _fetch_cert(self, host, port, timeout):
        """Opens one TLS connection and returns (der_bytes, cert_dict).
        Uses check_hostname=False but CERT_OPTIONAL so we get the full decoded
        certificate even for self-signed or mismatched hosts.
        """
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_OPTIONAL
        raw_sock = socket.create_connection((host, port), timeout=timeout)
        conn = ctx.wrap_socket(raw_sock, server_hostname=host)
        der_bytes = conn.getpeercert(binary_form=True)
        cert_dict = conn.getpeercert(binary_form=False)
        conn.close()
        # Fallback: if verify failed, cert_dict may be empty — still return der_bytes
        return der_bytes, cert_dict or {}


    def _parse_rdns(self, rdns_list, field):
        """Extracts a specific field (like 'CN', 'O', 'C') from an RDN list."""
        for rdn in rdns_list:
            for key, val in rdn:
                if key == field:
                    return val
        return None

    def _parse_san(self, cert_dict):
        """Parses Subject Alternative Names from cert dict."""
        san_list = []
        for ext_key, ext_val in cert_dict.get("subjectAltName", []):
            if ext_key == "DNS":
                san_list.append(ext_val.lower())
        return san_list

    def _detect_wildcards(self, san_list):
        """Returns list of wildcard SANs."""
        return [s for s in san_list if s.startswith("*.")]

    def _parse_date(self, date_str):
        """Parse the SSL cert date string into a datetime object."""
        # Python's ssl returns dates like: 'May 15 12:00:00 2025 GMT'
        try:
            return datetime.datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=datetime.timezone.utc
            )
        except ValueError:
            return None

    def _fingerprint_sha256(self, der_cert):
        """Computes the SHA-256 fingerprint of the raw DER cert."""
        digest = hashlib.sha256(der_cert).hexdigest()
        # Format as colon-separated pairs (e.g. AA:BB:CC:...)
        return ":".join(digest[i:i+2].upper() for i in range(0, len(digest), 2))

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: cert <host> [port]")

        host = args[0].strip().lower()
        port = int(args[1]) if len(args) > 1 else 443

        config_timeout = float(self.config.get("timeout", 8.0)) if self.config else 8.0
        timeout = max(config_timeout, 5.0)

        inv = self.begin_investigation(
            f"Analyze TLS X.509 certificate & SAN extension footprint for {host}:{port}",
            ["HANDSHAKE & FETCH", "X509 PARSING", "IDENTITY & EXPIRY ANALYSIS"]
        )

        der_cert, cert_dict = None, {}
        with inv.phase(0):
            def fetch_der():
                nonlocal der_cert, cert_dict
                der_cert, cert_dict = self._fetch_cert(host, port, timeout)

            try:
                self.status_step(f"Establishing TLS socket connection to {host}:{port}", work=fetch_der)
            except ssl.SSLError as e:
                return self.error(f"SSL error: {e}", target=host)
            except socket.timeout:
                return self.error(f"Connection timed out to {host}:{port}", target=host)
            except ConnectionRefusedError:
                return self.error(f"Connection refused to {host}:{port}", target=host)
            except Exception as e:
                return self.error(f"Failed to fetch certificate: {e}", target=host)

        with inv.phase(1):
            self.status_step("Computing SHA-256 fingerprint & SAN extensions")

        # --- Parse fields ---
        subject = cert_dict.get("subject", ())
        issuer = cert_dict.get("issuer", ())

        subject_cn   = self._parse_rdns(subject, "commonName")
        organization = self._parse_rdns(subject, "organizationName")
        country      = self._parse_rdns(subject, "countryName")
        issuer_cn    = self._parse_rdns(issuer, "commonName")
        issuer_org   = self._parse_rdns(issuer, "organizationName")

        san_list      = self._parse_san(cert_dict)
        wildcards     = self._detect_wildcards(san_list)
        is_wildcard   = len(wildcards) > 0

        valid_from_str = cert_dict.get("notBefore", "")
        valid_to_str   = cert_dict.get("notAfter", "")

        valid_from_dt  = self._parse_date(valid_from_str)
        valid_to_dt    = self._parse_date(valid_to_str)
        now_utc        = datetime.datetime.now(datetime.timezone.utc)

        expired       = bool(valid_to_dt and valid_to_dt < now_utc)
        days_remaining = (
            (valid_to_dt - now_utc).days
            if (valid_to_dt and not expired)
            else 0
        )

        serial_number = str(cert_dict.get("serialNumber", "N/A"))
        fingerprint   = self._fingerprint_sha256(der_cert)

        issuer_display = issuer_cn or issuer_org or "Unknown"
        valid_to_iso   = valid_to_dt.strftime("%Y-%m-%d") if valid_to_dt else "N/A"
        valid_from_iso = valid_from_dt.strftime("%Y-%m-%d") if valid_from_dt else "N/A"

        # --- Intelligence Notes ---
        if expired:
            self.add_note(
                f"CERT EXPIRED: Certificate for {host} expired on {valid_to_iso}.",
                severity="critical"
            )
        elif days_remaining < 30:
            self.add_note(
                f"CERT NEAR EXPIRY: Certificate for {host} expires in {days_remaining} days ({valid_to_iso}).",
                severity="warning"
            )
        else:
            self.add_note(
                f"Certificate for {host} is valid until {valid_to_iso} ({days_remaining} days remaining).",
                severity="info"
            )

        if is_wildcard:
            self.add_note(
                f"Wildcard certificate detected for {host}: {', '.join(wildcards)}",
                severity="info"
            )

        # --- Relations ---
        # cert fingerprint -> host
        self.add_relation(
            src_type="certificate",
            src_value=fingerprint,
            relation="issued_to",
            dst_type="host",
            dst_value=host,
            evidence=f"TLS certificate fetched from {host}:{port}"
        )

        # host -> issuer (CA)
        self.add_relation(
            src_type="host",
            src_value=host,
            relation="cert_issued_by",
            dst_type="issuer",
            dst_value=issuer_display,
            evidence=f"Certificate issuer from TLS handshake"
        )

        # wildcard relations
        for wc in wildcards:
            self.add_relation(
                src_type="certificate",
                src_value=fingerprint,
                relation="wildcard_covers",
                dst_type="wildcard",
                dst_value=wc,
                evidence=f"Wildcard SAN found in certificate for {host}"
            )

        # --- Push to Context (certificates store) ---
        if self.context:
            self.context.add_certificate(
                host=host,
                fingerprint=fingerprint,
                cert_data={
                    "fingerprint":     fingerprint,
                    "subject_cn":      subject_cn,
                    "organization":    organization,
                    "country":         country,
                    "issuer":          issuer_display,
                    "san":             san_list,
                    "wildcards":       wildcards,
                    "wildcard":        is_wildcard,
                    "expired":         expired,
                    "days_remaining":  days_remaining,
                    "valid_from":      valid_from_iso,
                    "valid_to":        valid_to_iso,
                    "serial_number":   serial_number,
                }
            )

        return self.success(
            target=host,
            data={
                "host":            host,
                "port":            port,
                "subject_cn":      subject_cn,
                "organization":    organization,
                "country":         country,
                "issuer":          issuer_display,
                "san":             san_list,
                "wildcards":       wildcards,
                "wildcard":        is_wildcard,
                "expired":         expired,
                "days_remaining":  days_remaining,
                "valid_from":      valid_from_iso,
                "valid_to":        valid_to_iso,
                "serial_number":   serial_number,
                "fingerprint":     fingerprint,
            }
        )
