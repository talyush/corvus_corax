# NATO Admiralty Intelligence Scoring System

**Module**: `core/admiralty.py`  
**Version**: v0.9  
**Purpose**: NATO-standard confidence scoring for intelligence assessment

## Overview

The NATO Admiralty Intelligence Scoring System provides a standardized framework for assessing intelligence confidence based on source reliability and information reliability. This system, originally developed by NATO for intelligence evaluation, has been adapted for cybersecurity reconnaissance to provide consistent, defensible confidence scores for threat intelligence.

## Theoretical Foundation

### NATO Admiralty Code System

The NATO Admiralty Code (also known as the NATO Intelligence Rating System) is a two-character code that represents the reliability of a source and the credibility of information:

**Format**: `[Source Reliability][Information Reliability]`

**Example**: `A1` = Completely Reliable Source + Confirmed Information

### Components

#### 1. Source Reliability (A-F)

Assesses the trustworthiness of the information source:

| Code | Rating | Description | Value |
|------|--------|-------------|-------|
| A | Completely Reliable | No doubt about authenticity, trustworthiness, or competency; has a history of complete reliability | 1.0 |
| B | Usually Reliable | Minor doubts about authenticity, trustworthiness, or competency; has a history of valid information most of the time | 0.8 |
| C | Fairly Reliable | Doubts about authenticity, trustworthiness, or competency; has provided valid information in the past but is now inconsistent | 0.6 |
| D | Not Usually Reliable | Significant doubts about authenticity, trustworthiness, or competency; has provided unreliable information in the past | 0.4 |
| E | Unreliable | Lacks authenticity, trustworthiness, or competency; history of invalid information | 0.2 |
| F | Reliability Cannot Be Judged | Insufficient information to assess reliability | 0.1 |

#### 2. Information Reliability (1-6)

Assesses the credibility and accuracy of the information itself:

| Code | Rating | Description | Value |
|------|--------|-------------|-------|
| 1 | Confirmed | Confirmed by other independent sources | 1.0 |
| 2 | Probably True | Logical and consistent with other information | 0.9 |
| 3 | Possibly True | Reasonably consistent but not confirmed | 0.7 |
| 4 | Doubtfully True | Not consistent with other information | 0.4 |
| 5 | Improbable | Inconsistent with other information | 0.2 |
| 6 | Truth Cannot Be Judged | Insufficient information to assess credibility | 0.1 |

## Implementation

### Class Structure

```python
class AdmiraltyScorer:
    def __init__(self):
        self.source_reliability_map = {
            SourceReliability.A: 1.0,
            SourceReliability.B: 0.8,
            SourceReliability.C: 0.6,
            SourceReliability.D: 0.4,
            SourceReliability.E: 0.2,
            SourceReliability.F: 0.1
        }
        
        self.info_reliability_map = {
            InformationReliability.CONFIRMED: 1.0,
            InformationReliability.PROBABLY_TRUE: 0.9,
            InformationReliability.POSSIBLY_TRUE: 0.7,
            InformationReliability.DOUBTFULLY_TRUE: 0.4,
            InformationReliability.IMPROBABLE: 0.2,
            InformationReliability.CANNOT_JUDGE: 0.1
        }
```

### Enums

#### SourceReliability Enum

```python
class SourceReliability(Enum):
    A = "Completely Reliable"
    B = "Usually Reliable"
    C = "Fairly Reliable"
    D = "Not Usually Reliable"
    E = "Unreliable"
    F = "Cannot Be Judged"
```

#### InformationReliability Enum

```python
class InformationReliability(Enum):
    CONFIRMED = "Confirmed"
    PROBABLY_TRUE = "Probably True"
    POSSIBLY_TRUE = "Possibly True"
    DOUBTFULLY_TRUE = "Doubtfully True"
    IMPROBABLE = "Improbable"
    CANNOT_JUDGE = "Cannot Be Judged"
```

#### EvidenceType Enum

