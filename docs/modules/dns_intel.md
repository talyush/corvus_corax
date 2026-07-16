# DNS Intelligence Module

**Module**: `dns_intel.py`  
**Version**: v0.8  
**Purpose**: Comprehensive DNS enumeration and security record analysis

## Overview

The DNS Intelligence Module performs comprehensive DNS record enumeration, including basic records (A, AAAA, MX, NS, TXT, CAA) and security-specific records (SPF, DMARC, DKIM) for email spoofing assessment and infrastructure profiling.

## Architecture

### Class Structure

```python
class DnsIntelModule(BaseModule):
    name = "dns"
    
    def execute(self):
        # Parse target domain
        # Query basic DNS records
        # Query security records
        # Analyze email infrastructure
        # Store in context
        # Return standardized payload
```

### Key Components

#### 1. Resolver Configuration (`_get_resolver`)

Configures DNS resolver with public nameservers:

- **Nameservers**: Google (8.8.8.8, 8.8.4.4) and Cloudflare (1.1.1.1, 1.0.0.1)
- **Timeout**: Configurable timeout for all queries
- **Lifetime**: Sets resolver lifetime to match timeout
- **Purpose**: Ensures consistent DNS resolution across networks

```python
def _get_resolver(self, timeout):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4', '1.0.0.1']
    resolver.timeout = timeout
    resolver.lifetime = timeout
    return resolver
```

#### 2. Record Querying (`_query_record`)

Generic DNS record query handler:

- **Record Types**: A, AAAA, NS, TXT, CAA
- **Error Handling**: Catches NXDOMAIN, NoAnswer, NoNameservers, Timeout
- **Normalization**: Strips quotes from TXT records
- **Return**: List of record values or empty list on error

```python
def _query_record(self, domain, rtype, timeout):
    try:
        resolver = self._get_resolver(timeout)
        answers = resolver.resolve(domain, rtype)
        return [str(rdata).strip('"\'') for rdata in answers]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, 
            dns.resolver.NoNameservers, dns.exception.Timeout):
        return []
    except Exception:
        return []
```

#### 3. MX Record Querying (`_query_mx`)

Specialized MX record parsing:

- **Priority Extraction**: Extracts MX priority values
- **Host Normalization**: Strips trailing dots and converts to lowercase
- **Sorting**: Sorts by priority (lower = higher preference)
- **Return**: List of MX records with priority and host

```python
def _query_mx(self, domain, timeout):
    try:
        resolver = self._get_resolver(timeout)
        answers = resolver.resolve(domain, 'MX')
        mx_list = []
        for rdata in answers:
            mx_list.append({
                "host": str(rdata.exchange).rstrip(".").lower(),
                "priority": int(rdata.preference)
            })
        mx_list.sort(key=lambda x: x["priority"])
        return mx_list
    except Exception:
        return []
```

#### 4. CAA Record Querying (`_query_caa`)

Certificate Authority Authorization record parsing:

- **Tag Extraction**: Extracts CAA tags (issue, issuewild, iodef)
- **Value Extraction**: Extracts CAA values
- **Return**: List of CAA records with tag and value

```python
def _query_caa(self, domain, timeout):
    try:
        resolver = self._get_resolver(timeout)
        answers = resolver.resolve(domain, 'CAA')
        caa_list = []
        for rdata in answers:
            caa_list.append({
                "tag": rdata.tag,
                "value": rdata.value
            })
        return caa_list
    except Exception:
        return []
```

#### 5. Security Record Analysis

##### SPF Analysis (`_analyze_spf`)

Parses SPF records for email infrastructure:

- **Include Detection**: Identifies included SPF policies
- **Mechanism Parsing**: Extracts ip4, ip6, a, mx, include mechanisms
- **All Policy**: Detects ~all, -all, +all policies
- **Return**: Structured SPF analysis

##### DMARC Analysis (`_analyze_dmarc`)

Parses DMARC records for email authentication:

- **Policy Extraction**: p=none, p=quarantine, p=reject
- **Reporting**: Extracts rua and ruf reporting addresses
- **Percentage**: Extracts sp= percentage for gradual enforcement
- **Return**: Structured DMARC analysis

##### DKIM Analysis (`_analyze_dkim`)

DKIM selector discovery:

- **Selector Discovery**: Attempts common selectors (default, google, k1, etc.)
- **TXT Query**: Queries _domainkey.{selector}.{domain}
- **Return**: List of discovered DKIM selectors

## Data Flow

```
Input: domain
    ↓
_get_resolver()
    ↓
_query_record() for A, AAAA, NS, TXT, CAA
_query_mx() for MX records
    ↓
_analyze_spf() + _analyze_dmarc() + _analyze_dkim()
    ↓
Structured DNS Intelligence
    ↓
ContextManager.add_dns_record()
    ↓
Standardized Payload
```

## Context Integration

### DNS Data Storage

DNS records are stored in `context.data["dns_records"]`:

