# Context Manager Documentation

**Module**: `core/context.py`  
**Version**: v0.9  
**Purpose**: Centralized intelligence graph management and query interface

## Overview

The `ContextManager` is the core intelligence graph component of Corvus Corax. It maintains a centralized, normalized data structure that stores all reconnaissance data collected by modules, provides query interfaces for analysis, and serves as the single source of truth for the Nexus Engine and Exporter.

## Architecture

### Class Structure

```python
class ContextManager:
    def __init__(self):
        self.data = {
            # v0.9: Entity-agnostic registry
            "entities": {},   # "{type}:{value}" -> {"type", "value", "properties", "created_at", "updated_at"}
            "events": [],     # Temporal event store (POL basis)
            
            # Legacy (backward compatible)
            "ips": {},
            "domains": {},
            "certificates": {},
            "dns_records": {},
            "http_headers": {},
            "email_intel": {},
            "metadata_intel": {},
            "asn_intel": {},
            "tech_intel": {},
            "notes": [],
            "relations": [],
            "derived_relations": [],
            "meta": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "event_count": 0,
                "recent_events": []
            }
        }
```

### Design Principles

1. **Single Source of Truth**: All intelligence data flows through ContextManager
2. **Normalization**: Consistent data structures across all modules
3. **Event Tracking**: All data changes are logged as events
4. **Query Interface**: Standardized methods for data retrieval
5. **Nexus Compatibility**: Clean data interface for correlation engine
6. **Entity-Agnostic**: All entity types (ip, domain, person, org, phone, email, wallet) in unified registry (v0.9)
7. **Temporal Events**: Timestamped events for Pattern of Life analysis (v0.9)

## v0.9 Additions

### Entity Registry (`entities`)

Unified entity-agnostic registry for all entity types:

```python
{
    "person:ahmet": {
        "type": "person",
        "value": "ahmet",
        "properties": {"job": "engineer"},
        "created_at": "2026-08-12T00:00:00Z",
        "updated_at": "2026-08-12T00:00:00Z"
    },
    "phone:+905321234567": {
        "type": "phone",
        "value": "+905321234567",
        "properties": {"number_type": "mobile", "operator": {...}},
        "created_at": "...",
        "updated_at": "..."
    },
    "wallet:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa": {
        "type": "wallet",
        "value": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "properties": {"chain": "btc"},
        "created_at": "...",
        "updated_at": "..."
    }
}
```

**Supported entity types** (v0.9):
- `ip`, `domain` — legacy
- `person`, `organization` — human-centric
- `phone`, `email`, `social_profile`, `username` — contact
- `wallet`, `location`, `certificate`, `publication`, `identity` — assets

### Temporal Event Store (`events`)

Timestamped events for Pattern of Life analysis:

```python
[
    {
        "timestamp": "2026-08-12T00:00:00+00:00",
        "entity": "person:ahmet",
        "action": "located_in",
        "source": "geoip",
        "location": "Istanbul, Turkey",
        "metadata": {"lat": 41.01, "lon": 28.98}
    }
]
```

**Event actions**: `located_in`, `traveled`, `phone_analyzed`, `profile_found`, `breach_found`, `publication_found`, `wallet_identified`, `org_identified`, etc.

### v0.9 API Methods

```python
# Entity-agnostic
def add_entity(self, entity_type, value, properties=None):
    """Add or update any entity type."""
def get_entity(self, entity_type, value):
    """Get specific entity."""
def query_entities(self, entity_type=None, search=None):
    """Query entities by type and/or search text."""

# Typed helpers
def add_person(self, name, properties=None):
def add_organization(self, name, properties=None):
def add_phone(self, number, properties=None):
def add_email(self, email, properties=None):
def add_social_profile(self, platform, handle, properties=None):
def add_wallet(self, address, chain="btc", properties=None):
def add_location(self, lat, lon, label=None, properties=None):

# Temporal events
def add_event(self, entity, action, source="system", location=None, metadata=None):
    """Add timestamped event for POL analysis."""
def query_events(self, entity=None, action=None, entity_type=None, time_range=None):
    """Query temporal events."""
def get_entity_events(self, entity, limit=100):
    """Get all events for a specific entity."""

# Views
def get_events_summary(self, entity=None, limit=50):
    """Human-readable event stream."""
def get_entities_summary(self, entity_type=None):
    """Human-readable entity registry."""
```

## Data Structure

### Core Data Types

