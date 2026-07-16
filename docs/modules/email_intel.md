# Email Pattern Discovery Module

**Module**: `email_intel.py`  
**Version**: v0.8  
**Purpose**: Email infrastructure profiling, provider identification, and pattern discovery

## Overview

The Email Pattern Discovery Module analyzes DNS context (MX, SPF, DMARC) to identify email providers, extract reporting addresses, detect email naming conventions, distinguish role-based from personal emails, and generate likely email formats for target domains.

## Architecture

### Class Structure

```python
class EmailIntelModule(BaseModule):
    name = "email"
    
    def execute(self):
        # Parse target domain and sample emails
        # Identify email provider via SPF/MX fingerprints
        # Extract DMARC reporting addresses
        # Analyze email naming conventions
        # Distinguish role-based vs personal emails
        # Generate likely email formats
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. Provider Fingerprinting

##### SPF Provider Map

SPF include patterns mapped to email providers:

```python
PROVIDER_SPF_MAP = [
    ("_spf.google.com", "Google Workspace"),
    ("_spf.googlemail.com", "Google Workspace"),
    ("spf.protection.outlook.com", "Microsoft 365"),
    ("mail.protection.outlook.com", "Microsoft 365"),
    ("spf.mandrillapp.com", "Mandrill (Mailchimp)"),
    ("servers.mcsv.net", "Mailchimp"),
    ("sendgrid.net", "SendGrid"),
    ("amazonses.com", "Amazon SES"),
    ("mailgun.org", "Mailgun"),
    ("_spf.salesforce.com", "Salesforce"),
    ("mimecast.com", "Mimecast"),
    ("pphosted.com", "Proofpoint"),
    ("proofpoint.com", "Proofpoint"),
    ("zoho.com", "Zoho Mail"),
]
```

##### MX Provider Map

MX host patterns mapped to email providers:

```python
PROVIDER_MX_MAP = [
    ("google.com", "Google Workspace"),
    ("googlemail.com", "Google Workspace"),
    ("outlook.com", "Microsoft 365"),
    ("protection.outlook.com", "Microsoft 365"),
    ("mimecast.com", "Mimecast"),
    ("pphosted.com", "Proofpoint"),
    ("proofpoint.com", "Proofpoint"),
    ("mailgun.org", "Mailgun"),
    ("sendgrid.net", "SendGrid"),
    ("amazonses.com", "Amazon SES"),
    ("zoho.com", "Zoho Mail"),
]
```

#### 2. Provider Identification (`_identify_provider`)

Identifies email provider from SPF and MX data:

- **SPF Analysis**: Checks SPF includes against provider map
- **MX Analysis**: Checks MX hosts against provider map
- **Priority**: SPF takes precedence over MX
- **Return**: Provider name or "Unknown"

```python
def _identify_provider(self, spf_record, mx_hosts):
    # Check SPF includes
    if spf_record:
        for pattern, provider in PROVIDER_SPF_MAP:
            if pattern in spf_record:
                return provider
    
    # Check MX hosts
    for mx_host in mx_hosts:
        for pattern, provider in PROVIDER_MX_MAP:
            if pattern in mx_host.lower():
                return provider
    
    return "Unknown"
```

#### 3. DMARC Reporting Extraction (`_extract_dmarc_reporting`)

Extracts DMARC reporting addresses:

- **RUA Extraction**: Extracts rua (aggregate reporting) addresses
- **RUF Extraction**: Extracts ruf (forensic reporting) addresses
- **Email Parsing**: Parses mailto: URIs and comma-separated lists
- **Return**: List of reporting email addresses

```python
def _extract_dmarc_reporting(self, dmarc_record):
    reporting = []
    
    # Extract rua
    if "rua=" in dmarc_record:
        rua_part = dmarc_record.split("rua=")[1].split(";")[0]
        for addr in rua_part.split(","):
            addr = addr.strip()
            if addr.startswith("mailto:"):
                addr = addr[7:]
            reporting.append(addr)
    
    # Extract ruf
    if "ruf=" in dmarc_record:
        ruf_part = dmarc_record.split("ruf=")[1].split(";")[0]
        for addr in ruf_part.split(","):
            addr = addr.strip()
            if addr.startswith("mailto:"):
                addr = addr[7:]
            reporting.append(addr)
    
    return reporting
