# ASN Intelligence Module

**Module**: `asn.py`  
**Version**: v0.8  
**Purpose**: ASN lookup, network infrastructure profiling, and correlation

## Overview

The ASN Intelligence Module performs Autonomous System Number (ASN) lookups to identify network infrastructure, extract organization and ISP information, determine CIDR blocks, enumerate related IP addresses, and provide country-level geolocation intelligence for Nexus correlation.

## Architecture

### Class Structure

```python
class ASNModule(BaseModule):
    name = "asn"
    
    def execute(self):
        # Parse target IP
        # Perform ASN lookup via ip-api.com
        # Extract organization, ASN, CIDR
        # Calculate related IPs in CIDR
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. ASN Lookup (`_lookup_asn`)

Performs ASN lookup using ip-api.com API:

- **API Endpoint**: Uses http://ip-api.com/json/{ip}
- **Fields Requested**: as, asname, org, country, isp, query
- **Error Handling**: Catches HTTP errors and JSON parse errors
- **Return**: ASN data dictionary or None on error

```python
def _lookup_asn(self, ip):
    try:
        url = f"http://ip-api.com/json/{ip}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.config.get("user_agent", "CorvusCorax/0.8")}
        )
        with urllib.request.urlopen(req, timeout=self.config.get("timeout", 3.0)) as response:
            data = json.loads(response.read().decode())
            
            return {
                "ip": data.get("query"),
                "asn": data.get("as"),
                "as_number": data.get("as", "").split()[0].replace("AS", ""),
                "organization": data.get("org"),
                "country": data.get("country"),
                "isp": data.get("isp"),
                "cidr": self._extract_cidr_from_asn(data.get("as", ""))
            }
    except Exception:
        return None
```

#### 2. CIDR Extraction (`_extract_cidr_from_asn`)

Extracts CIDR block from ASN string:

- **ASN Format**: Parses AS12345 (CIDR) format
- **CIDR Extraction**: Extracts CIDR block from parentheses
- **Return**: CIDR string or None

```python
def _extract_cidr_from_asn(self, asn_string):
    if not asn_string:
        return None
    
    # Format: AS12345 (192.168.1.0/24)
    if "(" in asn_string and ")" in asn_string:
        cidr = asn_string.split("(")[1].split(")")[0]
        return cidr
    
    return None
```

#### 3. Related IP Enumeration (`_enumerate_related_ips`)

Enumerates related IPs within CIDR block:

- **CIDR Parsing**: Parses CIDR notation (e.g., 192.168.1.0/24)
- **Network Calculation**: Calculates network range using ipaddress module
- **IP Generation**: Generates all IPs in the CIDR block
- **Limit**: Limits to first 256 IPs to avoid excessive enumeration
- **Return**: List of related IP addresses

```python
def _enumerate_related_ips(self, cidr, limit=256):
    if not cidr:
        return []
    
    try:
        import ipaddress
        network = ipaddress.ip_network(cidr, strict=False)
        related_ips = []
        
        for ip in network.hosts():
            related_ips.append(str(ip))
            if len(related_ips) >= limit:
                break
        
        return related_ips
    except Exception:
        return []
```

#### 4. Country-Level Geolocation

Extracts country information from ASN data:

- **Country Code**: ISO 3166-1 alpha-2 country code
- **Country Name**: Full country name
- **Return**: Country information

```python
def _extract_country_info(self, asn_data):
    return {
        "code": asn_data.get("country", ""),
        "name": self._country_code_to_name(asn_data.get("country", ""))
    }
```

## Data Flow

```
Input: ip_address
    ↓
_lookup_asn() via ip-api.com
    ↓
Extract ASN, Organization, CIDR
    ↓
_enumerate_related_ips() from CIDR
    ↓
Extract Country Info
    ↓
Structured ASN Intelligence
    ↓
ContextManager.add_asn_intel()
    ↓
