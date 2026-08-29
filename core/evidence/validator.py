"""Corvus Corax Evidence Validator.

Kanıtların sentaks, format ve mantıksal doğrulamasını yapar.
"""
import re


class EvidenceValidator:
    """Kanıt doğrulama ve geçerlilik motoru."""

    IP_REGEX = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    DOMAIN_REGEX = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    @staticmethod
    def validate_evidence(evidence) -> str:
        """
        Bir kanıtın geçerliliğini denetler ve yeni durum kodunu döndürür:
        - VALIDATED
        - SYNTAX_ERROR
        - UNVERIFIABLE
        - EXPIRED
        """
        ev_type = evidence.evidence_type
        val = str(evidence.observed_value).strip()

        if not val:
            evidence.status = "SYNTAX_ERROR"
            evidence.confidence = 0.1
            return "SYNTAX_ERROR"

        # IP doğrulaması
        if ev_type in ("ip_resolution", "resolves_to", "ip"):
            if " ==[" in val:
                ip_part = val.split("==>")[-1].strip()
                if EvidenceValidator.IP_REGEX.match(ip_part):
                    evidence.status = "VALIDATED"
                    return "VALIDATED"
            elif EvidenceValidator.IP_REGEX.match(val):
                evidence.status = "VALIDATED"
                return "VALIDATED"

        # Domain doğrulaması
        if ev_type in ("domain", "subdomain", "has_subdomain"):
            if EvidenceValidator.DOMAIN_REGEX.match(val):
                evidence.status = "VALIDATED"
                return "VALIDATED"

        # E-posta doğrulaması
        if ev_type in ("email", "has_email", "email_pattern"):
            if "@" in val and EvidenceValidator.EMAIL_REGEX.match(val):
                evidence.status = "VALIDATED"
                return "VALIDATED"

        # Varsayılan kontrol
        if evidence.confidence >= 0.5:
            evidence.status = "VALIDATED"
        else:
            evidence.status = "UNVERIFIABLE"

        return evidence.status