#### 1. IP Addresses (`ips`)

```python
{
    "192.168.1.100": {
        "ports": [
            {"port": 22, "service": "SSH"},
            {"port": 80, "service": "HTTP"}
        ],
        "geo": {
            "country": "United States",
            "city": "Mountain View",
            "isp": "Google LLC",
            "lat": 37.4223,
            "lon": -122.085
        },
        "hostname": "dns.google"
    }
}
```

**Fields**:
- `ports`: List of open ports with service detection
- `geo`: Geolocation data from GeoIP module
- `hostname`: Reverse DNS hostname

#### 2. Domains (`domains`)

```python
{
    "example.com": {
        "ips": ["192.168.1.100", "192.168.1.101"]
    }
}
```

**Fields**:
- `ips`: List of IP addresses the domain resolves to

#### 3. Certificates (`certificates`)

```python
{
    "a1b2c3d4e5f6...": {
        "fingerprint": "a1b2c3d4e5f6...",
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

**Fields**:
- `fingerprint`: SHA-256 certificate fingerprint
- `issuer`: Certificate issuer information
- `subject`: Certificate subject information
- `san`: Subject Alternative Names
- `wildcards`: Wildcard SAN entries
- `not_before`: Certificate validity start
- `not_after`: Certificate validity end
- `hosts`: List of hosts using this certificate

#### 4. DNS Records (`dns_records`)

```python
{
    "example.com": {
        "a": ["192.168.1.100", "192.168.1.101"],
        "aaaa": ["2001:db8::1"],
        "mx": [
            {"host": "mail.example.com", "priority": 10}
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

**Fields**:
- `a`: A records (IPv4 addresses)
- `aaaa`: AAAA records (IPv6 addresses)
- `mx`: MX records (mail servers)
- `ns`: NS records (nameservers)
- `txt`: TXT records
- `caa`: CAA records (certificate authorities)
- `spf`: SPF record analysis
- `dmarc`: DMARC record analysis
- `dkim`: DKIM selectors

#### 5. HTTP Headers (`http_headers`)

```python
{
    "example.com": {
        "server": "nginx/1.18.0",
        "security_headers": {
            "csp": {
                "present": true,
                "policy": "default-src 'self'",
                "unsafe_inline": false
            },
            "hsts": {
                "present": true,
                "max_age": 31536000,
                "include_subdomains": true
            },
            "x_frame_options": {
                "present": true,
                "directive": "SAMEORIGIN"
            }
        },
        "cors": {
            "allow_origin": "*",
            "allow_methods": ["GET", "POST"],
            "allow_credentials": false,
            "wildcard_origin": true
        },
        "cookies": [
            {
                "name": "sessionid",
                "httponly": true,
                "secure": true,
                "samesite": "Lax"
            }
        ],
        "waf_cdn": ["Cloudflare"],
        "tech_stack": ["nginx"]
    }
}
```

**Fields**:
- `server`: Server header value
- `security_headers`: Security header analysis
- `cors`: CORS policy analysis
- `cookies`: Cookie security analysis
- `waf_cdn`: Detected WAF/CDN services
- `tech_stack`: Detected technologies

#### 6. Email Intelligence (`email_intel`)

```python
{
    "example.com": {
        "provider": "Google Workspace",
        "mx_hosts": ["alt1.aspmx.l.google.com"],
        "spf_record": "v=spf1 include:_spf.google.com ~all",
        "dmarc_record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com",
        "reporting_addresses": ["dmarc@example.com"],
        "detected_pattern": "first.last",
        "likely_formats": [
            "first.last@example.com",
            "info@example.com"
        ],
        "role_aliases": ["admin", "support", "info"],
        "sample_emails": ["john.doe@example.com"]
    }
}
```

**Fields**:
- `provider`: Identified email provider
- `mx_hosts`: MX host list
- `spf_record`: SPF record
- `dmarc_record`: DMARC record
- `reporting_addresses`: DMARC reporting addresses
- `detected_pattern`: Email naming pattern
- `likely_formats`: Likely email formats
- `role_aliases`: Role-based aliases
- `sample_emails`: Sample email addresses

#### 7. Metadata Intelligence (`metadata_intel`)

```python
{
    "example.com": {
        "robots": {
            "present": true,
            "directives": [
                {"type": "user-agent", "value": "*"},
                {"type": "disallow", "value": "/admin"}
            ],
            "sitemaps": ["https://example.com/sitemap.xml"]
        },
        "sitemap": {
            "present": true,
            "urls": [
                {
                    "loc": "https://example.com/page1",
                    "priority": "0.8"
                }
            ]
        },
        "favicon_hash": 1234567890,
        "security": {
            "present": true,
            "contact": "mailto:security@example.com"
        },
        "generator": "WordPress 6.1.3"
    }
}
```

**Fields**:
- `robots`: Robots.txt analysis
- `sitemap`: Sitemap.xml analysis
- `favicon_hash`: MurmurHash3 favicon hash
- `security`: Security.txt analysis
- `generator`: Generator meta tag

#### 8. ASN Intelligence (`asn_intel`)

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
            "192.168.1.2"
        ]
    }
}
```

**Fields**:
- `ip`: IP address
- `asn`: ASN string
- `as_number`: ASN number
- `organization`: Organization name
- `country`: Country name
- `country_code`: Country code
- `isp`: ISP name
- `cidr`: CIDR block
- `related_ips`: Related IPs in CIDR

#### 9. Technology Intelligence (`tech_intel`)

```python
{
    "example.com": {
        "server": "nginx/1.18.0",
        "runtime": "PHP 8.1",
        "cms": [
            {"name": "WordPress", "version": "6.1.3"}
        ],
        "frameworks": [
            {"name": "jQuery", "version": "3.6.0"}
        ],
        "javascript": [
            {"name": "React", "version": "18.2.0"}
        ],
        "waf_cdn": [
            {"name": "Cloudflare", "evidence": "CF-Ray header"}
        ],
        "stack_profile": "nginx+php+wordpress"
    }
}
```

**Fields**:
- `server`: Server software
- `runtime`: Runtime environment
- `cms`: Detected CMS
- `frameworks`: Detected frameworks
- `javascript`: Detected JavaScript libraries
- `waf_cdn`: Detected WAF/CDN
- `stack_profile`: Normalized stack profile

### Notes (`notes`)

```python
[
    {
        "text": "Outdated nginx version detected",
        "source": "tech_detect",
        "severity": "high",
        "confidence": 0.9,
        "timestamp": "2024-01-01T00:00:00Z"
    }
]
```

**Fields**:
- `text`: Note text
- `source`: Module that created the note
- `severity`: Severity level (info, low, medium, high, critical)
- `confidence`: Confidence score (0.0-1.0)
- `timestamp`: ISO-8601 timestamp

### Relations (`relations`)

```python
[
    {
        "src": {"type": "domain", "value": "example.com"},
        "relation": "resolves_to",
        "dst": {"type": "ip", "value": "192.168.1.100"},
        "evidence": "A record",
        "confidence": 1.0,
        "timestamp": "2024-01-01T00:00:00Z"
    }
]
```

**Fields**:
- `src`: Source entity (type, value)
- `relation`: Relationship type
- `dst`: Destination entity (type, value)
- `evidence`: Evidence description
- `confidence`: Confidence score (0.0-1.0)
- `timestamp`: ISO-8601 timestamp

### Derived Relations (`derived_relations`)

Same structure as `relations`, but created by Nexus Engine through correlation rules.

### Metadata (`meta`)

```python
{
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "event_count": 150,
    "recent_events": [
        "ip_added:192.168.1.100",
        "geo_updated:192.168.1.100",
        "domain_mapped:example.com->192.168.1.100"
    ]
}
```

**Fields**:
- `created_at`: Context creation timestamp
- `updated_at`: Last update timestamp
- `event_count`: Total event count
- `recent_events`: Recent event list (max 50)

## API Methods

### Data Addition Methods

#### IP Management

```python
def add_ip(self, ip):
    """Add IP address to context."""
    
