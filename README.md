# Corvus Corax

Corvus Corax is a modular reconnaissance and analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture.

**See the unseen systems.**

## Current Version

**v0.4 - Context-Driven Recon Expansion**

v0.4 extends the stable v0.3 core with new passive recon modules, configurable runtime behavior, and a richer Nexus-ready context model (notes, relations, meta events).

## What's New in v0.4

- **New Recon Modules**
  - `whois`: WHOIS lookup with referral-aware querying.
  - `subdomain`: passive subdomain enum (`crt.sh`) + optional wordlist candidate generation.
  - `tech`: server, `X-Powered-By`, and framework hint detection.
  - `crawl`: lightweight page crawl (`title`, `links`, `forms`, `status_code`).

- **Config-Driven Runtime**
  - `config/config.json` expanded with:
    - `timeout`
    - `threads`
    - `user_agent`
    - `output_mode`
    - `scan_defaults`
  - `scan`, `netscan`, `geoip`, and web request based modules now use config values instead of hardcoded runtime behavior.

- **Logger Upgrade**
  - Colored console logs by level.
  - Rotating log files (size-based rollover).
  - Cleaner timestamped formatting.
  - Log level/settings can be controlled via config fallback logic.

- **Nexus-Ready Context Upgrade**
  - Context now includes:
    - structured `notes`
    - `relations`
    - `meta` (`created_at`, `updated_at`, event tracking)
  - New helper methods:
    - `add_note(...)`
    - `add_relation(...)`
    - `merge_context(...)`
  - Existing modules progressively emit structured context data for future multi-context reasoning.

- **Platform Stability Fix**
  - Banner output was made Windows-safe (ASCII rendering) to prevent encoding crashes in non-UTF terminals.

> v0.4 is a capability milestone: same framework philosophy, richer intelligence graph foundation.

---

## Module Set

| Module | Description |
| :--- | :--- |
| `scan` | Multi-mode port/network target scan (`normal`, `slow`, `banner`, `subnet`) |
| `netscan` | Network host discovery |
| `footprint` | Domain resolution and host footprint collection |
| `geoip` | IP geolocation lookup |
| `whois` | WHOIS lookup for domain/IP targets |
| `subdomain` | Passive subdomain discovery (`crt.sh`) + optional wordlist candidates |
| `tech` | Detect server, powered-by header, and framework hints |
| `crawl` | Extract title, links, forms, and HTTP status from a target page |
| `context` | View correlated intelligence context |
| `help` | Command list |
| `version` | Framework version information |

---

## Output Standard (v0.4 Core Contract)

All modules return normalized JSON-style payloads:

```json
{
  "module": "scan",
  "target": "192.168.1.10",
  "status": "success",
  "data": {}
}
```

Error form:

```json
{
  "module": "geoip",
  "target": "invalid-ip",
  "status": "error",
  "error": "lookup failed"
}
```

---

## Context Structure (Nexus-Compatible)

The context model remains stable while now including relation and event metadata:

```json
{
  "ips": {
    "1.2.3.4": {
      "ports": [],
      "geo": {},
      "hostname": null
    }
  },
  "domains": {},
  "notes": [
    {
      "text": "geoip lookup completed for 1.2.3.4",
      "source": "geoip",
      "severity": "info",
      "timestamp": "..."
    }
  ],
  "relations": [],
  "meta": {
    "created_at": "...",
    "updated_at": "...",
    "event_count": 0,
    "recent_events": []
  }
}
```

`context` prints a cleaned summary while preserving schema compatibility for future Nexus analysis.

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

Notes:
- `output_mode`: `text` (pretty JSON) or `json` (compact JSON)
- `scan_defaults` controls scan behavior centrally without touching module code

---

## Usage

```bash
corvus > help
corvus > version
corvus > scan 192.168.1.10 normal 1 1024
corvus > scan 192.168.1.10 banner 80
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

## Philosophy

Corvus Corax is an evolving system, not a one-off script set.  
Direction:

**data collection -> data correlation -> automated analysis**

---

## Roadmap

- Nexus multi-context correlation engine
- Risk scoring layer
- Cross-module relationship analysis
- Structured analytical report generation
- Interactive analyst-style response layer ("framework that thinks and talks")
- Improved result visualization

---

## Disclaimer

This project is for educational and authorized security research purposes only.  
Unauthorized use is strictly prohibited.

---

## Project History

Corvus Corax is the framework evolution of CrowWatch:

- **CrowWatch**: module-focused reconnaissance tooling
- **Corvus Corax**: modular, context-aware, extensible framework core

---

## Documentation

For architecture details, see `docs/`.
