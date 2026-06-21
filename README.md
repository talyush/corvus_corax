# Corvus Corax

Corvus Corax is a modular reconnaissance and intelligence analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture, creating a unified intelligence flow — and now exporting it as interactive reports.

**See the unseen systems.**

---

## Current Version

**v0.7 — Nexus Intelligence**

v0.7 introduces the **Nexus Exporter Engine** (`core/exporter.py`): a full reporting layer that transforms the collected intelligence graph into a standalone interactive HTML dossier and a Neo4j-ready graph JSON schema. The terminal dashboard for `nexus` has also been redesigned with cleaner structured output and help has been fully updated with all subcommands.

---

## Architecture Overview

```
                     [ Module Executions ]
                               │
                 (Generates Standardized Payload)
                               │
         ┌─────────────────────┴──────────────────────┐
         ▼                                            ▼
[ OutputManager ]                           [ ContextManager ]
(Terminal Presentation)                     (Centralized Intelligence Graph)
  │                                           │
  ├─► Render formatted terminal output        ├─► Map IPs / Domains
  ├─► Summarize discoveries                   ├─► Record Notes w/ Confidence
  └─► Display Notes & Nexus alerts            └─► Graph Entity Relationships
                                                    │
                                             [ NexusEngine ]
                                             (Correlation & Risk Scoring)
                                                    │
                                             [ NexusExporter ]
                                             (HTML Dossier / Neo4j JSON)
```

---

## What's New in v0.7 (Nexus Intelligence)

### `core/exporter.py` — Intelligence Export Engine *(New)*

- **`export_html(filepath)`** — Generates a standalone, single-file interactive HTML intelligence dossier.
  - **Executive Summary** tab: Threat alerts, confidence scores, and audit event log.
  - **Risk Profiles** tab: Expandable entity cards with risk score progress bars and evidence chains.
  - **Graph Relations Explorer** tab: Searchable table of all raw and Nexus-inferred relationships.
  - Glassmorphism dark UI, Google Fonts, smooth tab transitions — no external dependencies.

- **`export_neo4j_json(filepath)`** — Exports the full intelligence graph as a Neo4j-ready JSON schema.
  - Nodes: `IP`, `Domain`, `Port`, `Location`, `Server`, `Tech`, etc.
  - Relationships: All raw recon relations + Nexus-inferred derived relations.
  - Ready for `LOAD CSV` or `APOC` import.

- **`generate_neo4j_data()`** — Transforms the `ContextManager` graph into a flat `{ nodes, relationships }` dictionary.

### `modules/nexus.py` — CLI Routing Extended

New subcommands added:

| Command | Description |
|---|---|
| `nexus` / `nexus analyze` | Run Nexus Correlation Engine, print terminal dashboard |
| `nexus export html [path]` | Export interactive HTML dossier (default: `logs/nexus_report.html`) |
| `nexus export json [path]` | Export Neo4j graph JSON (default: `logs/nexus_neo4j.json`) |

### `output/output_manager.py` — Redesigned Nexus Dashboard

- Aligned column layout with `#` bar charts for risk distribution.
- Separate terminal formatters for `analyze`, `export html`, and `export json` result types.
- Improved readability with structured section dividers.

### `modules/help.py` — Fully Updated

- All nexus subcommands (`nexus analyze`, `nexus export html`, `nexus export json`) documented.
- Notes section added explaining prerequisites and default export paths.
- Version header updated to v0.7.

---

## What's New in v0.6.1 (Optimized Scanning)

- **Multi-threaded Port Scanning:** `ThreadPoolExecutor` for concurrent port probes.
- **Predefined Top Ports (`TOP_PORTS`):** Default quick scan covers 20+ common security services, finishing in ~1 second.
- **Stealth Slow Mode:** Sequential scanning with configurable delays remains fully supported.

---

## Command Reference