```python
class EvidenceType(Enum):
    CERTIFICATE_MATCH = {
        "base_weight": 40,
        "source_reliability": SourceReliability.A,
        "info_reliability": InformationReliability.RELIABLE
    }
    SHARED_FAVICON = {
        "base_weight": 25,
        "source_reliability": SourceReliability.B,
        "info_reliability": InformationReliability.PROBABLY_TRUE
    }
    SAME_TECH_STACK = {
        "base_weight": 20,
        "source_reliability": SourceReliability.B,
        "info_reliability": InformationReliability.PROBABLY_TRUE
    }
    SAME_ASN = {
        "base_weight": 15,
        "source_reliability": SourceReliability.A,
        "info_reliability": InformationReliability.RELIABLE
    }
    # ... more evidence types
```

### Scoring Algorithm

#### Confidence Calculation

```python
def calculate_score(self, evidence_type, source_reliability, info_reliability):
    """
    Calculates weighted confidence score based on:
    - Evidence type base weight
    - Source reliability multiplier
    - Information reliability multiplier
    """
    evidence_config = EvidenceType[evidence_type].value
    base_weight = evidence_config["base_weight"]
    
    source_value = self.source_reliability_map[source_reliability]
    info_value = self.info_reliability_map[info_reliability]
    
    weighted_score = base_weight * source_value * info_value
    
    admiralty_code = self._generate_admiralty_code(
        source_reliability, info_reliability, weighted_score
    )
    
    return {
        "weighted_score": weighted_score,
        "admiralty_code": admiralty_code,
        "source_reliability": source_reliability.value,
        "info_reliability": info_reliability.value,
        "base_weight": base_weight
    }
```

#### Admiralty Code Generation

```python
def _generate_admiralty_code(self, source_reliability, info_reliability, score):
    """
    Generates Admiralty code based on confidence percentage.
    
    Confidence Ranges:
    - 90-100: A1 (Completely Reliable + Confirmed)
    - 75-89:  B2 (Usually Reliable + Probably True)
    - 60-74:  C3 (Fairly Reliable + Possibly True)
    - 40-59:  D4 (Not Usually Reliable + Doubtfully True)
    - 20-39:  E5 (Unreliable + Improbable)
    - 0-19:   F6 (Cannot Be Judged)
    """
    if score >= 90:
        return "A1"
    elif score >= 75:
        return "B2"
    elif score >= 60:
        return "C3"
    elif score >= 40:
        return "D4"
    elif score >= 20:
        return "E5"
    else:
        return "F6"
```

### Evidence Types

#### Certificate Match (Weight: 40)

- **Description**: Shared TLS certificate fingerprint
- **Source Reliability**: A (Cryptographically verified)
- **Info Reliability**: RELIABLE (Fingerprint matching)
- **Use Case**: Identifying shared infrastructure

#### Shared Favicon (Weight: 25)

- **Description**: Identical favicon hash across domains
- **Source Reliability**: B (Can be spoofed)
- **Info Reliability**: PROBABLY_TRUE (Hash collision unlikely)
- **Use Case**: Infrastructure correlation

#### Same Tech Stack (Weight: 20)

- **Description**: Identical technology stack
- **Source Reliability**: B (Header-based detection)
- **Info Reliability**: PROBABLY_TRUE (Consistent patterns)
- **Use Case**: Shared hosting/platform detection

#### Same ASN (Weight: 15)

- **Description**: Same Autonomous System Number
- **Source Reliability**: A (Authoritative IP allocation)
- **Info Reliability**: RELIABLE (ASN databases)
- **Use Case**: Network infrastructure correlation

#### Outdated Software (Weight: 30)

- **Description**: Detected outdated software version
- **Source Reliability**: B (Version detection)
- **Info Reliability**: PROBABLY_TRUE (Version comparison)
- **Use Case**: Vulnerability assessment

#### Admin Port Exposure (Weight: 25)

- **Description**: Open administrative ports (SSH, RDP, etc.)
- **Source Reliability**: A (Port scanning)
- **Info Reliability**: RELIABLE (Direct observation)
- **Use Case**: Attack surface assessment

