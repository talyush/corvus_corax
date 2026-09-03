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
  ├─► Render formatted terminal output        ├─► Map IPs / Domains / Persons
  ├─► Summarize discoveries                   ├─► Record Notes w/ Confidence
  └─► Display Notes & Nexus alerts            ├─► Graph Entity Relationships
                                                    │
                                             [ NexusEngine ]
                                             (Correlation & Admiralty Scoring)
                                                    │
                                             [ Intelligence Vault ]
                                             (Persistent Memory — The Machine)
                                                    │
                                             [ Pattern of Life Engine ]
                                             (Behavioral Analysis & Anomaly Detection)
                                                    │
                                             [ GEOINT / Visualizer ]
                                             (Interactive Map & Graph)
```

---

## Current Version

**v1.1.0-inference-engine — Bayesian Reasoning, Competing Hypotheses & Dynamic Bridges**

v1.1 introduces the **Inference Engine** ("Sherlock"): Real Bayesian Sequential Updating (`P(H|E)`), Pattern Extraction, Hypothesis Lifecycle Management, Dynamic Bridges (Shared Infrastructure, Temporal, Type-based), Shannon Entropy Uncertainty Quantification, Negative Evidence Reasoning, and Counterfactual Explanations ("What would confirm/refute this?").

---

## Changelog

### v1.1.0-inference-engine — Bayesian Inference & Hypothesis Reasoning

**Inference Engine (`core/inference/`):**
- **`bayesian.py`** — Gerçek Bayesian sequential inanç güncelleme motoru (`HypothesisBelief`, `BayesianUpdater`), type-informed prior tablosu ve Bayes izi (trail).
- **`evidence_weight.py`** — NATO Admiralty, çapraz teyit çarpanı, temporal decay ve conflict cezası içeren gerçek kanıt ağırlıklandırma modeli (`EvidenceWeighter`).
- **`pattern.py`** — OSINT örüntü çıkarma motoru (`PatternExtractor`: Ownership, Infrastructure Cluster, Identity Anchor, Temporal Burst, Multi-source).
- **`hypothesis.py`** — Hipotez veri modeli (`Hypothesis`), hipotez üretici (`HypothesisGenerator`) ve durum geçiş makinesi (`HypothesisLifecycle`: Generated -> Active -> Confirmed/Refuted/Archived).
- **`dynamic_bridge.py`** — Graf bileşenleri arasındaki gizli bağlantıları keşfeden dinamik köprü motoru (`DynamicBridgeEngine`: Shared Infrastructure, Temporal, Type-Based).
- **`uncertainty.py`** — Shannon Entropisi ile belirsizlik ölçümü (`UncertaintyEngine`), kritik belirsizlik tespiti ve "What Corvus Does Not Know" analizi.
- **`counterfactual.py`** — Karşıolgusal akıl yürütme motoru (`CounterfactualEngine`: "Bunu doğrulamak/çürütmek için ne gerekir?", alternatif açıklamalar ve önerilen keşif eylemleri).
- **`temporal_reasoner.py`** — Zamansal çıkarım motoru (`TemporalReasoningEngine`: Temporal burst tespiti, zaman çizelgesi örtüşmesi, kronolojik nedensellik zinciri).
- **`negative_evidence.py`** — Yokluk ve negatif kanıt çıkarım motoru (`NegativeEvidenceEngine`: Beklenen ama bulunamayan kanıtların Bayesian inancı düşürmesi).
- **`orchestrator.py`** — Tüm çıkarım bileşenlerini tek bir pipeline'da birleştiren merkezi orkestratör (`InferenceOrchestrator`).

---

### v1.0.0-nexus-intelligence — Graph Service Layer, CQRS Event Bus & Nexus Reasoning

**CQRS & Event Sourcing (`core/events/`):**
- **`types.py`** & **`bus.py`** — Typed Event System (`EntityDiscovered`, `RelationshipCreated`, `EvidenceCorroborated`, `ConflictDetected`, `AssetBound`) and Observer pattern `EventBus`.

**Graph Service Abstraction Layer (`core/graph/`):**
- **`interface.py`** — `AbstractGraphService` interface separating Commands and Intelligence-Level Queries.
- **`providers/neo4j_provider.py`** — Docker Neo4j (`bolt://localhost:7687`) Cypher driver mapping intelligence queries to graph patterns.
- **`providers/memory_provider.py`** — Dahili In-Memory fallback graph service ensuring 100% zero downtime.

