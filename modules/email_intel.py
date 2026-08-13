import re
from core.module_base import BaseModule


class EmailIntelModule(BaseModule):
    """
    Corvus Corax v0.8 — Email Pattern Discovery Module.

    Reads DNS context (MX, SPF, DMARC) to identify the email provider,
    extracts reporting addresses from DMARC records, detects email naming
    conventions from sample addresses, distinguishes role-based system mailboxes
    from personal emails, and generates likely email formats for the target domain.
    """
    name = "email"

    # ---------------------------------------------------------------
    # Provider fingerprints (SPF includes & MX host substrings)
    # ---------------------------------------------------------------
    PROVIDER_SPF_MAP = [
        ("_spf.google.com",            "Google Workspace"),
        ("_spf.googlemail.com",         "Google Workspace"),
        ("spf.protection.outlook.com",  "Microsoft 365"),
        ("mail.protection.outlook.com", "Microsoft 365"),
        ("spf.mandrillapp.com",         "Mandrill (Mailchimp)"),
        ("servers.mcsv.net",            "Mailchimp"),
        ("sendgrid.net",                "SendGrid"),
        ("amazonses.com",               "Amazon SES"),
        ("mailgun.org",                 "Mailgun"),
        ("_spf.salesforce.com",         "Salesforce"),
        ("mimecast.com",                "Mimecast"),
        ("pphosted.com",                "Proofpoint"),
        ("proofpoint.com",              "Proofpoint"),
        ("zoho.com",                    "Zoho Mail"),
    ]

    PROVIDER_MX_MAP = [
        ("google.com",              "Google Workspace"),
        ("googlemail.com",          "Google Workspace"),
        ("outlook.com",             "Microsoft 365"),
        ("protection.outlook.com",  "Microsoft 365"),
        ("mimecast.com",            "Mimecast"),
        ("pphosted.com",            "Proofpoint"),
        ("proofpoint.com",          "Proofpoint"),
        ("mailgun.org",             "Mailgun"),
        ("sendgrid.net",            "SendGrid"),
        ("amazonses.com",           "Amazon SES"),
        ("zoho.com",                "Zoho Mail"),
    ]

    ROLE_ALIASES = [
        "support", "security", "admin", "info", "contact", "sales", "jobs", "hr", 
        "billing", "marketing", "webmaster", "noc", "abuse", "postmaster", "hostmaster",
        "mailauth-reports", "dmarc-forensics", "dmarc", "noreply", "no-reply", "office",
        "staff", "hello", "team", "privacy", "legal", "invoice", "helpdesk"
    ]

    # ---------------------------------------------------------------
    # Role / System Mailbox identification
    # ---------------------------------------------------------------
    def _is_role_email(self, email):
        """Returns True if the email local-part matches a common role or system alias."""
        local = email.split("@")[0].lower()
        if local in self.ROLE_ALIASES:
            return True
        for role in self.ROLE_ALIASES:
            if local.startswith(role + "-") or local.startswith(role + "."):
                return True
        return False

    # ---------------------------------------------------------------
    # Email pattern detection helpers
    # ---------------------------------------------------------------
    def _detect_pattern(self, email, domain):
        """Given a full email address, determine the naming pattern."""
        local = email.split("@")[0].lower()

        # Check delimiters
        for delim in [".", "_", "-"]:
            if delim in local:
                parts = local.split(delim, 1)
                p1, p2 = parts[0], parts[1]
                if len(p1) == 1 and len(p2) == 1:
                    return f"{{fi}}{delim}{{li}}", 0.90  # j_d
                if len(p1) == 1:
                    return f"{{fi}}{delim}{{last}}", 0.95  # j.doe
                if len(p2) == 1:
                    return f"{{first}}{delim}{{li}}", 0.95  # john.d
                
                # Default delimiter match
                return f"{{first}}{delim}{{last}}", 0.95

        # No delimiter
        if len(local) == 2:
            return "{fi}{li}", 0.80  # jd
        if len(local) <= 5:
            return "{fi}{last}", 0.85  # jdoe
        if len(local) >= 8:
            return "{first}{last}", 0.70  # johndoe
            
        return "{first}", 0.60  # john

    def _generate_formats(self, pattern, domain, confidence_label):
        """Build a list of likely email format suggestions."""
        templates = [
            ("{first}.{last}",   "first.last@domain"),
            ("{fi}.{last}",      "fi.last@domain"),
            ("{fi}{last}",       "filast@domain"),
            ("{first}{li}",      "firstli@domain"),
            ("{first}",          "first@domain"),
            ("{last}",           "last@domain"),
            ("{last}.{first}",   "last.first@domain"),
            ("{first}_{last}",   "first_last@domain"),
            ("{fi}_{last}",      "fi_last@domain"),
            ("{first}-{last}",   "first-last@domain"),
            ("{fi}-{last}",      "fi-last@domain"),
            ("{first}{last}",    "firstlast@domain"),
        ]

        # Scoring logic based on matching delimiters
        delim = None
        for d in [".", "_", "-"]:
            if d in pattern:
                delim = d
                break

        result = []
        for tmpl, example in templates:
            if tmpl == pattern:
                conf = "HIGH"
            elif delim and delim in tmpl:
                conf = "MEDIUM"
            elif not delim and ("." not in tmpl and "_" not in tmpl and "-" not in tmpl):
                conf = "MEDIUM"
            else:
                conf = "LOW"
            result.append({
                "format": f"{tmpl}@{domain}",
                "example": f"john.doe -> {example.replace('domain', domain)}",
                "confidence": conf,
            })

        # Sort by confidence
        conf_weight = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        result.sort(key=lambda x: conf_weight[x["confidence"]])
        return result

    # ---------------------------------------------------------------
    # DMARC email extraction
    # ---------------------------------------------------------------
    def _extract_dmarc_emails(self, dmarc_record):
        """Pull rua= and ruf= mailto: addresses from a DMARC record."""
        emails = []
        if not dmarc_record:
            return emails
        for match in re.finditer(r'mailto:([^\s,;!]+)', dmarc_record, re.IGNORECASE):
            addr = match.group(1).strip()
            if "@" in addr:
                emails.append(addr)
        return emails

    # ---------------------------------------------------------------
    # Provider detection
    # ---------------------------------------------------------------
    def _detect_provider(self, spf_record, mx_records):
        """Return (provider_name, evidence_string) or (None, None)."""
        if spf_record:
            spf_lower = spf_record.lower()
            for needle, name in self.PROVIDER_SPF_MAP:
                if needle in spf_lower:
                    return name, f"SPF record includes '{needle}'"

        for mx in mx_records:
            host = mx.get("host", "").lower() if isinstance(mx, dict) else mx.lower()
            for needle, name in self.PROVIDER_MX_MAP:
                if needle in host:
                    return name, f"MX host '{host}' matches '{needle}'"

        return None, None

    # ---------------------------------------------------------------
    # Main execute
    # ---------------------------------------------------------------
    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: email <domain> [sample1@domain,sample2@domain]")

        domain = args[0].strip().lower()

        inv = self.begin_investigation(
            f"Analyze corporate email infrastructure, forensic contacts & address patterns for {domain}",
            ["DNS CONTEXT RECON", "FORENSIC CONTACT EXTRACTION", "PATTERN DEDUCTION"]
        )

        with inv.phase(0):
            self.status_step(f"Retrieving DNS context & prior relation graph for {domain}")

        # Optional: user-supplied sample email addresses
        sample_emails = []
        if len(args) > 1:
            for raw in args[1].split(","):
                raw = raw.strip().lower()
                if "@" in raw and raw.endswith(f"@{domain}"):
                    sample_emails.append(raw)

        # ------------------------------------------------------------------
        # 1. Pull DNS context & existing emails in context relations
        # ------------------------------------------------------------------
        dns_data = {}
        existing_emails = set()
        if self.context:
            dns_data = self.context.data.get("dns_records", {}).get(domain, {})
            for rel in self.context.data.get("relations", []):
                if isinstance(rel, dict):
                    dst = rel.get("dst", {})
                    if isinstance(dst, dict) and dst.get("type") == "email":
                        val = str(dst.get("value", "")).lower()
                        if val.endswith(f"@{domain}"):
                            existing_emails.add(val)

        spf_record   = dns_data.get("spf")
        dmarc_record = dns_data.get("dmarc")
        mx_records   = dns_data.get("MX", [])

        # ------------------------------------------------------------------
        # 2. Provider detection
        # ------------------------------------------------------------------
        provider, provider_evidence = self._detect_provider(spf_record, mx_records)

        if provider:
            self.add_note(
                f"Email provider identified for {domain}: {provider} ({provider_evidence})",
                severity="info"
            )
        else:
            self.add_note(
                f"Could not identify email provider for {domain}. Run 'dns' first.",
                severity="warning"
            )

        # ------------------------------------------------------------------
        # 3. DMARC reporting email extraction
        # ------------------------------------------------------------------
        report_emails = self._extract_dmarc_emails(dmarc_record)

        # ------------------------------------------------------------------
        # 4. Categorize all unique emails into Role-based & Personal
        # ------------------------------------------------------------------
        all_emails = set(sample_emails)
        all_emails.update(report_emails)
        all_emails.update(existing_emails)

        role_emails = []
        personal_emails = []
        for email in sorted(all_emails):
            if self._is_role_email(email):
                role_emails.append(email)
            else:
                personal_emails.append(email)

        # Log notes for role emails
        for email in role_emails:
            self.add_note(
                f"Identified role-based/system email contact: {email}",
                severity="info"
            )

        # ------------------------------------------------------------------
        # 5. Pattern detection from personal emails
        # ------------------------------------------------------------------
        detected_pattern = None
        pattern_confidence = None
        if personal_emails:
            patterns = [self._detect_pattern(e, domain) for e in personal_emails]
            from collections import Counter
            pat_names = [pat for pat, _ in patterns]
            most_common, _ = Counter(pat_names).most_common(1)[0]
            detected_pattern = most_common
            
            matching_confs = [c for pat, c in patterns if pat == most_common]
            pattern_confidence = round(
                sum(matching_confs) / max(len(matching_confs), 1),
                2
            )
            self.add_note(
                f"Email naming pattern detected for {domain}: "
                f"{detected_pattern} (confidence: {pattern_confidence})",
                severity="info"
            )
        else:
            detected_pattern = "{first}.{last}"
            pattern_confidence = 0.5
            self.add_note(
                f"No personal sample emails found - defaulting to common pattern "
                f"{detected_pattern} for {domain}",
                severity="info"
            )

        # ------------------------------------------------------------------
        # 6. Build suggested formats
        # ------------------------------------------------------------------
        conf_label = "high" if pattern_confidence >= 0.85 else "medium" if pattern_confidence >= 0.6 else "low"
        suggested_formats = self._generate_formats(detected_pattern, domain, conf_label)

        # ------------------------------------------------------------------
        # 7. Relations -> Context Intelligence Graph
        # ------------------------------------------------------------------
        if provider:
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="uses_email_provider",
                dst_type="provider", dst_value=provider,
                evidence=provider_evidence
            )

        self.add_relation(
            src_type="domain", src_value=domain,
            relation="email_pattern",
            dst_type="pattern", dst_value=detected_pattern,
            evidence=f"Detected from {len(personal_emails)} personal address(es)" if personal_emails else "Default assumption"
        )

        for email in role_emails:
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="role_email_associated_with",
                dst_type="email", dst_value=email,
                evidence="Role-based/system mailbox alias detected — candidate association, not confirmed ownership",
                confidence=0.5
            )

        for email in personal_emails:
            self.add_relation(
                src_type="domain", src_value=domain,
                relation="email_associated_with",
                dst_type="email", dst_value=email,
                evidence="Personal contact mailbox alias identified — candidate association, not confirmed ownership",
                confidence=0.3
            )

        # ------------------------------------------------------------------
        # 8. Save structured data to Context
        # ------------------------------------------------------------------
        email_data = {
            "domain": domain,
            "provider": provider,
            "provider_evidence": provider_evidence,
            "spf_used": spf_record,
            "dmarc_report_emails": report_emails,
            "role_emails": role_emails,
            "personal_emails": personal_emails,
            "detected_pattern": detected_pattern,
            "pattern_confidence": pattern_confidence,
            "suggested_formats": suggested_formats,
        }

        if self.context:
            self.context.add_email_intel(domain, email_data)

        return self.success(target=domain, data=email_data)