#### Missing Security Header (Weight: 10)

- **Description**: Missing security headers (HSTS, CSP, etc.)
- **Source Reliability**: B (Header analysis)
- **Info Reliability**: PROBABLY_TRUE (Header absence)
- **Use Case**: Security posture assessment

#### DNS Record (Weight: 15)

- **Description**: DNS record analysis
- **Source Reliability**: A (Authoritative DNS)
- **Info Reliability**: RELIABLE (DNS records)
- **Use Case**: Infrastructure profiling

#### Email Pattern (Weight: 15)

- **Description**: Email naming convention detection
- **Source Reliability**: B (Pattern analysis)
- **Info Reliability**: PROBABLY_TRUE (Pattern matching)
- **Use Case**: Email enumeration

#### Phone Verified (Weight: 30 — v0.9)

- **Description**: Phone number format/operator verification
- **Source Reliability**: B (Phone analysis)
- **Info Reliability**: PROBABLY_TRUE (Format validation)
- **Use Case**: Human identity verification

#### Breach Correlation (Weight: 25 — v0.9)

- **Description**: Same email/password appears in breach databases
- **Source Reliability**: C (Breach databases vary in reliability)
- **Info Reliability**: POSSIBLY_TRUE (Breach data may be stale)
- **Use Case**: Identity risk assessment

#### Social Profile Match (Weight: 20 — v0.9)

- **Description**: Same username across multiple platforms
- **Source Reliability**: C (Social media data)
- **Info Reliability**: POSSIBLY_TRUE (Different people may share usernames)
- **Use Case**: Identity correlation

#### Person Email Match (Weight: 15 — v0.9)

- **Description**: Person-email association
- **Source Reliability**: C (Email patterns are inferential)
- **Info Reliability**: POSSIBLY_TRUE (Email may not be personal)
- **Use Case**: Human identity resolution

#### Organization Registry Match (Weight: 18 — v0.9)

- **Description**: Official company registry verification
- **Source Reliability**: B (Official registries)
- **Info Reliability**: PROBABLY_TRUE (Registry data is reliable)
- **Use Case**: Organization verification

#### Academic Affiliation (Weight: 12 — v0.9)

- **Description**: Academic institution affiliation
- **Source Reliability**: B (Academic records)
- **Info Reliability**: PROBABLY_TRUE (ORCID/publications)
- **Use Case**: Professional background analysis

#### Location Correlation (Weight: 14 — v0.9)

- **Description**: Location-based correlation
- **Source Reliability**: B (Geo data)
- **Info Reliability**: POSSIBLY_TRUE (VPN may obscure location)
- **Use Case**: Movement analysis

#### Financial Trace (Weight: 10 — v0.9)

- **Description**: Financial footprint (crypto wallets, etc.)
- **Source Reliability**: D (Financial data can be speculative)
- **Info Reliability**: POSSIBLY_TRUE (Wallet ownership unverified)
- **Use Case**: Financial intelligence

#### Personal Data Correlation (Weight: 8 — v0.9)

- **Description**: Cross-verification of personal data
- **Source Reliability**: C (Mixed reliability)
- **Info Reliability**: POSSIBLY_TRUE
- **Use Case**: Identity resolution support

## Default Source Reliability Mapping

Each data source has a default source reliability based on its inherent trustworthiness:

```python
DEFAULT_SOURCE_RELIABILITY = {
    "cert_intel": SourceReliability.A,      # Cryptographically verified
    "asn": SourceReliability.A,            # Authoritative IP allocation
    "dns_intel": SourceReliability.A,      # Authoritative DNS
    "scan": SourceReliability.A,           # Direct port observation
    "tech_detect": SourceReliability.B,    # Header-based detection
    "http_headers": SourceReliability.B,   # Can be spoofed
    "metadata_intel": SourceReliability.B, # Can be spoofed
    "email_intel": SourceReliability.B,    # Pattern-based
    "subdomain_enum": SourceReliability.B, # Passive OSINT
    "footprint": SourceReliability.B,      # DNS-based
    "geoip": SourceReliability.B,          # IP geolocation databases
    "whois": SourceReliability.C,          # WHOIS data accuracy varies
}
```