**Nexus Intelligence Engine (`core/nexus/`):**
- **`reasoning.py`** — **Graph Reasoning Engine**: Generates human-readable analytical reasoning statements ("X relationship observed between A and B, supported by N evidences...").
- **`timeline.py`** — **Temporal Timeline Engine**: Event sequences and chronological order (`nexus timeline`).
- **`assets.py`** — **Asset Intelligence**: Treats owned resources (Certificates, DNS records, subnets) as distinct first-class intelligence assets.
- **`modules/nexus.py`** — CLI Nexus Intelligence commands (`nexus summary`, `nexus query paths`, `nexus query clusters`, `nexus timeline`, `nexus correlation`).

---

### v0.9.5-evidence-engine — Evidence Processing Pipeline, Lineage & Intelligence Gaps

**Evidence Processing Pipeline (`core/evidence/`):**
- **`model.py`** — `Observation` (sequential observation IDs `#12`), `Evidence` (atomic GUIDs, SHA-256 raw hashes, NATO codes), `KeyFinding` cards, and `IntelligenceGaps`.
- **`extractor.py`** — Normalizes raw module outputs into structured observations and atomic evidence objects.
- **`validator.py`** — Validates format, syntax, IP ranges, domain regex, and TLS cert dates.
- **`corroboration.py`** — Independent cross-source corroboration confidence boosts and multi-source conflict detection.
- **`derived.py`** — Higher-level intelligence derivation and `KEY FINDING` card creation.
- **`lineage.py`** — Parent-to-child provenance lineage tree tracking (`evidence lineage <id>`) and institutional-grade **WHAT CORVUS DOES NOT KNOW** intelligence gaps reporting (`evidence gaps <target>`).
- **`modules/evidence.py`** — CLI Evidence command suite (`evidence list`, `evidence findings`, `evidence gaps`, `evidence lineage`).

---

### v0.9.1-autonomous — Autonomous Intelligence Strategy & Capability Engine

**Autonomous Strategy Engine:**
- **`core/strategy.py`** — Goal Decomposition (`GoalDecomposer`), Hypothesis Formulation (`HypothesisEngine`), Action Selection (`ActionPlanner`), and Failure Awareness & Dynamic Pivoting (`FailureEvaluator`).
- **`core/discovery.py` & `modules/discover.py`** — Dynamic investigation orchestration replacing static module chains. Automatically evaluates target seeds, tests hypotheses, handles probe failures, and executes fallback dorking/pivots.

**Corvus Capability Layer (`core/capabilities/`):**
- **`core/capabilities/identity_capability.py`** — Turkish character normalization (`ç, ğ, ı, ö, ş, ü` -> `c, g, i, o, s, u`), name & username handle permutations (`firstlast`, `f.last`, `first_last`), and candidate email generation.
- **`core/capabilities/search_capability.py`** — Kamuya açık arama motoru OSINT dorking (DuckDuckGo HTML / public probing) for target names, handles, emails, and corporate documents.
- **`core/capabilities/enrichment_capability.py`** — Gravatar MD5 avatar hash checking & profile discovery.

---

### v0.9.0-alpha — Intelligence Collection Expansion (5.5 Phases)

#### Phase 1 — Core Transformation
- **`core/context.py`** — Entity-agnostic intelligence graph: all entities (ip, domain, person, organization, phone, email, social_profile, wallet, location, certificate...) stored in a unified `entities` registry.
- **Temporal Event Store** — `events` buffer for Pattern of Life (POL) analysis. Every module logs timestamped events automatically.
- **New APIs** — `add_entity()`, `add_person()`, `add_organization()`, `add_phone()`, `add_email()`, `add_social_profile()`, `add_wallet()`, `add_location()`, `add_event()`, `query_events()`.
- **Backward compatibility** — Legacy `ips`, `domains`, `certificates` fields preserved; all existing modules work unchanged.

