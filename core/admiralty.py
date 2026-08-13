"""
Corvus Corax v0.8 — NATO Admiralty Intelligence Scoring System

This module implements the NATO Admiralty Code system for intelligence confidence scoring.
The system evaluates both source reliability (A-F) and information reliability (1-6) to produce
a standardized confidence percentage.

Admiralty Code Format: [Source][Information] (e.g., A1, B2, C3)
- Source Reliability (A-F): How trustworthy the data source is
- Information Reliability (1-6): How likely the information is to be accurate

Combined with evidence weights, this produces a 0-100 confidence score.
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional

from core.config import load_rules


class SourceReliability(Enum):
    """NATO Source Reliability Classification (A-F)"""
    A = "Completely Reliable"  # 1.0
    B = "Usually Reliable"    # 0.8
    C = "Fairly Reliable"     # 0.6
    D = "Not Usually Reliable" # 0.4
    E = "Unreliable"          # 0.2
    F = "Reliability Cannot Be Judged" # 0.1


class InformationReliability(Enum):
    """NATO Information Reliability Classification (1-6)"""
    CONFIRMED = "1"      # 1.0 - Confirmed by other sources
    PROBABLE = "2"        # 0.9 - Good source
    POSSIBLY_TRUE = "3"   # 0.7 - Possibly true
    DOUBTFUL = "4"        # 0.5 - Doubtful
    IMPROBABLE = "5"      # 0.3 - Improbable
    UNVERIFIABLE = "6"    # 0.1 - Cannot be verified


class EvidenceType(Enum):
    """Evidence types with base weights — ağırlıklar config/rules.json'dan okunur."""
    CERTIFICATE_MATCH = 40
    SHARED_FAVICON = 25
    SAME_TECH_STACK = 20
    SAME_ASN = 15
    SAME_PROVIDER = 15
    SAME_EMAIL_PATTERN = 15
    SHARED_SUBNET = 10
    DNS_RECORD_MATCH = 10
    HTTP_HEADER_MATCH = 8
    COOKIE_PATTERN = 5
    PATH_PATTERN = 5
    METADATA_MATCH = 5
    # --- v0.9: İnsan/Otganizasyon Varlık Kanıtları ---
    PHONE_VERIFIED = 30         # Telefon doğrulandı (WhatsApp/Telegram/operatör tespiti)
    BREACH_CORRELATION = 25     # Aynı email/şifre breach veritabanında ortak
    SOCIAL_PROFILE_MATCH = 20   # Aynı kullanıcı adı birden çok platformda
    PERSON_EMAIL_MATCH = 15     # Kişi-email eşleşmesi
    ORG_REGISTRY_MATCH = 18     # Resmi şirket kaydı doğrulaması
    ACADEMIC_AFFILIATION = 12   # Akademik kurum bağlantısı
    LOCATION_CORRELATION = 14   # Konum tabanlı korelasyon
    FINANCIAL_TRACE = 10        # Finansal iz (kripto cüzdan vb.)
    PERSONAL_DATA_CORRELATION = 8  # Kişisel veri çapraz doğrulama

    @classmethod
    def from_rules(cls):
        """
        Evidence ağırlıklarını config/rules.json'dan yükleyerek
        Enum değerlerini dinamik olarak günceller.
        Farklı kurallar/config profilleri için doğrusal ağırlık eşlemesi.
        """
        rules = load_rules()
        weights = rules.get("evidence_weights", {})
        mapping = {
            "certificate_match": "CERTIFICATE_MATCH",
            "shared_favicon": "SHARED_FAVICON",
            "same_tech_stack": "SAME_TECH_STACK",
            "same_asn": "SAME_ASN",
            "same_provider": "SAME_PROVIDER",
            "same_email_pattern": "SAME_EMAIL_PATTERN",
            "shared_subnet": "SHARED_SUBNET",
            "dns_record_match": "DNS_RECORD_MATCH",
            "http_header_match": "HTTP_HEADER_MATCH",
            "cookie_pattern": "COOKIE_PATTERN",
            "path_pattern": "PATH_PATTERN",
            "metadata_match": "METADATA_MATCH",
            "phone_verified": "PHONE_VERIFIED",
            "breach_correlation": "BREACH_CORRELATION",
            "social_profile_match": "SOCIAL_PROFILE_MATCH",
            "person_email_match": "PERSON_EMAIL_MATCH",
            "org_registry_match": "ORG_REGISTRY_MATCH",
            "academic_affiliation": "ACADEMIC_AFFILIATION",
            "location_correlation": "LOCATION_CORRELATION",
            "financial_trace": "FINANCIAL_TRACE",
            "personal_data_correlation": "PERSONAL_DATA_CORRELATION",
        }
        for rule_key, enum_name in mapping.items():
            if rule_key in weights and hasattr(cls, enum_name):
                setattr(cls, enum_name, int(weights[rule_key]))
        return cls