## v0.9 — Centralized Rules (`config/rules.json`)

Evidence weights and source reliability are now loaded from `config/rules.json` instead of hardcoding:

```json
{
  "evidence_weights": {
    "certificate_match": 40,
    "shared_favicon": 25,
    "same_tech_stack": 20,
    "same_asn": 15,
    "phone_verified": 30,
    "breach_correlation": 25,
    "social_profile_match": 20,
    "org_registry_match": 18,
    "location_correlation": 14,
    "financial_trace": 10,
    "personal_data_correlation": 8
  },
  "source_reliability": {
    "phone_intel": "B",
    "social_intel": "C",
    "breach_intel": "C",
    "academic_intel": "B",
    "org_intel": "B",
    "financial_intel": "D",
    "geo_intel": "B"
  }
}
```

**Key benefits**:
- No more hardcoded values in `core/admiralty.py`
- Users can customize evidence weights without code changes
- Future intelligence modules can define their own reliability profiles

## v0.9 — Confidence Aggregation (`core/confidence.py`)

Weak individual evidence combines into strong evidence:

**Formula**: `combined = 1 - (1-c1)*(1-c2)*(1-c3)*...`

```python
from core.confidence import combine_confidences, aggregate_entity_confidence

# Example: 3 weak candidate links (0.4, 0.3, 0.6)
combined = combine_confidences([0.4, 0.3, 0.6])
# Result: 0.832 — strong evidence from weak individual links

# Aggregate all candidate/possible links to a target entity
result = aggregate_entity_confidence(context, "ahmet")
# {
#   "combined_confidence": 0.8992,
#   "evidence_count": 4,
#   "evidence_list": [...]
# }
```

This enables **entity resolution** — determining that `phone:+90532...`, `email:ahmet@example.com`, and `social_profile:github/ahmet` all belong to the same person.

## Integration with Nexus Engine

### Risk Calculation

Nexus Engine uses Admiralty scoring for risk assessment:

```python
def calculate_risk(self, entity):
    evidence_chain = []
    total_weight = 0
    
    for evidence in entity_evidence:
        scorer = AdmiraltyScorer()
        score = scorer.calculate_score(
            evidence_type=evidence["type"],
            source_reliability=evidence["source"],
            info_reliability=evidence["info"]
        )
        evidence_chain.append(score)
        total_weight += score["weighted_score"]
    
    risk_score = min(100, total_weight)
    admiralty_rating = self._calculate_admiralty_code(risk_score)
    
    return {
        "score": risk_score,
        "level": self._get_risk_level(risk_score),
        "admiralty_rating": admiralty_rating,
        "evidence_count": len(evidence_chain),
        "evidence_chain": evidence_chain
    }
```

### Evidence Chain Structure

Each evidence item in the chain contains:

```python
{
    "type": "CERTIFICATE_MATCH",
    "weighted_score": 40.0,
    "admiralty_code": "A1",
    "source_reliability": "Completely Reliable",
    "info_reliability": "Confirmed",
    "base_weight": 40,
    "description": "Shared certificate fingerprint detected"
}
```

## Output Formats

### Summary Mode

```
Entity: example.com
Risk Score: 75
Risk Level: High
Admiralty Rating: B2
Evidence Count: 4
```

### Verbose Mode

```
Entity: example.com
Risk Score: 75
Risk Level: High
Admiralty Rating: B2
Evidence Count: 4

Evidence Chain:
1. CERTIFICATE_MATCH (A1)
   - Weighted Score: 40.0
   - Source: Completely Reliable
   - Info: Confirmed
   - Description: Shared certificate fingerprint detected

2. SAME_TECH_STACK (B2)
   - Weighted Score: 16.0
   - Source: Usually Reliable
   - Info: Probably True
   - Description: Identical technology stack detected

3. SAME_ASN (A1)
   - Weighted Score: 15.0
   - Source: Completely Reliable
   - Info: Confirmed
   - Description: Same ASN detected

4. MISSING_SECURITY_HEADER (C3)
   - Weighted Score: 6.0
   - Source: Fairly Reliable
   - Info: Possibly True
   - Description: HSTS header missing
```