#### Phase 2 — Entity Expansion: Phone & Social Intelligence
- **`modules/phone_intel.py`** — Phone analysis: E.164 normalization, operator prefix detection (with MNP warning), number type classification, candidate person linking.
- **`modules/social_intel.py`** — Username OSINT: 12-platform sweep, correlation probability model (base 0.15 + 0.1/platform, max 0.7).
- **`config/rules.json`** — Centralized rule system: evidence weights, source reliability, relationship policies, operator prefixes, social platforms.
- **`core/admiralty.py`** — Evidence weights and source reliability now loaded from `rules.json` (no more hardcoding).
- **Candidate/possible model** — Phone/email/username links are CANDIDATE, not confirmed ownership.

#### Phase 3 — Deepening: Organization, Academic, Wallet, Breach, GitHub, Wayback
- **`modules/org_intel.py`** — Organization intelligence: domain ownership (candidate), personnel mapping, infrastructure correlation.
- **`modules/academic_intel.py`** — Academic intelligence: OpenAlex API (free, no key), ORCID, publications, university detection from email domain.
- **`modules/financial_intel.py`** — Wallet intelligence: BTC/ETH/SOL format validation, chain detection, live BTC balance (blockchain.info, no key).
- **`modules/breach_intel.py`** — Breach intelligence: Firefox Monitor (no key), HIBP Pwned Passwords (k-anonymity), manual sources. **Ethical design: meta-data only — no raw credentials stored.**
- **`modules/github_intel.py`** — GitHub intelligence: profile, repos, commit email correlation, secret scanning.
- **`modules/wayback_intel.py`** — Wayback Machine: snapshot history, CDX records, web history correlation.
- **Nexus Rule 16-20** — Organization, academic, wallet, GitHub, Wayback correlation rules.

#### Phase 4 — Visualization: GEOINT Map, D3.js Graph, Persistence
- **`core/geoint.py`** — Leaflet.js + OpenStreetMap interactive map: IP/person/org markers, movement routes, heatmap.
- **`core/visualizer.py`** — D3.js force-directed graph: drag, zoom, hover tooltip, detail panel, search, legend.
- **`modules/geoint.py`** — CLI: `geoint map`, `geoint graph`, `geoint timeline`, `geoint export` (GeoJSON).
- **`modules/netscan.py`** — Extended: `--ports`, `--geo`, `--map` flags for deep network discovery.
- **`core/db.py`** — Persistence: `save_state()`, `load_state()`, `save_geoint()`, `save_timeline()`.
- **`main.py`** — `context save/load` commands for session persistence.

#### Phase 5 — Pattern of Life (POL) Engine + Intelligence Vault
- **`core/db.py` — `IntelligenceVault`** — Three-layer architecture:
  - **Session Context (RAM)** — temporary, lost on session end
  - **Intelligence Vault (Disk)** — persistent, confirmed evidence (JSONL append-only log + index.json)
  - **POL Engine (Analysis)** — reads from vault, extracts behavior patterns
- **Evidence threshold filter** — `confidence >= 0.5` auto-persists; low-confidence candidate/possible links filtered.
- **`core/pol.py`** — Pattern of Life engine:
  - **Activity Rhythm** — hourly/weekly activity distribution, peak hours
  - **Movement Pattern** — location history, routes, VPN warning
  - **Communication Pattern** — entity connections
  - **Anomaly Detection** — hybrid (rule-based + statistical z-score)
  - **Case File** — full investigation dossier
- **`modules/pol.py`** — CLI: `pol analyze`, `pol compare`, `pol casefile`, `pol timeline`.
- **`main.py`** — `vault show/events/confirm/stats` commands.