Standardized Payload
```

## Context Integration

### ASN Intel Data Storage

ASN intelligence is stored in `context.data["asn_intel"]`:

```python
{
    "192.168.1.100": {
        "ip": "192.168.1.100",
        "asn": "AS15169 Google LLC",
        "as_number": "15169",
        "organization": "Google Cloud",
        "country": "United States",
        "country_code": "US",
        "isp": "Google LLC",
        "cidr": "192.168.1.0/24",
        "related_ips": [
            "192.168.1.1",
            "192.168.1.2",
            "192.168.1.3"
        ]
    }
}
```

### Relationships Added

- **IP to ASN**: `belongs_to_asn` relation
- **IP to Organization**: `hosted_by` relation
- **IP to Country**: `located_in` relation
- **IP to Related IP**: `shares_cidr` relation

### Notes Added

- ASN discovery notes
- Organization detection notes
- CIDR block notes
- Country geolocation notes

## Configuration

### Required Config Parameters

```json
{
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.8"
}
```

### Module-Specific Config

- **related_ip_limit**: Maximum number of related IPs to enumerate (default: 256)

## Error Handling

### API Errors

- **HTTP Errors**: Returns error with HTTP details
- **JSON Parse Errors**: Returns error with parse details
- **Timeout**: Returns error with timeout message
- **Rate Limiting**: Returns error if rate limited

### Invalid Input

- **Invalid IP**: Returns error requiring valid IP address
- **Missing CIDR**: Continues without CIDR information
- **Parse Errors**: Continues with successfully parsed data

## Nexus Integration

### ASN Intelligence Correlation

Nexus Engine uses ASN intelligence for network correlation:

```python
# RULE 12: ASN Intelligence Correlation
asn_index = {}
for ip, asn_data in context.data["asn_intel"].items():
    asn = asn_data.get("asn")
    if asn:
        asn_index.setdefault(asn, []).append(ip)

# 12a. Shares ASN
for asn, ips in asn_index.items():
    if len(ips) >= 2:
        for ip_a, ip_b in combinations(ips, 2):
            context.add_derived_relation(
                src_type="ip", src_value=ip_a,
                relation="shares_asn",
                dst_type="ip", dst_value=ip_b,
                evidence=f"Both IPs belong to {asn}",
                confidence=0.9
            )

# 12b. Same Provider
org_index = {}
for ip, asn_data in context.data["asn_intel"].items():
    org = asn_data.get("organization")
    if org:
        org_index.setdefault(org, []).append(ip)

for org, ips in org_index.items():
    if len(ips) >= 2:
        for ip_a, ip_b in combinations(ips, 2):
            context.add_derived_relation(
                src_type="ip", src_value=ip_a,
                relation="same_provider",
                dst_type="ip", dst_value=ip_b,
                evidence=f"Both IPs hosted by {org}",
                confidence=0.85
            )

# 12c. Same Prefix (CIDR)
for ip, asn_data in context.data["asn_intel"].items():
    cidr = asn_data.get("cidr")
    related = asn_data.get("related_ips", [])
    
    for related_ip in related:
        if related_ip != ip:
            context.add_derived_relation(
                src_type="ip", src_value=ip,
                relation="same_prefix",
                dst_type="ip", dst_value=related_ip,
                evidence=f"Both IPs in CIDR {cidr}",
                confidence=0.95
            )
```

### Admiralty Scoring

ASN intelligence has high source reliability (A) due to authoritative IP allocation databases:

```python
EvidenceType.SAME_ASN = {
    "base_weight": 15,
    "source_reliability": SourceReliability.A,  # Authoritative IP allocation
    "info_reliability": InformationReliability.RELIABLE
}
```

## Output Format

### Success Payload

```json
{
  "module": "asn",
  "target": "192.168.1.100",
  "status": "success",
  "data": {
    "ip": "192.168.1.100",
    "asn": "AS15169 Google LLC",
    "as_number": "15169",
    "organization": "Google Cloud",
    "country": "United States",
    "country_code": "US",
    "isp": "Google LLC",
    "cidr": "192.168.1.0/24",
    "related_ips": [
      "192.168.1.1",
      "192.168.1.2",
      "192.168.1.3"
    ]
  },
  "notes": [
    {
      "text": "ASN identified: AS15169 Google LLC",
      "source": "asn_intel",
      "severity": "info",
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "src": {"type": "ip", "value": "192.168.1.100"},
      "relation": "belongs_to_asn",
      "dst": {"type": "asn", "value": "AS15169"},
      "evidence": "ASN lookup",
      "confidence": 1.0
    }
  ]
}
```

### Error Payload

```json
{
  "module": "asn",
  "target": "192.168.1.100",
  "status": "error",
  "error": "ASN lookup timeout",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **API Request**: Single HTTP request per IP
- **CIDR Enumeration**: Linear time based on CIDR size (limited to 256 IPs)
- **Network Calculation**: Efficient using ipaddress module
- **Rate Limiting**: ip-api.com has rate limits (45 requests/minute)

## Security Considerations

- **Public API**: Uses public ip-api.com API
- **Data Exposure**: ASN data is public information
- **No Authentication**: No API key required
- **Rate Limiting**: Respects API rate limits

## Future Enhancements

- **Multiple API Sources**: Support multiple ASN lookup APIs (RIPE, ARIN, etc.)
- **Historical ASN Data**: Query historical ASN assignments
- **BGP Route Analysis**: Analyze BGP routing information
- **IP Reputation**: Check IP reputation from threat intelligence feeds
- **Geolocation Enhancement**: More precise geolocation data
