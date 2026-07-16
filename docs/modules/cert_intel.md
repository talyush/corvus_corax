# Certificate Intelligence Module

**Module**: `cert_intel.py`  
**Version**: v0.8  
**Purpose**: Deep TLS certificate analysis and fingerprinting for entity correlation

## Overview

The Certificate Intelligence Module performs comprehensive TLS certificate analysis, extracting structured intelligence for use in Nexus correlation. It identifies shared certificates across entities, detects wildcard certificates, and provides expiration timeline analysis.

## Architecture

### Class Structure

```python
class CertIntelModule(BaseModule):
    name = "cert"
    
    def execute(self):
        # Parse target (host:port)
        # Fetch certificate
        # Parse certificate fields
        # Calculate fingerprint
        # Detect wildcards
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. Certificate Fetching (`_fetch_cert`)

Opens TLS connection and retrieves certificate data:

- **SSL Context**: Configured with `check_hostname=False` and `CERT_OPTIONAL` to handle self-signed/mismatched certificates
- **Socket Connection**: Creates raw socket with configurable timeout
- **Certificate Extraction**: Returns both DER bytes and parsed certificate dictionary
- **Fallback Handling**: Returns DER bytes even if certificate parsing fails

```python
def _fetch_cert(self, host, port, timeout):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_OPTIONAL
    raw_sock = socket.create_connection((host, port), timeout=timeout)
    conn = ctx.wrap_socket(raw_sock, server_hostname=host)
    der_bytes = conn.getpeercert(binary_form=True)
    cert_dict = conn.getpeercert(binary_form=False)
    conn.close()
    return der_bytes, cert_dict or {}
```

#### 2. RDN Parsing (`_parse_rdns`)

Extracts specific fields from Relative Distinguished Names:

- **Target Fields**: Common Name (CN), Organization (O), Country (C)
- **Traversal**: Iterates through RDN list to find requested field
- **Return**: Field value or None if not found

```python
def _parse_rdns(self, rdns_list, field):
    for rdn in rdns_list:
        for key, val in rdn:
            if key == field:
                return val
    return None
```

#### 3. SAN Parsing (`_parse_san`)

Extracts Subject Alternative Names:

- **DNS SANs**: Filters for DNS-type SAN entries
- **Normalization**: Converts to lowercase for consistency
- **Return**: List of domain names from SAN extension

```python
def _parse_san(self, cert_dict):
    san_list = []
    for ext_key, ext_val in cert_dict.get("subjectAltName", []):
        if ext_key == "DNS":
            san_list.append(ext_val.lower())
    return san_list
```

#### 4. Wildcard Detection (`_detect_wildcards`)

Identifies wildcard patterns in SANs:

- **Pattern Matching**: Checks for `*.` prefix
- **Return**: List of wildcard SAN entries

```python
def _detect_wildcards(self, san_list):
    return [san for san in san_list if san.startswith("*.")]
```

#### 5. Fingerprint Calculation (`_calculate_fingerprint`)

Computes SHA-256 fingerprint:

- **Input**: DER-encoded certificate bytes
- **Algorithm**: SHA-256
- **Format**: Hexadecimal string
- **Purpose**: Unique identifier for certificate matching

```python
def _calculate_fingerprint(self, der_bytes):
    return hashlib.sha256(der_bytes).hexdigest()
```

## Data Flow

```
Input: host:port
    ↓
_fetch_cert()
    ↓
DER bytes + Certificate Dictionary
    ↓
_parse_rdns() + _parse_san() + _detect_wildcards()
    ↓
_calculate_fingerprint()
    ↓
Structured Certificate Intelligence
    ↓
ContextManager.add_certificate()
    ↓
Standardized Payload
```

## Context Integration

### Certificate Data Storage

Certificates are stored in `context.data["certificates"]`:

```python
{
    "fingerprint": {
        "fingerprint": "sha256_hash",
        "issuer": "CN=DigiCert, O=DigiCert Inc",
        "subject": "CN=example.com",
        "san": ["example.com", "*.example.com", "www.example.com"],
        "wildcards": ["*.example.com"],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z",
        "hosts": ["example.com:443", "www.example.com:443"]
    }
}
```

### Relationships Added

- **Certificate to Host**: `has_certificate` relation
- **Certificate to Issuer**: `issued_by` relation
- **Certificate to Domain**: `covers_domain` relation (for SANs)

### Notes Added

- Certificate discovery notes with severity based on expiration
- Wildcard certificate warnings
- Expiration timeline alerts

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

### Connection Errors

- **Timeout**: Returns error payload with timeout message
- **SSL Errors**: Returns error with SSL-specific details
- **Certificate Parse Failures**: Still returns DER bytes if available

### Invalid Input

- **Missing Host**: Returns error requiring host parameter
- **Invalid Port**: Uses default port 443 if not specified

## Nexus Integration

### Shared Certificate Detection

Nexus Engine uses certificate fingerprints to identify shared certificates:

```python
# RULE 5: Shared Certificate Detection
for fingerprint, cert_data in context.data["certificates"].items():
    if len(cert_data["hosts"]) >= 2:
        for host_a, host_b in combinations(cert_data["hosts"], 2):
            context.add_derived_relation(
                src_type="host", src_value=host_a,
                relation="shares_certificate",
                dst_type="host", dst_value=host_b,
                evidence=f"Both hosts use certificate with fingerprint {fingerprint[:16]}...",
                confidence=0.95
            )
```

### Admiralty Scoring

Certificate intelligence has high source reliability (A) due to cryptographic verification:

```python
EvidenceType.CERTIFICATE_MATCH = {
    "base_weight": 40,
    "source_reliability": SourceReliability.A,  # Cryptographically verified
    "info_reliability": InformationReliability.RELIABLE
}
```

## Output Format

### Success Payload

```json
{
  "module": "cert",
  "target": "example.com:443",
  "status": "success",
  "data": {
    "host": "example.com",
    "port": 443,
    "fingerprint": "a1b2c3d4e5f6...",
    "issuer": "CN=DigiCert, O=DigiCert Inc",
    "subject": "CN=example.com",
    "san": ["example.com", "*.example.com"],
    "wildcards": ["*.example.com"],
    "not_before": "2024-01-01T00:00:00Z",
    "not_after": "2025-01-01T00:00:00Z",
    "days_until_expiry": 180
  },
  "notes": [
    {
      "text": "Certificate valid for 180 days",
      "source": "cert_intel",
      "severity": "info",
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "src": {"type": "host", "value": "example.com:443"},
      "relation": "has_certificate",
      "dst": {"type": "certificate", "value": "a1b2c3d4..."},
      "evidence": "TLS handshake",
      "confidence": 1.0
    }
  ]
}
```

### Error Payload

```json
{
  "module": "cert",
  "target": "example.com:443",
  "status": "error",
  "error": "Connection timeout",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **Connection Timeout**: Uses config timeout (default 3.0s)
- **SSL Handshake**: May be slow for distant servers
- **Certificate Parsing**: Minimal overhead
- **Fingerprint Calculation**: SHA-256 is fast

## Security Considerations

- **Certificate Verification**: Disabled to analyze self-signed certificates
- **Hostname Verification**: Disabled to analyze mismatched certificates
- **Data Exposure**: Certificate data is public information
- **No Private Keys**: Only public certificate data is analyzed

## Future Enhancements

- **OCSP Stapling**: Check certificate revocation status
- **Certificate Transparency**: Query CT logs for certificate history
- **Chain Analysis**: Analyze full certificate chain
- **Key Strength**: Analyze RSA/ECDSA key parameters
- **Signature Algorithms**: Detect weak signature algorithms