def add_port(self, ip, port, service="Unknown"):
    """Add port to IP address."""
    
def add_geo(self, ip, geo_data):
    """Add geolocation data to IP address."""
```

#### Domain Management

```python
def add_domain_mapping(self, domain, ip):
    """Map domain to IP address."""
```

#### Certificate Management

```python
def add_certificate(self, host, fingerprint, cert_data):
    """Add certificate to context."""
```

#### DNS Management

```python
def add_dns_record(self, domain, dns_data):
    """Add DNS records to context."""
```

#### HTTP Header Management

```python
def add_http_headers(self, domain, headers_data):
    """Add HTTP headers to context."""
```

#### Email Intelligence

```python
def add_email_intel(self, domain, email_data):
    """Add email intelligence to context."""
```

#### Metadata Management

```python
def add_metadata_intel(self, domain, metadata_data):
    """Add metadata intelligence to context."""
```

#### ASN Intelligence

```python
def add_asn_intel(self, ip, asn_data):
    """Add ASN intelligence to context."""
```

#### Technology Intelligence

```python
def add_tech_intel(self, domain, tech_data):
    """Add technology intelligence to context."""
```

### Note and Relation Methods

```python
def add_note(self, text, source="system", severity="info", confidence=1.0):
    """Add structured note to context."""
    