#### Phase 5.5 — Intelligence Deepening: Entity Resolution, Pivoting, Confidence
- **`core/confidence.py`** — Confidence aggregation: `1 - (1-c1)*(1-c2)*...` formula. Weak individual evidence combines into strong evidence.
- **`modules/resolve.py`** — Entity resolution: identity clustering. `resolve ahmet` finds all entities belonging to the same person (phone, email, GitHub, org).
- **`modules/pivot.py`** — Cross-entity pivoting: BFS graph traversal. `pivot ahmet --depth=3` discovers the entire company infrastructure from a single phone number.

---

## Command Reference

```
================================================================================
  CORVUS CORAX v0.9 — INTELLIGENCE COLLECTION EXPANSION  |  Modular Recon Framework
================================================================================
  Command               | Arguments                    | Description
--------------------------------------------------------------------------------
  help                  |                              | Show commands
  version               |                              | Show tool version
  context               | [--admiralty]                | Show collected context (use --admiralty for intelligence details)
  context               | [--events] [--entities]      | Show temporal event stream / entity registry (v0.9)
  context               | save|load [file]             | Persist / restore intelligence state (v0.9)
  scan                  | <ip> <mode> ...              | Port scan (normal/slow/banner/subnet)
  netscan               | <ip/network> [--ports] [--geo] [--map] | Network discovery with port/geo/map (v0.9)
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
  phone                 | <number> [person]            | Phone analysis: format, operator prefix & candidate link (v0.9)
  social                | <username> [person]          | Username OSINT: multi-platform correlation (v0.9)
  org                   | <company> [domain] [person]  | Organization intelligence: domain/personnel mapping (v0.9)
  academic              | <name_or_email>              | Academic intelligence: OpenAlex, ORCID, publications (v0.9)
  wallet                | <address> [chain] [person]   | Crypto wallet analysis: format, chain, balance (v0.9)
  breach                | <email> [--sources=X,Y]      | Breach intelligence: Firefox Monitor + k-anonymity (v0.9)
  github                | <username> [person]          | GitHub intelligence: profile, repos, email correlation (v0.9)
  wayback               | <url>                        | Wayback Machine: web history & snapshots (v0.9)
  geoint                | map|graph|timeline|export    | Geographical map / relationship graph visualization (v0.9)
  resolve               | <name_or_entity>             | Entity resolution: identity clustering (v0.9)
  pivot                 | <entity> [--depth=N]         | Cross-entity pivoting: BFS graph traversal (v0.9)
  pol                   | analyze|compare|casefile|timeline | Pattern of Life behavioral analysis (v0.9)
  vault                 | show|events|confirm|stats    | Intelligence vault: persistent memory (v0.9)
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
    - Use 'context --events' for temporal event stream (Pattern of Life basis)
    - Use 'context --entities [type]' for entity registry summary
    - Use 'context save/load' for session persistence
    - Use 'geoint map/graph' for visualization (open HTML in browser)
    - Use 'pol analyze <entity>' for behavioral analysis
    - Use 'vault show' for persistent memory stats
    - Default export path: logs/nexus_report.html | logs/nexus_neo4j.json | logs/nexus_graph.json
    - phone/social/org/wallet module relations are CANDIDATE — not confirmed ownership (v0.9)
================================================================================
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

# 2. Human-centric intelligence (v0.9)
corvus > phone +905321234567 ahmet
corvus > social johndoe
corvus > org "Acme Corp" acme.com ahmet
corvus > academic ahmet@itu.edu.tr
corvus > wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa ahmet
corvus > breach ahmet@example.com --sources=LinkedIn,Adobe
corvus > github octocat
corvus > wayback example.com

# 3. Entity resolution & pivoting (v0.9)
corvus > resolve ahmet
corvus > pivot ahmet --depth=3

# 4. Inspect the live graph
corvus > context
corvus > context --admiralty
corvus > context --events
corvus > context --entities

# 5. Run Nexus correlation & risk analysis
corvus > nexus analyze
corvus > nexus analyze --verbose

# 6. Visualize (v0.9)
corvus > geoint map
corvus > geoint graph
corvus > geoint timeline ahmet
corvus > geoint export

# 7. Pattern of Life analysis (v0.9)
corvus > pol analyze ahmet
corvus > pol compare ahmet 8.8.8.8
corvus > pol casefile ahmet

# 8. Persist intelligence (v0.9)
corvus > context save
corvus > vault show
corvus > vault confirm ahmet

# 9. Export results
corvus > nexus export html
corvus > nexus export json
corvus > nexus export graph
```

