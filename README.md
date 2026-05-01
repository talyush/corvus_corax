# Corvus Corax

Corvus Corax is a modular reconnaissance and analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture.

**See the unseen systems.**

## Current Version

**v0.3 - Stable Framework Core**

v0.3 focuses on framework stability, consistent module behavior, and a clean context/output pipeline while preserving the architecture for future Nexus integration.

## What's New in v0.3

- **Stable Output Layer**
  - `OutputManager` is stabilized (`clear()` fix, safe result handling, normalized JSON output).
  - Module outputs are now consistently rendered and logged.

- **Unified Module Standard**
  - Core modules now follow the same response contract:
    - `module`
    - `target`
    - `status` (`success` / `error`)
    - `data` or `error`
  - Legacy direct `print` patterns inside modules are standardized.

- **Clean Context View (Nexus-ready)**
  - Context structure is preserved for future Nexus compatibility.
  - `context` output is cleaned from empty/noise fields while keeping schema intact.

- **Main Loop Simplification**
  - `main.py` command flow is simplified and stabilized.
  - Better runtime feedback in terminal for long-running modules (`scan`, `netscan`).

> v0.3 is a stabilization milestone: same architecture, cleaner execution.

---

## Module Set

| Module | Description |
| :--- | :--- |
| `scan` | Multi-mode port/network target scan (`normal`, `slow`, `banner`, `subnet`) |
| `footprint` | Domain resolution and host footprint collection |
| `geoip` | IP geolocation lookup |
| `netscan` | Network host discovery |
| `context` | View correlated intelligence context |
| `help` | Command list |
| `version` | Framework version information |

---

## Output Standard (v0.3 Core Contract)

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

The context model remains stable for future Nexus engine integration:

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
  "notes": []
}
```

`context` command prints a cleaned summary without breaking schema compatibility.

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
corvus > context
```

---

## Philosophy

Corvus Corax is an evolving system, not a one-off script set.  
Direction:

**data collection -> data correlation -> automated analysis**

---

## Roadmap

- Nexus Correlation Engine
- Risk scoring layer
- Cross-module relationship analysis
- Structured analytical report generation
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

For architecture details, see: `docs/architecture.md`
