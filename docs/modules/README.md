# Corvus Corax v0.8 — Modules Technical Documentation

This directory contains detailed technical documentation for all Corvus Corax modules. Each module is documented with its architecture, data flow, integration points, and implementation details.

## Module Categories

### Core Intelligence Modules (v0.8)
- **Certificate Intelligence** (`cert_intel.py`) — TLS certificate analysis and fingerprinting
- **DNS Intelligence** (`dns_intel.py`) — DNS enumeration and security record analysis
- **HTTP Header Intelligence** (`http_headers.py`) — HTTP header extraction and security evaluation
- **Email Pattern Discovery** (`email_intel.py`) — Email infrastructure profiling
- **Metadata Collection** (`metadata_intel.py`) — Robots.txt, sitemap, favicon hash, security.txt
- **ASN Intelligence** (`asn.py`) — ASN lookup and network infrastructure profiling

### Reconnaissance Modules
- **Scan** (`scan.py`) — Port scanning with multi-threaded and stealth modes
- **Network Scan** (`netscan.py`) — Network/subnet scanning
- **Footprint** (`footprint.py`) — Basic domain reconnaissance
- **GeoIP** (`geoip.py`) — Geolocation intelligence
- **WHOIS** (`whois_lookup.py`) — WHOIS data extraction
- **Subdomain Enumeration** (`subdomain_enum.py`) — Passive subdomain discovery
- **Technology Detection** (`tech_detect.py`) — Deep fingerprinting engine
- **Simple Crawler** (`simple_crawler.py`) — Web content extraction

### Analysis Modules
- **Nexus** (`nexus.py`) — Correlation engine and risk scoring
- **Context** (via `main.py`) — Intelligence graph inspection

### Utility Modules
- **Help** (`help.py`) — Command reference
- **Version** (`version.py`) — Version information

## Module Architecture

All modules inherit from `BaseModule` (`core/module_base.py`) and follow a standardized interface:

```python
class BaseModule:
    name = "module_name"
    
    def __init__(self, target, config, logger, context):
        self.target = target
        self.config = config
        self.logger = logger
        self.context = context
    
    def execute(self):
        # Module implementation
        return self.success(target="...", data={...})
```

### Standardized Payload

All modules return normalized JSON payloads:

```json
{
  "module": "module_name",
  "target": "target_value",
  "status": "success|error",
  "data": { ... },
  "notes": [ ... ],
  "relationships": [ ... ],
  "timestamp": "ISO-8601"
}
```

### Context Integration

Modules integrate with the `ContextManager` through:

- **Notes**: Structured observations with confidence scores
- **Relationships**: Entity-to-entity connections with evidence
- **Direct Data**: Domain-specific data structures (ips, domains, tech_intel, etc.)

## Data Flow

```
User Input → Module → ContextManager → OutputManager → Terminal/Export
                ↓
            Standardized Payload
                ↓
            Notes & Relationships
```

## Module-Specific Documentation

See individual module documentation files for detailed implementation details:

- [Certificate Intelligence](./cert_intel.md)
- [DNS Intelligence](./dns_intel.md)
- [HTTP Header Intelligence](./http_headers.md)
- [Email Pattern Discovery](./email_intel.md)
- [Metadata Collection](./metadata_intel.md)
- [ASN Intelligence](./asn.md)
- [Port Scanning](./scan.md)
- [Technology Detection](./tech_detect.md)
- [Nexus Correlation Engine](./nexus.md)

## Module Development Guidelines

When creating new modules:

1. **Inherit from BaseModule**: Ensure consistent interface
2. **Use standardized payload**: Follow the JSON schema
3. **Integrate with ContextManager**: Add notes and relationships
4. **Handle errors gracefully**: Return error payloads
5. **Log appropriately**: Use the provided logger
6. **Respect configuration**: Use config values for timeouts, threads, etc.
7. **Document thoroughly**: Add docstrings and comments
