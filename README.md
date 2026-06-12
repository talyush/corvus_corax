# Corvus Corax

Corvus Corax is a modular reconnaissance and analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture, creating a unified intelligence flow.

**See the unseen systems.**

---

## Current Version

**v0.6.1 - Nexus Core & Optimized Scanning**

v0.6.1 optimizes the framework's active scanning capabilities by introducing multi-threaded parallel execution (`ThreadPoolExecutor`) and a predefined Top Ports scan list. Version numbers across modules, CLI banners, and help systems have been updated to `v0.6.1-nexus-core`.

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

## What's New in v0.6.1 (Optimized Scanning)

*   **Multi-threaded Port Scanning (`modules/scan.py`):**
    *   **High-speed Parallel Scanning:** Implements Python's `ThreadPoolExecutor` to execute port probes concurrently.
    *   **Predefined Top Ports (`TOP_PORTS`):** Added a standard list of 20+ common security services.
    *   **Default Quick Scan (`scan <ip>`):** Running `scan` without a range now defaults to scanning `TOP_PORTS` concurrently (finishing in ~1 second).
    *   **Stealth Slow Mode Preservation:** Sequential scanning with configurable delays remains fully supported in `slow` mode to bypass rate limiters.

*   **Documentation & Usability Improvements:**
    *   **Help Commands:** Integrated `nexus` and `nexus analyze` into the CLI help output.
    *   **Version Alignments:** Standardized the command line banners and query outputs.

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
corvus > scan 192.168.1.10
corvus > scan 192.168.1.10 normal 1 1024
corvus > scan 192.168.1.10 slow 1 100
corvus > netscan 192.168.1.0/24
corvus > geoip 8.8.8.8
corvus > footprint example.com
corvus > whois example.com
corvus > subdomain example.com
corvus > tech example.com
corvus > crawl example.com
corvus > context
corvus > nexus
corvus > nexus analyze
```

---

## Roadmap

*   **Structured Report Generation:** HTML/PDF intelligence reports and visual dossier export.
*   **Interactive Analyst Layer:** LLM-guided threat reasoning and natural language context queries.
*   **Dynamic Visualizer Graph:** Interactive network relationship visualizer graph.

---

## Disclaimer

This project is for educational and authorized security research purposes only. Unauthorized use is strictly prohibited.