---

## Three-Layer Intelligence Architecture (v0.9)

```
┌─────────────────────────────────────────────────────────────┐
│  1. SESSION CONTEXT (RAM — temporary)                      │
│  ┌─────────────────────────────────────────────┐            │
│  │  context.data                              │            │
│  │  • entities (session entities)              │            │
│  │  • events (buffer, max 10.000)              │            │
│  │  • relations / notes                        │            │
│  │  Lost on session end.                       │            │
│  └──────────────────┬──────────────────────────┘            │
│                     │ context save/load                     │
│                     ▼                                       │
│  2. INTELLIGENCE VAULT (Disk — persistent)                  │
│  ┌─────────────────────────────────────────────┐            │
│  │  vault/events.log      (append-only JSONL)   │            │
│  │  vault/index.json      (entity/action index) │            │
│  │  vault/state.json      (entity inventory)    │            │
│  │  vault/evidence/       (case files)          │            │
│  │  Survives sessions — The Machine's memory.   │            │
│  └──────────────────┬──────────────────────────┘            │
│                     ▼                                       │
│  3. POL ENGINE (Analysis — reads from vault)                │
│  ┌─────────────────────────────────────────────┐            │
│  │  core/pol.py                               │            │
│  │  • Activity rhythm                          │            │
│  │  • Movement pattern                         │            │
│  │  • Communication pattern                    │            │
│  │  • Anomaly detection (hybrid)               │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

Runtime config lives in `config/config.json`:

```json
{
  "log_level": "INFO",
  "threads": 20,
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.9",
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

Centralized rules live in `config/rules.json` (v0.9):

```json
{
  "evidence_weights": { "phone_verified": 30, "breach_correlation": 25, ... },
  "source_reliability": { "phone_intel": "B", "social_intel": "C", ... },
  "relationship_policies": {
    "phone_to_person": {"type": "candidate", "default_confidence": 0.4},
    "username_match": {"type": "possible", "base_confidence": 0.15, "boost_per_platform": 0.1, "max": 0.7},
    ...
  },
  "geoint": { "default_map_path": "logs/geo_map.html", ... },
  "pol": { "anomaly_threshold": 70, "vault_dir": "vault", ... },
  "node_colors": { "ip": "#06b6d4", "person": "#ef4444", ... }
}
```

---

## Ethical Design (v0.9)

- **Candidate/possible model** — Phone/email/username/org/wallet links are CANDIDATE, not confirmed ownership. Confidence scores reflect uncertainty.
- **Breach meta-data only** — No raw credentials, credit cards, or personal content stored. Only "which breach lists this email appears in."
- **k-anonymity** — HIBP Pwned Passwords: full password never transmitted, only 5-char SHA-1 prefix.
- **Public OSINT only** — All data from publicly available sources (geoip, social media, certificate transparency, GitHub, Wayback, OpenAlex).
- **VPN warning** — Movement analysis always warns about possible VPN/recording errors.
- **Educational purpose** — For authorized security research and learning only.

---

## Roadmap

- **Real-time monitoring** — Live data streams for continuous POL analysis.
- **Neo4j integration** — Direct push to a running Neo4j instance via Bolt protocol.
- **Machine learning** — Automated evidence weighting and confidence prediction.
- **PDF export** — Printable intelligence dossier alongside HTML.
- **Multi-user collaboration** — Shared intelligence vaults.

---

## Disclaimer

This project is for educational and authorized security research purposes only. Unauthorized use is strictly prohibited.