class AdmiraltyScorer:
    """
    NATO Admiralty Code implementation for intelligence confidence scoring.
    
    Combines evidence weights with source/information reliability to produce
    standardized confidence scores (0-100).
    """
    
    # Source reliability numeric values
    SOURCE_VALUES = {
        SourceReliability.A: 1.0,
        SourceReliability.B: 0.8,
        SourceReliability.C: 0.6,
        SourceReliability.D: 0.4,
        SourceReliability.E: 0.2,
        SourceReliability.F: 0.1,
    }
    
    # Information reliability numeric values
    INFO_VALUES = {
        InformationReliability.CONFIRMED: 1.0,
        InformationReliability.PROBABLE: 0.9,
        InformationReliability.POSSIBLY_TRUE: 0.7,
        InformationReliability.DOUBTFUL: 0.5,
        InformationReliability.IMPROBABLE: 0.3,
        InformationReliability.UNVERIFIABLE: 0.1,
    }
    
    # Source reliability by data source type — config/rules.json'dan yüklenir
    # Kaynak eşlemesi: rules["source_reliability"] dict'i.
    _RULES_SOURCE_RELIABILITY = None

    @classmethod
    def _get_rules_source_reliability(cls):
        """Kaynak güvenilirlik eşlemesini config/rules.json'dan yükler (cache'lenmiş)."""
        if cls._RULES_SOURCE_RELIABILITY is None:
            rules = load_rules()
            cls._RULES_SOURCE_RELIABILITY = rules.get("source_reliability", {})
        return cls._RULES_SOURCE_RELIABILITY

    # Default source reliability by data source type (fallback — rules.json tercih edilir)
    DEFAULT_SOURCE_RELIABILITY = {
        "cert_intel": SourceReliability.A,      # Certificate data is cryptographically verified
        "asn": SourceReliability.A,
        "dns": SourceReliability.A,
        "scan": SourceReliability.A,
        "geoip": SourceReliability.B,
        "tech": SourceReliability.B,
        "http_headers": SourceReliability.B,
        "subdomain": SourceReliability.B,
        "phone_intel": SourceReliability.B,
        "academic_intel": SourceReliability.B,
        "org_intel": SourceReliability.B,
        "geo_intel": SourceReliability.B,
        "metadata": SourceReliability.C,
        "email": SourceReliability.C,
        "whois": SourceReliability.C,
        "social_intel": SourceReliability.C,
        "breach_intel": SourceReliability.C,
        "financial_intel": SourceReliability.D,
        "person": SourceReliability.D,
    }
    
    def __init__(self):
        self.evidence_chain: List[Dict] = []
    
    def add_evidence(self, 
                     evidence_type: EvidenceType,
                     source: str,
                     info_reliability: InformationReliability = InformationReliability.PROBABLE,
                     source_reliability: Optional[SourceReliability] = None,
                     description: str = ""):
        """
        Add evidence to the scoring chain.
        
        Args:
            evidence_type: Type of evidence (with base weight)
            source: Data source (e.g., 'cert_intel', 'asn', 'dns')
            info_reliability: Information reliability level
            source_reliability: Override default source reliability
            description: Human-readable description
        """
        # Use default source reliability if not specified
        if source_reliability is None:
            # Önce rules.json'dan, sonra fallback olarak DEFAULT_SOURCE_RELIABILITY'dan
            rules_src = self._get_rules_source_reliability().get(source)
            if rules_src:
                source_reliability = SourceReliability(rules_src)
            else:
                source_reliability = self.DEFAULT_SOURCE_RELIABILITY.get(
                    source, SourceReliability.C
                )
        
        # Calculate weighted score
        base_weight = evidence_type.value
        source_factor = self.SOURCE_VALUES[source_reliability]
        info_factor = self.INFO_VALUES[info_reliability]
        
        # Admiralty formula: weight × source_reliability × info_reliability
        weighted_score = base_weight * source_factor * info_factor
        
        evidence = {
            "type": evidence_type.name,
            "source": source,
            "source_reliability": source_reliability.value,
            "info_reliability": info_reliability.value,
            "admiralty_code": f"{source_reliability.name}{info_reliability.value}",
            "base_weight": base_weight,
            "weighted_score": round(weighted_score, 2),
            "description": description,
        }
        
        self.evidence_chain.append(evidence)
        return evidence
    
    def calculate_confidence(self) -> Dict:
        """
        Calculate overall confidence score from evidence chain.
        
        Returns:
            Dict with:
                - total_score: 0-100 (sum of weighted evidence)
                - confidence_percentage: 0-100 (normalized score)
                - admiralty_rating: Overall admiralty classification
                - evidence_count: Number of evidence items
                - evidence_chain: Full evidence details
        """
        if not self.evidence_chain:
            return {
                "total_score": 0,
                "confidence_percentage": 0,
                "admiralty_rating": "F6",
                "evidence_count": 0,
                "evidence_chain": []
            }
        
        # Sum weighted scores (max theoretical is ~300 with all evidence types)
        total_score = sum(e["weighted_score"] for e in self.evidence_chain)
        
        # Normalize to 0-100 (assuming max reasonable score is ~100)
        confidence_percentage = min(round(total_score), 100)
        
        # Determine overall admiralty rating
        admiralty_rating = self._get_admiralty_rating(confidence_percentage)
        
        return {
            "total_score": round(total_score, 2),
            "confidence_percentage": confidence_percentage,
            "admiralty_rating": admiralty_rating,
            "evidence_count": len(self.evidence_chain),
            "evidence_chain": self.evidence_chain
        }
    
    def _get_admiralty_rating(self, confidence: int) -> str:
        """Convert confidence percentage to admiralty code."""
        if confidence >= 90:
            return "A1"  # Completely reliable, confirmed
        elif confidence >= 75:
            return "B2"  # Usually reliable, probable
        elif confidence >= 60:
            return "C3"  # Fairly reliable, possibly true
        elif confidence >= 40:
            return "D4"  # Not usually reliable, doubtful
        elif confidence >= 20:
            return "E5"  # Unreliable, improbable
        else:
            return "F6"  # Cannot judge, unverifiable
    
    def reset(self):
        """Clear evidence chain for new calculation."""
        self.evidence_chain = []
    
    def get_evidence_summary(self) -> str:
        """Get human-readable summary of evidence chain."""
        if not self.evidence_chain:
            return "No evidence collected."
        
        lines = ["Evidence Chain:"]
        for i, ev in enumerate(self.evidence_chain, 1):
            lines.append(
                f"  {i}. {ev['type']} ({ev['admiralty_code']}) - "
                f"+{ev['weighted_score']} points - {ev['description']}"
            )
        
        result = self.calculate_confidence()
        lines.append(f"\nTotal Score: {result['total_score']}/100")
        lines.append(f"Confidence: {result['confidence_percentage']}%")
        lines.append(f"Admiralty Rating: {result['admiralty_rating']}")
        
        return "\n".join(lines)


