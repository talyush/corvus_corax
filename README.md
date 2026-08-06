# Corvus Corax

Corvus Corax is a modular reconnaissance and intelligence analysis framework for cybersecurity learners and researchers.  
It is designed to collect, normalize, and correlate reconnaissance data in a scalable core architecture, creating a unified intelligence flow with NATO-standard confidence scoring and multi-format graph export capabilities.

**See the unseen systems.**

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
                                             (Correlation & Admiralty Scoring)
                                                    │
                                             [ NexusExporter ]
                                             (HTML / Neo4j JSON / Graph JSON)
```

---

## Current Version

**v0.8.5 — Identity Update & Dynamic Analysis Flow**

v0.8.5 overhauls Corvus Corax's identity, introducing interactive boot sequences, 3D title graphics, surveillance reticle art, phased investigation goal tracking, real-time dynamic work execution, and Cyber Sherlock narrative assessment commentary.

---

## Changelog

### v0.8.5 — Identity Update & Dynamic Analysis Flow

**Visual Identity & Boot Experience:**
- **`core/banner.py`** — Interactive boot sequence initialization routine (`[READY]`, `[INITIALIZED]`), ANSI 3D "Corvus Corax" title banner, and 67-character surveillance reticle ASCII artwork.
- **Mottos & Branding** — *See The Unseen* and *>> From Evidence to Intelligence <<*.
- **Exit Animation** — Typing typewriter animation effect on `exit`/`quit` or `Ctrl+C` session end ("*The crow returns to the shadows...*").

**Analyst Experience & Real-Time Dynamic Execution:**
- **`core/investigation_flow.py`** — High-contrast `[INVESTIGATION GOAL]` header rendering and multi-phase progression tracker (`>> Phase 1/3 -- TARGET ACQUISITION`).
- **`core/module_base.py`** — Live work-wrapped `status_step()` execution. Status steps dynamically transition from `[~] RUNNING` to `[OK]` during actual network & socket tasks.
- **`output/output_manager.py`** — `[Analyst Assessment]` Cyber Sherlock narrative synthesis blocks highlighting critical security findings.
- **`core/analyst_advisor.py` & `core/analyst_runtime.py`** — Context-aware preflight commentary and intelligent next-step investigative suggestions after module execution.
- **Full Module Coverage** — Integrated phased investigation flows across all 18 platform modules (`dns`, `scan`, `cert`, `headers`, `metadata`, `email`, `tech`, `subdomain`, `geoip`, `whois`, `asn`, `netscan`, `footprint`, `crawl`, `nexus`, `help`, `version`).

---

### v0.8 — Intelligence Expansion

**New Intelligence Modules:**

- **`modules/cert_intel.py`** — Certificate Intelligence Module
  - Deep TLS certificate analysis with fingerprint extraction
  - Subject Alternative Names (SAN) parsing and wildcard detection
  - Certificate transparency integration for shared cert detection
  - Expiration analysis and issuer intelligence
  - Nexus correlation support for certificate-based entity relationships

- **`modules/dns_intel.py`** — DNS Intelligence Module
  - Comprehensive DNS record enumeration (A, AAAA, MX, NS, TXT, CAA)
  - Security-specific record analysis (SPF, DMARC, DKIM)
  - Email infrastructure profiling and spoofing vulnerability assessment
  - Custom resolver configuration with public DNS fallback
  - Timeout handling for unreliable DNS servers

- **`modules/http_headers.py`** — HTTP Header Intelligence Module
  - Detailed HTTP header extraction and analysis
  - Security header evaluation (CSP, HSTS, X-Frame-Options, etc.)
  - CORS policy analysis and cookie security assessment
  - Technology fingerprinting from header signatures
  - WAF/CDN detection via header patterns

- **`modules/email_intel.py`** — Email Pattern Discovery Module
  - Email provider identification via SPF/MX fingerprints
  - DMARC reporting address extraction
  - Email naming convention detection from sample addresses
  - Role-based mailbox vs personal email distinction
  - Likely email format generation for target domains

- **`modules/metadata_intel.py`** — Metadata Collection Module
  - Robots.txt and sitemap.xml parsing
  - Favicon hash calculation (Shodan-compatible MurmurHash3)
  - Security.txt discovery and analysis
  - Generator meta tag extraction
  - Nexus correlation support for shared infrastructure detection

- **`modules/asn.py`** — ASN Intelligence Module
  - ASN lookup with organization and ISP identification
  - CIDR block extraction and related IP enumeration
  - Country-level geolocation intelligence
  - Nexus correlation support for ASN-based entity relationships

**NATO Admiralty Scoring System:**

- **`core/admiralty.py`** — NATO Admiralty Intelligence Scoring
  - `SourceReliability` (A-F): Kaynak güvenilirlik sınıflandırması
  - `InformationReliability` (1-6): Bilgi doğruluk sınıflandırması
  - `EvidenceType`: Kanıt tipleri ve ağırlıkları (CERTIFICATE_MATCH=40, SHARED_FAVICON=25, vb.)
  - `AdmiraltyScorer`: Kanıt zinciri ve confidence hesaplama (0-100 puan)
  - Default source reliability mapping for data source types

**Nexus Engine Integration:**

- **`core/nexus.py`** — Enhanced Risk Calculation
  - `calculate_risk()` integrated with Admiralty scoring
  - Risk profiles now include `admiralty_rating`, `evidence_count`, `evidence_chain`
  - Evidence-based risk scoring for admin ports, outdated software, ASN intelligence
  - RULE 12: ASN Intelligence Correlation (shares_asn, same_provider, same_prefix)

**Hybrid Output System:**

- **`modules/nexus.py`** — Verbose Flag Support
  - `--verbose` / `-v` flag for detailed evidence chains
  - Summary mode: Risk score + Admiralty rating + evidence count
  - Verbose mode: Full evidence chain with admiralty codes, weighted scores, source info

- **`output/output_manager.py`** — Enhanced Nexus Dashboard
  - Conditional formatting based on verbose flag
  - Admiralty rating display in risk profiles
  - Evidence chain expansion in verbose mode

**Context Command Integration:**

- **`core/context.py`** — Admiralty Intelligence Display
  - `context --admiralty`: ASN and tech intelligence summary
  - `context <entity> --admiralty`: Detailed entity evidence chains
  - ASN intel, tech intel, derived relations Admiralty correlations

- **`main.py`** — Context Command Enhancement
  - Admiralty flag support for context command
  - Entity-specific intelligence queries

**Generic Graph Export Format:**

- **`core/exporter.py`** — AI/ML Pipeline Support
  - `generate_graph_data()`: Generic graph format (nodes + edges + metadata)
  - `export_graph_json()`: Graph data export to disk
  - IP nodes: Admiralty rating, evidence_count, ASN, geo, ports
  - Domain nodes: Tech stack, frameworks, CMS, WAF/CDN
  - Edges: Full metadata (evidence, confidence, timestamp, derived flag)

- **`modules/nexus.py`** — Graph Export Command
  - `nexus export graph [filepath]` command
  - Default path: `logs/nexus_graph.json`
  - Format: `corvus_graph_v1` for AI/ML pipeline compatibility

**Pipeline Architecture:**

- Machine → graph.json → AI → neo4j → visualization
- Three export formats: HTML (interactive), Neo4j JSON (graph database), Graph JSON (AI/ML)

**Help Documentation:**

- **`modules/help.py`** — Comprehensive Command Reference
  - All new modules documented
  - Verbose flag usage explained
  - Admiralty context commands documented
  - Graph export format explained
  - Default export paths updated

### v0.7.2 — Subdomain Stability Patch

- **`modules/subdomain_enum.py`**:
  - Added **HackerTarget** API and **RapidDNS** parsing lookups to run alongside `crt.sh`.
  - Configured minimum `8.0 seconds` timeout for all passive OSINT resources to prevent premature timeouts on slower servers.
  - Isolated connection/timeout errors per source so that one flaky source (like `crt.sh`) does not fail the entire module execution.
  - Consolidated subdomains across all active sources and updated intelligence relations with consolidated evidence names.
- **`output/output_manager.py`**:
  - Dynamically formats subdomain results to list the specific active sources (e.g. `Active Sources: hackertarget, rapiddns`).
  - Supports backwards-compatible data structures for legacy count values.
- **Branding updates**:
  - Version updated to `v0.7.2-stability-patch` in `core/banner.py`, `modules/version.py`, and `modules/help.py`.

### v0.7.1 — Stability & Polish

- **`core/logger.py`:** Removed `StreamHandler` (console output). Logger now writes to file only — no more raw log lines appearing in the terminal after commands like `help`.
- **`output/output_manager.py`:**
  - `to_log()`: Changed from dumping the full JSON payload to logging a brief summary (`[module] status=X target=Y`).
  - `to_text()`: `help` and `version` modules now skip the `[+] SUCCESS / Target / Time` header block — clean output only.
- **`main.py`:**
  - Added `exit_animation()`: typewriter-style *"The crow returns to the shadows..."* on `exit`, `quit`, or `Ctrl+C`.
  - Removed noisy `[*] Running module` / `[+] Module finished` prints.
  - Improved unknown command message to show what was typed.

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
  └─► Display Notes & Nexus alerts            ├─► Graph Entity Relationships
                                                    │
                                             [ NexusEngine ]
                                             (Correlation & Admiralty Scoring)
                                                    │
                                             [ NexusExporter ]
                                             (HTML / Neo4j JSON / Graph JSON)
```