## Context Integration

### Admiralty Summary

ContextManager provides Admiralty intelligence summary:

```python
def get_admiralty_summary(self):
    """
    Returns Admiralty intelligence summary for all entities.
    """
    summary = {
        "total_entities": 0,
        "high_confidence": 0,  # A1, B2
        "medium_confidence": 0,  # C3, D4
        "low_confidence": 0,  # E5, F6
        "entities": []
    }
    
    # Calculate summary from risk profiles
    return summary
```

### Entity-Specific Admiralty

ContextManager provides entity-specific Admiralty details:

```python
def get_entity_admiralty(self, entity):
    """
    Returns detailed Admiralty evidence chain for specific entity.
    """
    return {
        "entity": entity,
        "admiralty_rating": "B2",
        "risk_score": 75,
        "evidence_chain": [...]
    }
```

## CLI Integration

### Verbose Flag

Nexus module supports verbose mode for detailed evidence chains:

```bash
corvus > nexus analyze --verbose
```

### Context Command

Context command supports Admiralty intelligence display:

```bash
corvus > context --admiralty
corvus > context example.com --admiralty
```

## Configuration

### Evidence Weights

Evidence weights can be customized in `core/admiralty.py`:

```python
class EvidenceType(Enum):
    CERTIFICATE_MATCH = {
        "base_weight": 40,  # Adjust as needed
        ...
    }
```

### Source Reliability Mapping

Default source reliability can be customized per module:

```python
DEFAULT_SOURCE_RELIABILITY = {
    "cert_intel": SourceReliability.A,
    ...
}
```

## Best Practices

### 1. Evidence Weight Assignment

- **High Weight (30-40)**: Cryptographically verified, direct observation
- **Medium Weight (15-25)**: Pattern-based, correlation-based
- **Low Weight (5-10)**: Indirect, potentially spoofable

### 2. Source Reliability Assignment

- **A (Completely Reliable)**: Cryptographic verification, authoritative sources
- **B (Usually Reliable)**: Standard protocols, well-established patterns
- **C (Fairly Reliable)**: Third-party data, variable accuracy
- **D-F**: Rarely used in cybersecurity context

### 3. Information Reliability Assignment

- **1 (Confirmed)**: Cross-verified, multiple sources
- **2 (Probably True)**: Consistent with other data
- **3 (Possibly True)**: Reasonable but unconfirmed
- **4-6**: Rarely used in cybersecurity context

## Limitations

### 1. Subjectivity

Source and information reliability assessment involves some subjectivity. Default mappings are provided but should be reviewed for specific use cases.

### 2. Context Dependence

Reliability can vary based on context. For example, WHOIS data may be reliable for some domains but not others.

### 3. Weight Calibration

Evidence weights are calibrated for general cybersecurity reconnaissance but may need adjustment for specific threat models.

## Future Enhancements

### 1. Machine Learning Integration

- Automated source reliability assessment
- Dynamic weight adjustment based on historical accuracy
- Anomaly detection in evidence chains

### 2. Temporal Weighting

- Time-decay for older evidence
- Recency weighting for recent observations
- Temporal correlation analysis

### 3. Cross-Source Validation

- Automated cross-validation between sources
- Confidence boosting based on multi-source confirmation
- Contradiction detection and resolution

### 4. Customizable Profiles

- User-defined reliability profiles
- Industry-specific weightings
- Threat model-specific configurations

## References

- NATO Standardization Agreement (STANAG) 2511
- NATO Intelligence Handbook
- Intelligence Community Directive (ICD) 203
- Cyber Intelligence Tradecraft Standards