```
================================================================================
  CORVUS CORAX v0.7 — NEXUS INTELLIGENCE  |  Modular Recon Framework
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               |                              | Show collected context
  scan                  | <ip> <mode> ...              | Port scan (normal/slow/banner/subnet)
  netscan               | <ip/network>                 | Scan a network/subnet
  footprint             | <domain>                     | Get IP and hostname info
  geoip                 | <ip>                         | Get geolocation info
  whois                 | <domain|ip>                  | Run WHOIS lookup
  subdomain             | <domain> [wordlist]          | Passive subdomain enum (crt.sh+wordlist)
  tech                  | <url_or_host>                | Detect server, framework & tech stack
  crawl                 | <url_or_host>                | Get title, links, forms & status code
  nexus                 | [analyze]                    | Run Nexus Correlation Engine
  nexus analyze         |                              | Correlate & score all collected data
  nexus export html     | [filepath]                   | Export HTML intelligence dossier
  nexus export json     | [filepath]                   | Export Neo4j-ready graph JSON
================================================================================
  Notes:
    - Nexus commands require prior data collection (scan, footprint, etc.)
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json
    - Use 'context' at any time to inspect the collected intelligence graph
================================================================================
```

---

## Standard Output Schema

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
      "timestamp": "2026-06-13T00:00:00Z"
    }
  ],
  "relationships": [
    {
      "src": {"type": "ip", "value": "192.168.1.10"},
      "relation": "has_open_port",
      "dst": {"type": "port", "value": "22/SSH"},
      "evidence": "port scan",
      "confidence": 1.0,
      "timestamp": "2026-06-13T00:00:00Z"
    }
  ],
  "timestamp": "2026-06-13T00:00:00Z"
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
  "timestamp": "2026-06-13T00:00:00Z"
}
```

---

## Context Structure

The `ContextManager` maintains a live intelligence graph updated by every module:

```json
{
  "ips": {
    "8.8.8.8": {
      "ports": [{"port": 80, "service": "http"}],
      "geo": {
        "country": "United States",
        "city": "Mountain View",
        "isp": "Google LLC"
      },
      "hostname": "dns.google"
    }
  },
  "domains": {
    "dns.google": {"ips": ["8.8.8.8"]}
  },
  "notes": [...],
  "relations": [
    {
      "src": {"type": "ip", "value": "8.8.8.8"},
      "relation": "located_in",
      "dst": {"type": "location", "value": "Mountain View, United States"},
      "evidence": "geoip lookup",
      "confidence": 1.0
    }
  ],
  "derived_relations": [...],
  "meta": {
    "created_at": "...",
    "updated_at": "...",
    "event_count": 5,
    "recent_events": ["ip_added:8.8.8.8", "geo_updated:8.8.8.8"]
  }
}
```

---

## Configuration

Runtime config lives in `config/config.json`:

```json
{
  "log_level": "INFO",
  "threads": 20,
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.7",
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

## Typical Workflow

```bash
# 1. Collect intelligence
corvus > footprint example.com
corvus > scan 192.168.1.10
corvus > geoip 8.8.8.8
corvus > whois example.com
corvus > subdomain example.com
corvus > tech example.com
corvus > crawl example.com

# 2. Inspect the live graph
corvus > context

# 3. Run Nexus correlation & risk analysis
corvus > nexus analyze

# 4. Export results
corvus > nexus export html          # -> logs/nexus_report.html
corvus > nexus export json          # -> logs/nexus_neo4j.json
corvus > nexus export html reports/my_report.html   # custom path
```

---

## Roadmap

- **Interactive Analyst Layer:** LLM-guided threat reasoning and natural language context queries.
- **Dynamic Visualizer Graph:** Interactive network relationship visualizer (D3.js / Cytoscape).
- **Neo4j Integration:** Direct push to a running Neo4j instance via Bolt protocol.
- **PDF Export:** Printable intelligence dossier alongside the HTML version.

---

## Disclaimer

This project is for educational and authorized security research purposes only. Unauthorized use is strictly prohibited.