```

#### 4. Role Alias Detection

Role-based mailbox patterns:

```python
ROLE_ALIASES = [
    "admin", "administrator", "root", "sysadmin",
    "support", "help", "info", "contact",
    "sales", "marketing", "billing", "finance",
    "hr", "jobs", "careers", "recruiting",
    "webmaster", "hostmaster", "postmaster",
    "abuse", "security", "noc", "spam",
    "office", "reception", "enquiries"
]
```

#### 5. Email Pattern Analysis (`_analyze_email_patterns`)

Analyzes email naming conventions:

- **Local Part Extraction**: Extracts local part (before @)
- **Pattern Detection**: Identifies first.last, firstlast, f.last patterns
- **Separator Detection**: Detects ., _, - separators
- **Return**: Structured pattern analysis

```python
def _analyze_email_patterns(self, email_samples):
    patterns = []
    
    for email in email_samples:
        if "@" not in email:
            continue
        
        local = email.split("@")[0].lower()
        
        # Detect first.last pattern
        if "." in local and local.count(".") == 1:
            parts = local.split(".")
            if len(parts) == 2 and all(part.isalpha() for part in parts):
                patterns.append("first.last")
        
        # Detect firstlast pattern
        elif local.isalpha() and len(local) > 3:
            patterns.append("firstlast")
        
        # Detect f.last pattern
        elif "." in local and len(local.split(".")[0]) == 1:
            patterns.append("f.last")
    
    # Return most common pattern
    if patterns:
        from collections import Counter
        return Counter(patterns).most_common(1)[0][0]
    
    return "unknown"
```

#### 6. Email Format Generation (`_generate_likely_formats`)

Generates likely email formats:

- **Pattern-Based**: Generates formats based on detected patterns
- **Common Patterns**: first.last, firstlast, f.last, first_initial.last
- **Return**: List of likely email formats

```python
def _generate_likely_formats(self, domain, detected_pattern):
    formats = []
    
    if detected_pattern == "first.last":
        formats.append(f"first.last@{domain}")
        formats.append(f"first.last@{domain}")
    elif detected_pattern == "firstlast":
        formats.append(f"firstlast@{domain}")
    elif detected_pattern == "f.last":
        formats.append(f"f.last@{domain}")
    
    # Always add common formats
    formats.extend([
        f"info@{domain}",
        f"admin@{domain}",
        f"support@{domain}"
    ])
    
    return list(set(formats))
```

## Data Flow

```
Input: domain [sample1,sample2]
    ↓
ContextManager.get_dns_records()
    ↓
Identify Provider (SPF/MX)
    ↓
Extract DMARC Reporting
    ↓
Analyze Email Patterns
    ↓
Generate Likely Formats
    ↓
Structured Email Intelligence
    ↓
ContextManager.add_email_intel()
    ↓