---

## What's New in v0.8 (Intelligence Expansion)

### Deep Intelligence Modules

**Certificate Intelligence (`modules/cert_intel.py`)**:
- Deep TLS certificate analysis with SHA-256 fingerprint extraction
- Subject Alternative Names (SAN) parsing for wildcard and multi-domain certificates
- Certificate transparency integration for shared certificate detection across entities
- Expiration timeline analysis and issuer intelligence extraction
- Nexus correlation support for certificate-based entity relationships

**DNS Intelligence (`modules/dns_intel.py`)**:
- Comprehensive DNS record enumeration (A, AAAA, MX, NS, TXT, CAA)
- Security-specific record analysis (SPF, DMARC, DKIM) for email spoofing assessment
- Email infrastructure profiling and mail server identification
- Custom resolver configuration with public DNS fallback (Google, Cloudflare)
- Graceful timeout handling for unreliable DNS servers

**HTTP Header Intelligence (`modules/http_headers.py`)**:
- Detailed HTTP header extraction and security evaluation
- Security header analysis (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- CORS policy analysis and cross-origin request assessment
- Cookie security evaluation (HttpOnly, Secure, SameSite attributes)
- Technology fingerprinting from header signatures
- WAF/CDN detection via header patterns (Cloudflare, Akamai, Sucuri, etc.)

**Email Pattern Discovery (`modules/email_intel.py`)**:
- Email provider identification via SPF/MX fingerprints (Google Workspace, Microsoft 365, etc.)
- DMARC reporting address extraction for abuse contact discovery
- Email naming convention detection from sample addresses
- Role-based mailbox vs personal email distinction (admin@, support@, etc.)
- Likely email format generation for target domains

**Metadata Collection (`modules/metadata_intel.py`)**:
- Robots.txt parsing for crawler directives and hidden paths
- Sitemap.xml extraction for content structure analysis
- Favicon hash calculation using Shodan-compatible MurmurHash3 algorithm
- Security.txt discovery and security policy analysis
- Generator meta tag extraction for CMS identification
- Nexus correlation support for shared infrastructure detection

**ASN Intelligence (`modules/asn.py`)**:
- ASN lookup with organization and ISP identification
- CIDR block extraction and related IP enumeration
- Country-level geolocation intelligence
- Network infrastructure profiling
- Nexus correlation support for ASN-based entity relationships

### NATO Admiralty Scoring System

**Admiralty Intelligence (`core/admiralty.py`)**:
- `SourceReliability` (A-F): Kaynak güvenilirlik sınıflandırması (A=Completely Reliable, F=Cannot Be Judged)
- `InformationReliability` (1-6): Bilgi doğruluk sınıflandırması (1=Confirmed, 6=Unverifiable)
- `EvidenceType`: Kanıt tipleri ve ağırlıkları (CERTIFICATE_MATCH=40, SHARED_FAVICON=25, SAME_TECH_STACK=20, SAME_ASN=15)
- `AdmiraltyScorer`: Kanıt zinciri ve confidence hesaplama (0-100 puan)
- Default source reliability mapping for data source types (cert_intel=A, asn=A, tech=B, etc.)
- Admiralty code generation (e.g., A1, B2, C3) based on confidence percentage

### Nexus Engine Integration

**Enhanced Risk Calculation (`core/nexus.py`)**:
- `calculate_risk()` integrated with Admiralty scoring
- Risk profiles now include `admiralty_rating`, `evidence_count`, `evidence_chain`
- Evidence-based risk scoring for admin ports, outdated software, ASN intelligence
- RULE 12: ASN Intelligence Correlation (shares_asn, same_provider, same_prefix)
- Weighted evidence accumulation with source and information reliability factors

### Hybrid Output System

**Verbose Flag Support (`modules/nexus.py`)**:
- `--verbose` / `-v` flag for detailed evidence chains
- Summary mode: Risk score + Admiralty rating + evidence count
- Verbose mode: Full evidence chain with admiralty codes, weighted scores, source info

**Enhanced Nexus Dashboard (`output/output_manager.py`)**:
- Conditional formatting based on verbose flag
- Admiralty rating display in risk profiles
- Evidence chain expansion in verbose mode
- Color-coded confidence indicators

### Context Command Integration

**Admiralty Intelligence Display (`core/context.py`)**:
- `context --admiralty`: ASN and tech intelligence summary
- `context <entity> --admiralty`: Detailed entity evidence chains
- ASN intel, tech intel, derived relations Admiralty correlations

**Context Command Enhancement (`main.py`)**:
- Admiralty flag support for context command
- Entity-specific intelligence queries

### Generic Graph Export Format

**AI/ML Pipeline Support (`core/exporter.py`)**:
- `generate_graph_data()`: Generic graph format (nodes + edges + metadata)
- `export_graph_json()`: Graph data export to disk
- IP nodes: Admiralty rating, evidence_count, ASN, geo, ports
- Domain nodes: Tech stack, frameworks, CMS, WAF/CDN
- Edges: Full metadata (evidence, confidence, timestamp, derived flag)

**Graph Export Command (`modules/nexus.py`)**:
- `nexus export graph [filepath]` command
- Default path: `logs/nexus_graph.json`
- Format: `corvus_graph_v1` for AI/ML pipeline compatibility

### Pipeline Architecture

- Machine → graph.json → AI → neo4j → visualization
- Three export formats: HTML (interactive), Neo4j JSON (graph database), Graph JSON (AI/ML)

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
  CORVUS CORAX v0.8 — INTELLIGENCE EXPANSION  |  Modular Recon Framework
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               | [--admiralty]                | Show collected context (use --admiralty for intelligence details)
  scan                  | <ip> <mode> ...              | Port scan (normal/slow/banner/subnet)
  netscan               | <ip/network>                 | Scan a network/subnet
  footprint             | <domain>                     | Get IP and hostname info
  geoip                 | <ip>                         | Get geolocation info
  whois                 | <domain|ip>                  | Run WHOIS lookup
  dns                   | <domain> [selector]          | Run DNS & email security (SPF/DMARC/DKIM/CAA)
  email                 | <domain> [sample1,sample2]   | Email provider, DMARC contacts & address patterns
  subdomain             | <domain> [wordlist]          | Passive subdomain enum (crt.sh+HackerTarget+RapidDNS)
  tech                  | <url_or_host>                | Detect server, framework & tech stack
  asn                   | <ip_address>                 | ASN lookup: organization, CIDR & related IPs
  crawl                 | <url_or_host>                | Get title, links, forms & status code
  cert                  | <host> [port]                | Fetch & analyze TLS certificate intelligence
  headers               | <url_or_host>                | Fetch & analyze HTTP headers, security & cookies
  metadata              | <url_or_host>                | Collect robots.txt, sitemap, favicon hash & security.txt
  nexus                 | [analyze] [--verbose]        | Run Nexus Correlation Engine
  nexus analyze         | [--verbose]                  | Correlate & score all collected data
  nexus export html     | [filepath]                   | Export HTML intelligence dossier
  nexus export json     | [filepath]                   | Export Neo4j-ready graph JSON
  nexus export graph    | [filepath]                   | Export generic graph JSON (AI/ML ready)
================================================================================
  Notes:
    - Nexus commands require prior data collection (scan, footprint, etc.)
    - Use 'nexus analyze --verbose' for detailed Admiralty evidence chains
    - Use 'context --admiralty' for intelligence summary
    - Use 'context <entity> --admiralty' for detailed entity evidence
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json | logs/nexus_graph.json
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
corvus > scan 192.168.1.10 normal
corvus > geoip 8.8.8.8
corvus > whois example.com
corvus > subdomain example.com
corvus > dns example.com
corvus > email example.com admin@,support@
corvus > tech example.com
corvus > asn 192.168.1.10
corvus > cert example.com 443
corvus > headers example.com
corvus > metadata example.com
corvus > crawl example.com

# 2. Inspect the live graph
corvus > context
corvus > context --admiralty              # Admiralty intelligence summary
corvus > context 192.168.1.10 --admiralty # Entity-specific evidence

# 3. Run Nexus correlation & risk analysis
corvus > nexus analyze                   # Summary mode
corvus > nexus analyze --verbose         # Detailed evidence chains

# 4. Export results
corvus > nexus export html               # -> logs/nexus_report.html
corvus > nexus export json               # -> logs/nexus_neo4j.json
corvus > nexus export graph              # -> logs/nexus_graph.json (AI/ML ready)
corvus > nexus export html reports/my_report.html   # custom path
```

---

## Roadmap

- **Interactive Analyst Layer:** LLM-guided threat reasoning and natural language context queries.
- **Dynamic Visualizer Graph:** Interactive network relationship visualizer (D3.js / Cytoscape).
- **Neo4j Integration:** Direct push to a running Neo4j instance via Bolt protocol.
- **PDF Export:** Printable intelligence dossier alongside the HTML version.
- **Admiralty AI Integration:** Machine learning models for automated evidence weighting and confidence prediction.

---

## Disclaimer

This project is for educational and authorized security research purposes only. Unauthorized use is strictly prohibited.