# Convenience functions for common evidence patterns
def score_certificate_match(source: str = "cert_intel", description: str = "Certificate fingerprint match") -> float:
    """Quick scoring for certificate match evidence."""
    scorer = AdmiraltyScorer()
    scorer.add_evidence(
        EvidenceType.CERTIFICATE_MATCH,
        source,
        InformationReliability.CONFIRMED,
        description=description
    )
    return scorer.calculate_confidence()["weighted_score"]


def score_shared_favicon(source: str = "metadata", description: str = "Shared favicon hash") -> float:
    """Quick scoring for shared favicon evidence."""
    scorer = AdmiraltyScorer()
    scorer.add_evidence(
        EvidenceType.SHARED_FAVICON,
        source,
        InformationReliability.PROBABLE,
        description=description
    )
    return scorer.calculate_confidence()["weighted_score"]


def score_same_tech_stack(source: str = "tech", description: str = "Identical technology stack") -> float:
    """Quick scoring for shared tech stack evidence."""
    scorer = AdmiraltyScorer()
    scorer.add_evidence(
        EvidenceType.SAME_TECH_STACK,
        source,
        InformationReliability.PROBABLE,
        description=description
    )
    return scorer.calculate_confidence()["weighted_score"]


def score_same_asn(source: str = "asn", description: str = "Shared ASN/network block") -> float:
    """Quick scoring for shared ASN evidence."""
    scorer = AdmiraltyScorer()
    scorer.add_evidence(
        EvidenceType.SAME_ASN,
        source,
        InformationReliability.CONFIRMED,
        description=description
    )
    return scorer.calculate_confidence()["weighted_score"]