def add_relation(self, src_type, src_value, relation, dst_type, dst_value, 
                 evidence=None, confidence=1.0):
    """Add entity relation to context."""
    
def add_derived_relation(self, src_type, src_value, relation, dst_type, dst_value,
                        evidence=None, confidence=1.0):
    """Add derived relation (from Nexus Engine) to context."""
```

### Query Methods

```python
def get_clean_data(self):
    """Return cleaned data suitable for Nexus Engine."""
    
def get_ip(self, ip):
    """Get IP data."""
    
def get_domain(self, domain):
    """Get domain data."""
    
def get_relations(self, entity_type=None, entity_value=None):
    """Get relations matching criteria."""
    
def get_notes(self, severity=None, source=None):
    """Get notes matching criteria."""
```

### Admiralty Intelligence Methods

```python
def get_admiralty_summary(self):
    """Return Admiralty intelligence summary for all entities."""
    
def get_entity_admiralty(self, entity):
    """Return detailed Admiralty evidence chain for specific entity."""
```

### Utility Methods

```python
def merge_context(self, other_context):
    """Merge another context into this one."""
    
def clear(self):
    """Clear all context data."""
    
def get_stats(self):
    """Return context statistics."""
```

## Event System

### Event Types

Events are generated for all data modifications:

- `ip_added:{ip}`: IP address added
- `port_added:{ip}:{port}/{service}`: Port added to IP
- `geo_updated:{ip}`: Geolocation data updated
- `domain_mapped:{domain}->{ip}`: Domain mapped to IP
- `certificate_added:{fingerprint}@{host}`: Certificate added
- `dns_record_added:{domain}`: DNS records added
- `http_headers_added:{domain}`: HTTP headers added
- `email_intel_added:{domain}`: Email intelligence added
- `metadata_intel_added:{domain}`: Metadata intelligence added
- `asn_intel_added:{ip}`: ASN intelligence added
- `tech_intel_added:{domain}`: Technology intelligence added
- `note_added:{source}`: Note added
- `relation_added:{src_type}->{dst_type}:{relation}`: Relation added
- `derived_relation_added:{src_type}->{dst_type}:{relation}`: Derived relation added

### Event Tracking

```python
def _touch(self, event=None):
    """Update metadata and track event."""
    if event:
        self.data["meta"]["recent_events"].append(event)
        if len(self.data["meta"]["recent_events"]) > 50:
            self.data["meta"]["recent_events"].pop(0)
    
    self.data["meta"]["event_count"] += 1
    self.data["meta"]["updated_at"] = datetime.now().isoformat()
```

## Nexus Integration

### Clean Data Interface

Nexus Engine requires cleaned data without metadata:

```python
def get_clean_data(self):
    """
    Return cleaned data suitable for Nexus Engine.
    Removes meta field and normalizes data structures.
    """
    clean = {
        "ips": self.data["ips"],
        "domains": self.data["domains"],
        "certificates": self.data["certificates"],
        "dns_records": self.data["dns_records"],
        "http_headers": self.data["http_headers"],
        "email_intel": self.data["email_intel"],
        "metadata_intel": self.data["metadata_intel"],
        "asn_intel": self.data["asn_intel"],
        "tech_intel": self.data["tech_intel"],
        "notes": self.data["notes"],
        "relations": self.data["relations"],
        "derived_relations": self.data["derived_relations"]
    }
    return clean
