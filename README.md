# Corvus Corax

Corvus Corax is a modular reconnaissance and analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture, creating a unified intelligence flow.

**See the unseen systems.**

---

## Current Version

**v0.5 - Framework Stabilization & Nexus Foundation (Unified Intelligence Flow)**

v0.5 stabilizes the modular framework, standardizes all reconnaissance outputs, implements a single unified presentation layer (`OutputManager`), and embeds a robust entity-relationship zeka flow into `ContextManager` to serve as a complete foundation for future Nexus multi-context correlation engines.

---

## Unified Intelligence Flow (v0.5 Core Philosophy)

With v0.5, Corvus Corax transitions from a simple command-line recon toolset into a **unified intelligence framework**:

```
                       [ Module Executions ]
                                 │
                   (Generates Standardized Payload)
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
[ OutputManager ]                               [ ContextManager ]
(Single Presentation)                           (Centralized Mind)
  │                                               │
  ├─► Render formatted terminal output            ├─► Map IPs / Domains
  ├─► Summarize discoveries                       ├─► Record Notes w/ Confidence
  └─► Display local Notes & Nexus Relations       └─► Graph Varlık Relationships
```

---

## What's New in v0.5

*   **Universal Module Standardization:**
    *   All 10 modules subclass `BaseModule` and run via the strict `execute()` cycle.
    *   **`geoip.py`** has been completely standardized, removing raw dictionaries and utilizing standard wrapper classes.
    *   No direct `print()` statements exist inside module execution logic; all output is returned as data payloads.

*   **Unified Output Schema:**
    *   Every single module now returns a predictable JSON structure for both success and error events.
    *   Includes target details, timestamping, local note structures, and dynamic relationship logs.

*   **OutputManager Rewrite (Single Presentation Layer):**
    *   Acts as the central renderer and formatter.
    *   Formats console data beautifully and uniquely based on the active module (ports, subdomains, tech details, crawls, whois records).
    *   Ensures Windows-safe execution by removing decorative unicode emojis (preventing `UnicodeEncodeError` on Turkish cp1254 consoles).
    *   Prints local module notes and relationship links directly in real-time under each execution banner.

*   **Nexus-Ready Context Manager Enhancements:**
    *   Both structural `notes` and entity `relations` inside the central zeka database now support the `confidence` float parameter (default `1.0`).
    *   Timestamp support has been standardized to ISO-8601 UTC.
    *   `merge_context()` has been upgraded to support both `"relations"` and `"relationships"` payload formats during context merges.
    *   **100% Modül Entegrasyonu:** Every single active module (including `netscan` and `geoip`) actively populates the context graph with semantic relationships (e.g., `located_in`, `has_active_host`, `uses_server`, `has_open_port`).

---

## Standard Output Schema (v0.5 Core Contract)

All modules return normalized JSON-style payloads:

```json
{
  "module": "scan",
  "target": "192.168.1.10",
  "status": "success",
  "data": {
    "ip": "192.168.1.10",
    "mode": "normal",
    "open_ports": [
      {"port": 22, "service": "SSH"},
      {"port": 80, "service": "HTTP"}
    ]
  },
  "notes": [
    {
      "text": "Port 22 (SSH) discovered open on 192.168.1.10",
      "source": "scan",
      "severity": "info",
      "confidence": 1.0,
      "timestamp": "2026-05-24T17:15:00.000000+00:00"
    }
  ],
  "relationships": [
    {
      "src": {"type": "ip", "value": "192.168.1.10"},
      "relation": "has_open_port",
      "dst": {"type": "port", "value": "22/SSH"},
      "evidence": "port scan",
      "confidence": 1.0,
      "timestamp": "2026-05-24T17:15:00.000000+00:00"
    }
  ],
  "timestamp": "2026-05-24T17:15:00.000000+00:00"
}
```

Error form:

```json
{
  "module": "geoip",
  "target": "invalid-ip",
  "status": "error",
  "error": "Lookup failed",
  "notes": [],
  "relationships": [],
  "timestamp": "2026-05-24T17:15:00.000000+00:00"
}
```

---

## Context Structure (Nexus-Ready Ontoloji)

```json
{
  "ips": {
    "8.8.8.8": {
      "ports": [],
      "geo": {
        "country": "United States",
        "region": "California",
        "city": "Mountain View",
        "isp": "Google LLC",
        "org": "Google LLC",
        "lat": 37.4223,
        "lon": -122.084
      },
      "hostname": "dns.google"
    }
  },
  "domains": {
    "dns.google": {
      "ips": ["8.8.8.8"]
    }
  },
  "notes": [
    {
      "text": "GeoIP intelligence gathered for 8.8.8.8: located in Mountain View, United States",
      "source": "geoip",
      "severity": "info",
      "confidence": 1.0,
      "timestamp": "2026-05-24T17:15:00.000000+00:00"
    }
  ],
  "relations": [
    {
      "src": {"type": "ip", "value": "8.8.8.8"},
      "relation": "located_in",
      "dst": {"type": "location", "value": "Mountain View, California, United States"},
      "evidence": "geoip lookup",
      "confidence": 1.0,
      "timestamp": "2026-05-24T17:15:00.000000+00:00"
    }
  ],
  "meta": {
    "created_at": "...",
    "updated_at": "...",
    "event_count": 5,
    "recent_events": ["ip_added:8.8.8.8", "geo_updated:8.8.8.8", "note_added:geoip"]
  }
}
```

---

## Configuration

Default runtime config lives in `config/config.json`:

```json
{
  "log_level": "INFO",
  "threads": 20,
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.3 (+https://github.com/corvus-corax/project)",
  "output_mode": "text",
  "scan_defaults": {
    "connect_timeout": 1.0,
    "banner_timeout": 2.0,
    "host_probe_ports": [80, 22],
    "host_probe_timeout": 0.3,
    "slow_scan_delay": 0.3,
    "normal_port_range": [1, 1024],
    "max_threads": 200
  }
}
```

---

## Usage

```bash
corvus > help
corvus > version
corvus > scan 192.168.1.10 normal 1 1024
corvus > netscan 192.168.1.0/24
corvus > geoip 8.8.8.8
corvus > footprint example.com
corvus > whois example.com
corvus > subdomain example.com
corvus > tech example.com
corvus > crawl example.com
corvus > context
```

---

## Roadmap

*   **Nexus Correlation Engine:** Active context graph queries and multi-source reasoning.
*   **Risk Scoring Layer:** Algorithmic vulnerability and footprint risk assessment.
*   **Structured Report Generation:** HTML/PDF intelligence reports.
*   **Interactive Analyst Layer:** LLM-guided threat reasoning.

---

## Disclaimer

This project is for educational and authorized security research purposes only. Unauthorized use is strictly prohibited.
