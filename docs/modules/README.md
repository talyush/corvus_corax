# Corvus Corax v0.9 — Modules Technical Documentation

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
- **Network Scan** (`netscan.py`) — Network/subnet scanning with `--ports`, `--geo`, `--map` flags (v0.9)
- **Footprint** (`footprint.py`) — Basic domain reconnaissance
- **GeoIP** (`geoip.py`) — Geolocation intelligence
- **WHOIS** (`whois_lookup.py`) — WHOIS data extraction
- **Subdomain Enumeration** (`subdomain_enum.py`) — Passive subdomain discovery
- **Technology Detection** (`tech_detect.py`) — Deep fingerprinting engine
- **Simple Crawler** (`simple_crawler.py`) — Web content extraction

### Human-Centric Intelligence Modules (v0.9)
- **Phone Intelligence** (`phone_intel.py`) — E.164 normalization, operator prefix detection (MNP warning), number type classification, candidate person linking
- **Social Intelligence** (`social_intel.py`) — Username OSINT across 12 platforms, correlation probability model
- **Organization Intelligence** (`org_intel.py`) — Domain ownership (candidate), personnel mapping, infrastructure correlation
- **Academic Intelligence** (`academic_intel.py`) — OpenAlex API, ORCID, publications, university detection
- **Wallet Intelligence** (`financial_intel.py`) — BTC/ETH/SOL validation, chain detection, live balance
- **Breach Intelligence** (`breach_intel.py`) — Firefox Monitor (no key), HIBP k-anonymity, manual sources. **Ethical: meta-data only.**
- **GitHub Intelligence** (`github_intel.py`) — Profile, repos, commit email correlation, secret scanning
- **Wayback Intelligence** (`wayback_intel.py`) — Snapshot history, CDX records, web history correlation

### Intelligence Deepening Modules (v0.9)
- **Entity Resolution** (`resolve.py`) — Identity clustering: finds all entities belonging to the same person
- **Cross-Entity Pivoting** (`pivot.py`) — BFS graph traversal: discovers entire infrastructure from a single entity
- **Pattern of Life** (`pol.py`) — Behavioral analysis: activity rhythm, movement, communications, anomaly detection

### Visualization Modules (v0.9)
- **GEOINT** (`geoint.py`) — Interactive map (Leaflet.js), D3.js graph, timeline, GeoJSON export

### Analysis Modules
- **Nexus** (`nexus.py`) — Correlation engine and risk scoring (Rule 1-20)
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

### v0.9 BaseModule Extensions

```python
# Entity-agnostic entity creation
self.add_entity("person", "ahmet", {"job": "engineer"})
self.add_person("ahmet")
self.add_phone("+905321234567")
self.add_email("ahmet@example.com")
self.add_social_profile("github", "ahmet_dev")
self.add_wallet("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "btc")
self.add_organization("Acme Corp")

# Temporal event logging (POL basis)
self.log_event("phone_analyzed", entity="phone:+905321234567", metadata={...})
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
- **Temporal Events**: Timestamped events for Pattern of Life analysis
- **Direct Data**: Domain-specific data structures (ips, domains, tech_intel, etc.)

## Data Flow

```
User Input → Module → ContextManager → OutputManager → Terminal/Export
                ↓
            Standardized Payload
                ↓
            Notes & Relationships
                ↓
            Temporal Events (POL)
                ↓
            Intelligence Vault (persistent)
```

## Three-Layer Architecture (v0.9)

```
1. Session Context (RAM)     — temporary, lost on session end
2. Intelligence Vault (Disk) — persistent, confirmed evidence (JSONL + index)
3. POL Engine (Analysis)     — reads from vault, extracts behavior patterns
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
3. **Integrate with ContextManager**: Add notes, relationships, and temporal events
4. **Use candidate/possible model**: For human-centric links, use confidence scores (not confirmed ownership)
5. **Log temporal events**: Every module should call `log_event()` for POL analysis
6. **Handle errors gracefully**: Return error payloads
7. **Log appropriately**: Use the provided logger
8. **Respect configuration**: Use config values for timeouts, threads, etc.
9. **Document thoroughly**: Add docstrings and comments