Standardized Payload
```

## Context Integration

### Email Intel Data Storage

Email intelligence is stored in `context.data["email_intel"]`:

```python
{
    "example.com": {
        "provider": "Google Workspace",
        "mx_hosts": ["alt1.aspmx.l.google.com", "alt2.aspmx.l.google.com"],
        "spf_record": "v=spf1 include:_spf.google.com ~all",
        "dmarc_record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
        "reporting_addresses": ["dmarc@example.com"],
        "detected_pattern": "first.last",
        "likely_formats": [
            "first.last@example.com",
            "info@example.com",
            "admin@example.com"
        ],
        "role_aliases": ["admin", "support", "info"],
        "sample_emails": ["john.doe@example.com", "jane.smith@example.com"]
    }
}
```

### Relationships Added

- **Domain to Provider**: `uses_email_provider` relation
- **Domain to Reporting**: `has_abuse_contact` relation
- **Domain to Role**: `has_role_alias` relation

### Notes Added

- Email provider detection notes
- DMARC policy notes
- Missing DMARC warnings
- Email pattern detection notes

## Configuration

### Required Config Parameters

```json
{
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.8"
}
```

### Module-Specific Config

None - uses default timeout from config.

## Error Handling

### Missing DNS Context

- **No DNS Data**: Returns error requiring DNS data first
- **Incomplete DNS**: Continues with available data

### Parse Errors

- **Invalid Email Format**: Skips invalid email samples
- **Malformed DMARC**: Continues with partial parsing
- **Missing SPF/MX**: Sets provider to "Unknown"

## Nexus Integration

### Email Leak Profiling

Nexus Engine uses email intelligence for leak profiling:

```python
# RULE 8: Email Leak Profiling
for domain, email_data in context.data["email_intel"].items():
    provider = email_data.get("provider")
    reporting = email_data.get("reporting_addresses", [])
    
    # Correlate with known providers
    if provider == "Google Workspace":
        context.add_derived_relation(
            src_type="domain", src_value=domain,
            relation="uses_google_workspace",
            dst_type="provider", dst_value="Google Workspace",
            evidence=f"Email provider identified via SPF/MX",
            confidence=0.9
        )
```

### Admiralty Scoring

Email intelligence has medium source reliability (B) due to DNS-based detection:

```python
EvidenceType.EMAIL_PATTERN = {
    "base_weight": 15,
    "source_reliability": SourceReliability.B,  # DNS-based
    "info_reliability": InformationReliability.PROBABLY_TRUE
}
```

## Output Format

### Success Payload

```json
{
  "module": "email",
  "target": "example.com",
  "status": "success",
  "data": {
    "domain": "example.com",
    "provider": "Google Workspace",
    "mx_hosts": ["alt1.aspmx.l.google.com"],
    "spf_record": "v=spf1 include:_spf.google.com ~all",
    "dmarc_record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
    "reporting_addresses": ["dmarc@example.com"],
    "detected_pattern": "first.last",
    "likely_formats": [
      "first.last@example.com",
      "info@example.com",
      "admin@example.com"
    ],
    "role_aliases": ["admin", "support", "info"],
    "sample_emails": ["john.doe@example.com"]
  },
  "notes": [
    {
      "text": "Email provider identified: Google Workspace",
      "source": "email_intel",
      "severity": "info",
      "confidence": 0.9
    }
  ],
  "relationships": [
    {
      "src": {"type": "domain", "value": "example.com"},
      "relation": "uses_email_provider",
      "dst": {"type": "provider", "value": "Google Workspace"},
      "evidence": "SPF/MX fingerprint",
      "confidence": 0.9
    }
  ]
}
```

### Error Payload

```json
{
  "module": "email",
  "target": "example.com",
  "status": "error",
  "error": "DNS data not available. Run 'dns' module first.",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **Pattern Matching**: Linear search through provider maps
- **Email Analysis**: Linear time based on sample count
- **String Operations**: Minimal overhead for pattern detection
- **No External Requests**: Uses existing DNS context

## Security Considerations

- **Email Privacy**: Only analyzes email patterns, not email content
- **Provider Detection**: Based on public DNS records
- **Reporting Addresses**: Public abuse contacts
- **Pattern Generation**: Generates likely formats, not actual emails

## Future Enhancements

- **Email Validation**: Validate generated email formats via SMTP
- **Password Reset Detection**: Detect password reset endpoints
- **Email Enumeration**: Attempt email enumeration via timing attacks
- **Breach Data Integration**: Check email patterns against breach databases
- **Disposable Email Detection**: Detect disposable email services