```python
{
    "example.com": {
        "a": ["192.168.1.1", "192.168.1.2"],
        "aaaa": ["2001:db8::1"],
        "mx": [
            {"host": "mail.example.com", "priority": 10},
            {"host": "mail2.example.com", "priority": 20}
        ],
        "ns": ["ns1.example.com", "ns2.example.com"],
        "txt": ["v=spf1 include:_spf.google.com ~all"],
        "caa": [{"tag": "issue", "value": "letsencrypt.org"}],
        "spf": {
            "record": "v=spf1 include:_spf.google.com ~all",
            "includes": ["_spf.google.com"],
            "all_policy": "~all",
            "mechanisms": ["include:_spf.google.com", "~all"]
        },
        "dmarc": {
            "record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
            "policy": "quarantine",
            "reporting": ["dmarc@example.com"],
            "percentage": 100
        },
        "dkim": ["default", "google"]
    }
}
```

### Relationships Added

- **Domain to IP**: `resolves_to` relation (A/AAAA records)
- **Domain to MX**: `has_mx_server` relation
- **Domain to NS**: `has_nameserver` relation
- **Domain to CAA**: `has_caa_policy` relation

### Notes Added

- SPF policy notes with severity based on all policy
- DMARC policy notes with severity based on enforcement level
- Missing security record warnings
- CAA policy notes

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

### DNS Resolution Errors

- **NXDOMAIN**: Returns empty results for non-existent domains
- **Timeout**: Returns empty results for slow/unresponsive DNS servers
- **NoNameservers**: Returns empty results if all nameservers fail
- **Network Errors**: Returns empty results on network failures

### Record-Specific Errors

- **NoAnswer**: Returns empty list for missing record types
- **Invalid Records**: Skips malformed records
- **Parse Errors**: Continues with successfully parsed records

## Nexus Integration

### Email Infrastructure Profiling

Nexus Engine uses DNS intelligence for email leak profiling:

```python
# RULE 8: Email Leak Profiling
for domain, dns_data in context.data["dns_records"].items():
    mx_hosts = [mx["host"] for mx in dns_data.get("mx", [])]
    spf_includes = dns_data.get("spf", {}).get("includes", [])
    
    # Correlate MX hosts with known providers
    for mx_host in mx_hosts:
        if "google.com" in mx_host:
            context.add_derived_relation(
                src_type="domain", src_value=domain,
                relation="uses_google_workspace",
                dst_type="provider", dst_value="Google Workspace",
                evidence=f"MX host {mx_host} detected",
                confidence=0.9
            )
```

### Admiralty Scoring

DNS intelligence has high source reliability (A) due to authoritative DNS servers:

```python
EvidenceType.DNS_RECORD = {
    "base_weight": 15,
    "source_reliability": SourceReliability.A,  # Authoritative DNS
    "info_reliability": InformationReliability.RELIABLE
}
```

## Output Format

### Success Payload

```json
{
  "module": "dns",
  "target": "example.com",
  "status": "success",
  "data": {
    "domain": "example.com",
    "a": ["192.168.1.1"],
    "aaaa": ["2001:db8::1"],
    "mx": [
      {"host": "mail.example.com", "priority": 10}
    ],
    "ns": ["ns1.example.com"],
    "txt": ["v=spf1 include:_spf.google.com ~all"],
    "caa": [{"tag": "issue", "value": "letsencrypt.org"}],
    "spf": {
      "record": "v=spf1 include:_spf.google.com ~all",
      "includes": ["_spf.google.com"],
      "all_policy": "~all",
      "mechanisms": ["include:_spf.google.com", "~all"]
    },
    "dmarc": {
      "record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
      "policy": "quarantine",
      "reporting": ["dmarc@example.com"],
      "percentage": 100
    },
    "dkim": ["default", "google"]
  },
  "notes": [
    {
      "text": "SPF policy: ~all (soft fail)",
      "source": "dns_intel",
      "severity": "info",
      "confidence": 1.0
    }
  ],
  "relationships": [
    {
      "src": {"type": "domain", "value": "example.com"},
      "relation": "resolves_to",
      "dst": {"type": "ip", "value": "192.168.1.1"},
      "evidence": "A record",
      "confidence": 1.0
    }
  ]
}
```

### Error Payload

```json
{
  "module": "dns",
  "target": "example.com",
  "status": "error",
  "error": "DNS resolution timeout",
  "notes": [],
  "relationships": []
}
```

## Performance Considerations

- **Resolver Configuration**: Public DNS servers may have rate limits
- **Query Parallelization**: Sequential queries for different record types
- **Timeout Handling**: Each query respects timeout independently
- **Caching**: No local caching - relies on resolver cache

## Security Considerations

- **DNS Privacy**: Queries are sent to public DNS servers (Google, Cloudflare)
- **Data Exposure**: DNS records are public information
- **Spoofing Risk**: DNS responses are not cryptographically verified
- **Rate Limiting**: Public DNS servers may rate-limit queries

## Future Enhancements

- **DNSSEC Validation**: Verify DNSSEC signatures
- **DNS over HTTPS**: Support DoH for privacy
- **DNS over TLS**: Support DoT for privacy
- **Passive DNS**: Query passive DNS databases for historical records
- **Zone Transfer**: Attempt AXFR for zone enumeration (if allowed)