```

### Derived Relations

Nexus Engine adds derived relations through `add_derived_relation()`:

```python
# Nexus Engine usage
context.add_derived_relation(
    src_type="domain", src_value="example.com",
    relation="shares_certificate",
    dst_type="domain", dst_value="another.com",
    evidence="Both domains use certificate with fingerprint a1b2c3...",
    confidence=0.95
)
```

## Admiralty Integration

### Admiralty Summary

Provides high-level Admiralty intelligence:

```python
def get_admiralty_summary(self):
    """
    Returns Admiralty intelligence summary.
    """
    summary = {
        "total_entities": 0,
        "high_confidence": 0,  # A1, B2
        "medium_confidence": 0,  # C3, D4
        "low_confidence": 0,  # E5, F6
        "entities": []
    }
    
    # Calculate from risk profiles
    for ip in self.data["ips"]:
        summary["total_entities"] += 1
        # Add entity details with Admiralty rating
    
    for domain in self.data["domains"]:
        summary["total_entities"] += 1
        # Add entity details with Admiralty rating
    
    return summary
```

### Entity-Specific Admiralty

Provides detailed evidence chain for specific entity:

```python
def get_entity_admiralty(self, entity):
    """
    Returns detailed Admiralty evidence chain for entity.
    """
    # Look up entity in risk profiles
    # Return evidence chain with Admiralty codes
    return {
        "entity": entity,
        "admiralty_rating": "B2",
        "risk_score": 75,
        "evidence_chain": [...]
    }
```

## Performance Considerations

### Memory Usage

- **Data Growth**: Context grows with reconnaissance data
- **Memory Management**: Consider clearing old data for large scans
- **Event Buffer**: Recent events limited to 50 entries

### Query Performance

- **Direct Access**: O(1) for direct key lookups
- **Relation Queries**: O(n) for relation filtering
- **Note Queries**: O(n) for note filtering

### Concurrency

- **Thread Safety**: Not thread-safe by default
- **Locking**: Add locks if using in multi-threaded environment
- **Atomic Operations**: Individual operations are atomic

## Best Practices

### 1. Data Normalization

Always use provided methods instead of direct data access:

```python
# Good
context.add_ip("192.168.1.100")

# Bad
context.data["ips"]["192.168.1.100"] = {}
```

### 2. Event Tracking

Let ContextManager handle event tracking automatically:

```python
# Automatic event tracking
context.add_ip("192.168.1.100")  # Generates ip_added event
```

### 3. Relation Consistency

Use consistent entity types and values:

```python
# Good
context.add_relation("domain", "example.com", "resolves_to", "ip", "192.168.1.100")

# Bad
context.add_relation("domain", "example.com", "resolves_to", "address", "192.168.1.100")
```

### 4. Confidence Scoring

Use appropriate confidence scores (0.0-1.0):

```python
# High confidence (direct observation)
context.add_relation(..., confidence=1.0)

# Medium confidence (correlation)
context.add_relation(..., confidence=0.7)

# Low confidence (inference)
context.add_relation(..., confidence=0.5)
```

### 5. Note Severity

Use appropriate severity levels:

```python
context.add_note(..., severity="info")      # Informational
context.add_note(..., severity="low")       # Low risk
context.add_note(..., severity="medium")    # Medium risk
context.add_note(..., severity="high")      # High risk
context.add_note(..., severity="critical")  # Critical risk
```

## Error Handling

### Invalid Input

Methods handle invalid input gracefully:

```python
# Invalid IP - ignored
context.add_ip("invalid_ip")

# Invalid domain - ignored
context.add_domain_mapping("invalid", "192.168.1.100")
```

### Missing Data

Query methods return None for missing data:

```python
# Missing IP
ip_data = context.get_ip("192.168.1.999")  # Returns None

# Missing domain
domain_data = context.get_domain("missing.com")  # Returns None
```

### Type Safety

Methods enforce type safety where possible:

```python
# Invalid confidence - clamped to [0.0, 1.0]
context.add_note(..., confidence=2.0)  # Clamped to 1.0
context.add_note(..., confidence=-1.0)  # Clamped to 0.0
```

## Future Enhancements

### 1. Persistence Layer

Already implemented in v0.9 via `core/db.py` `IntelligenceVault` (JSONL append-only log + state.json).

- SQLite/PostgreSQL backend
- Automatic context persistence
- Query optimization
- Data retention policies

### 2. Query Language

- Custom query language for complex queries
- Graph traversal queries
- Pattern matching queries
- Aggregation queries

### 3. Validation Layer

- Schema validation
- Data type enforcement
- Constraint checking
- Data sanitization

### 4. Caching Layer

- Query result caching
- Intelligent cache invalidation
- Cache warming
- Cache statistics

### 5. Event System Enhancement

- Event subscriptions
- Event filtering
- Event replay
- Event export
