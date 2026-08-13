# Corvus Corax v0.9 — Architecture Documentation

This directory contains detailed technical documentation about the Corvus Corax system architecture, including component design, data flow, integration patterns, and implementation details.

## System Overview

Corvus Corax is a modular reconnaissance and intelligence analysis framework built on a centralized intelligence graph architecture. The system is designed to collect, normalize, correlate, and export reconnaissance data through a unified intelligence flow with NATO-standard confidence scoring.

**v0.9** transforms the system from a network-focused recon tool into a **human-centric intelligence platform** with:
- Entity-agnostic intelligence graphs (persons, organizations, phones, emails, wallets, locations)
- Temporal event stores for Pattern of Life (POL) analysis
- Candidate/possible relationship modeling (not confirmed ownership)
- Persistent Intelligence Vault (The Machine's long-term memory)
- GEOINT map visualization and D3.js relationship graphs
- Entity resolution, cross-entity pivoting, and confidence aggregation

## Core Components

### 1. Module System (`core/module_base.py`)

All modules inherit from `BaseModule`, providing a standardized interface for intelligence collection.

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

**Key Features**:
- Standardized payload format
- Context integration via `ContextManager`
- Note and relationship management
- Error handling and logging
- Configuration-driven behavior

**v0.9 Extensions**:
- `add_entity()` — entity-agnostic entity creation
- `add_person()`, `add_phone()`, `add_email()`, `add_social_profile()`, `add_wallet()`, `add_organization()`
- `log_event()` — temporal event logging for POL analysis
- `add_location()` — geographic location entities

### 2. Context Manager (`core/context.py`)

The `ContextManager` maintains a centralized intelligence graph updated by every module.

**v0.9 Data Structure**:
```python
{
    "entities": {          # Entity-agnostic registry
        "person:ahmet": {"type": "person", "value": "ahmet", "properties": {...}},
        "ip:8.8.8.8": {"type": "ip", "value": "8.8.8.8", "properties": {...}},
        "phone:+90532...": {"type": "phone", "value": "+90532...", "properties": {...}},
        ...
    },
    "events": [            # Temporal event store (POL basis)
        {"timestamp": "...", "entity": "person:ahmet", "action": "located_in", "source": "geoip", "metadata": {...}}
    ],
    "ips": {...},          # Legacy (backward compatible)
    "domains": {...},      # Legacy
    "notes": [...],
    "relations": [...],
    "derived_relations": [...],
    "meta": {...}
}
```

**Key Methods**:
- `add_entity()`, `get_entity()`, `query_entities()` — entity-agnostic
- `add_person()`, `add_organization()`, `add_phone()`, `add_email()`, `add_social_profile()`, `add_wallet()`, `add_location()`
- `add_event()`, `query_events()`, `get_entity_events()` — temporal event store
- `add_ip()`, `add_domain()`, `add_port()` — legacy
- `add_note()`, `add_relation()`, `add_derived_relation()`
- `get_clean_data()` for Nexus compatibility
- `get_events_summary()`, `get_entities_summary()` — v0.9 views

### 3. Nexus Engine (`core/nexus.py`)

The `NexusEngine` performs correlation and risk scoring using Admiralty confidence scoring.

**Correlation Rules (v0.9 — Rule 1-20)**:
- **RULE 1**: Subnet correlation (IPs in same /24)
- **RULE 2**: Shared technology stack
- **RULE 3**: Outdated software detection
- **RULE 4**: High-risk exposure (outdated + admin ports)
- **RULE 5**: Shared certificate detection
- **RULE 6**: Software stack profiling
- **RULE 7**: Web security posture assessment
- **RULE 8**: Email leak profiling
- **RULE 9**: Shared favicon pivoting
- **RULE 10**: Metadata contact mapping
- **RULE 11**: Technology stack correlation
- **RULE 12**: ASN intelligence correlation
- **RULE 13**: Phone → Person candidate association (conflicting_phone_claim)
- **RULE 14**: Username → Person possible match aggregation (likely_same_person)
- **RULE 15**: Email → Person candidate association (multi_source_associated)
- **RULE 16**: Organization → Domain ownership aggregation (owns_multiple_domains)
- **RULE 17**: Academic affiliation correlation (same_affiliation)
- **RULE 18**: Wallet multi-owner conflict detection
- **RULE 19**: GitHub email correlation aggregation
- **RULE 20**: Wayback web history correlation

**Risk Calculation**:
```python
def calculate_risk(self, entity):
    evidence_chain = []
    total_weight = 0
    
    for evidence in entity_evidence:
        scorer = AdmiraltyScorer()
        score = scorer.calculate_score(
            evidence_type=evidence["type"],
            source_reliability=evidence["source"],
            info_reliability=evidence["info"]
        )
        evidence_chain.append(score)
        total_weight += score["weighted_score"]
    
    risk_score = min(100, total_weight)
    admiralty_rating = self._calculate_admiralty_code(risk_score)
    
    return {
        "score": risk_score,
        "level": self._get_risk_level(risk_score),
        "admiralty_rating": admiralty_rating,
        "evidence_count": len(evidence_chain),
        "evidence_chain": evidence_chain
    }
```

### 4. Intelligence Vault (`core/db.py` — v0.9)

The `IntelligenceVault` provides persistent, cross-session memory — The Machine's long-term memory.

**Three-Layer Architecture**:
```
1. Session Context (RAM)     — temporary, lost on session end
2. Intelligence Vault (Disk) — persistent, confirmed evidence
3. POL Engine (Analysis)     — reads from vault, extracts behavior patterns
```

**Data Model**:
```
vault/
├── events.log              # Append-only JSONL (each line = one event)
├── index.json              # {entity: [line_numbers], action: [line_numbers]}
├── state.json              # Entity inventory (entities, relations, notes)
├── evidence/               # Confirmed evidence chains (case files)
└── stats.json              # Vault statistics
```

**Key Methods**:
- `append_event()` — append-only event logging with evidence threshold filter
- `query_events()` — index-based event querying
- `confirm_event()` — promote session event to persistent evidence
- `save_state()` / `load_state()` — entity inventory persistence
- `get_casefile()` / `save_casefile()` — investigation dossiers
- `stats()` — vault statistics

**Evidence Threshold Filter**:
```python
def should_persist(self, event):
    # Test/keşif aşamasındaki olayları kalıcılaştırma
    if source in ("help", "version", "test"):
        return False
    # Düşük güvenilirlikteki candidate/possible ilişkileri kalıcılaştırma
    if confidence < 0.5 and any(k in action for k in ("candidate", "possible", "conflict")):
        return False
    return True
```

### 5. Pattern of Life Engine (`core/pol.py` — v0.9)

The `PatternOfLifeEngine` analyzes temporal events to extract behavioral patterns.

**Analysis Modules**:
- **Activity Rhythm** — hourly/weekly activity distribution, peak hours, source breakdown
- **Movement Pattern** — location history, routes, VPN warning (same-day multi-location)
- **Communication Pattern** — entity connections and relationship types
- **Anomaly Detection** — hybrid model (rule-based + statistical z-score)
- **Case File** — full investigation dossier

**Hybrid Anomaly Model**:
```python
# Rule-based (explainable)
night_activity: +40  # 03:00-05:00 activity
vpn_warning: +30     # same-day multi-location
candidate_rels: +20  # many unverified candidate links

# Statistical (adaptive)
z_score > 2.0: +10   # deviation from normal activity distribution

# Score: 0-100, Level: LOW/MEDIUM/HIGH
```

### 6. GEOINT Engine (`core/geoint.py` — v0.9)

The `GeoIntEngine` generates interactive Leaflet.js + OpenStreetMap maps.

**Features**:
- IP/person/org markers with popup details
- Movement routes (polyline) for entities with multiple locations
- Heatmap for dense regions
- CDN/offline mode support

### 7. Graph Visualizer (`core/visualizer.py` — v0.9)

The `GraphVisualizer` generates D3.js force-directed relationship graphs.

**Features**:
- Drag, zoom, hover tooltip, detail panel
- Node colors by entity type (from `rules.json`)
- Risk-score-based node sizing
- Search box and legend

### 8. Confidence Aggregation (`core/confidence.py` — v0.9)

The confidence aggregation engine combines weak individual evidence into strong evidence.

**Formula**: `combined = 1 - (1-c1)*(1-c2)*(1-c3)*...`

**Key Functions**:
- `combine_confidences()` — combine multiple confidence scores
- `aggregate_entity_confidence()` — aggregate all candidate/possible links to a target
- `find_identity_clusters()` — find entities belonging to the same person

### 9. Nexus Exporter (`core/exporter.py`)

The `NexusExporter` generates reports in multiple formats.

**Export Formats**:
- **HTML**: Interactive intelligence dossier with tabs
- **Neo4j JSON**: Graph database import format
- **Graph JSON**: AI/ML pipeline format (`corvus_graph_v2`)

### 10. Output Manager (`output/output_manager.py`)

The `OutputManager` handles terminal presentation and formatting.

**Output Modes**:
- **Text**: Colored terminal output with ANSI codes
- **JSON**: Raw JSON payload for programmatic use

**Module-Specific Formatting**:
- Each module has custom formatting logic
- Nexus supports verbose mode for detailed evidence chains
- GEOINT visualization export formatting
- Color-coded severity indicators

### 11. Configuration System (`config/config.json` + `config/rules.json`)

Runtime configuration for all components.

**`config/config.json`** — Runtime settings:
```json
{
  "log_level": "INFO",
  "threads": 20,
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.9",
  "output_mode": "text",
  "scan_defaults": {...}
}
```

**`config/rules.json`** — Centralized rules (v0.9):
```json
{
  "evidence_weights": {"phone_verified": 30, "breach_correlation": 25, ...},
  "source_reliability": {"phone_intel": "B", "social_intel": "C", ...},
  "relationship_policies": {
    "phone_to_person": {"type": "candidate", "default_confidence": 0.4},
    "username_match": {"type": "possible", "base_confidence": 0.15, "boost_per_platform": 0.1, "max": 0.7},
    ...
  },
  "geoint": {"default_map_path": "logs/geo_map.html", ...},
  "pol": {"anomaly_threshold": 70, "vault_dir": "vault", ...},
  "node_colors": {"ip": "#06b6d4", "person": "#ef4444", ...}
}
```

### 12. Module Loader (`core/loader.py`)

Dynamic module loading system.

**Loading Process**:
1. Scan `modules/` directory for Python files
2. Import each module file
3. Identify classes inheriting from `BaseModule`
4. Store in dictionary keyed by module name
5. Handle duplicate module names

### 13. Logger (`core/logger.py`)

File-based logging system.

**Features**:
- Writes to `logs/corvus.log`
- No console output (clean terminal)
- Configurable log levels
- Timestamped entries
- Module-specific logging

## Data Flow

### Module Execution Flow

```
User Input → main.py → Module.execute()
    ↓
Standardized Payload
    ↓
┌─────────────────┴─────────────────┐
│                                   │
ContextManager              OutputManager
│                                   │
├─ Add Notes                       ├─ Format Output
├─ Add Relations                   ├─ Display Terminal
├─ Add Temporal Events             └─ Log Summary
├─ Add Entities
└─ Add Domain Data
```

### v0.9 Intelligence Flow

```
Module Execution
    ↓
ContextManager (Session)
    ├─ entities
    ├─ events (temporal)
    └─ relations
    ↓
Intelligence Vault (Persistent)
    ├─ events.log (append-only)
    ├─ index.json
    └─ state.json
    ↓
Pattern of Life Engine
    ├─ Activity Rhythm
    ├─ Movement Pattern
    ├─ Communication Pattern
    └─ Anomaly Detection
    ↓
GEOINT / Visualizer
    ├─ Interactive Map
    └─ D3.js Graph
```

### Nexus Correlation Flow

```
ContextManager.get_clean_data()
    ↓
NexusEngine.correlate()
    ↓
Apply 20 Correlation Rules
    ↓
Generate Derived Relations
    ↓
NexusEngine.calculate_risk()
    ↓
AdmiraltyScorer.calculate_score()
    ↓
Generate Risk Profiles
    ↓
NexusEngine.generate_report()
    ↓
NexusExporter.export_*()
    ↓
HTML / Neo4j JSON / Graph JSON
```

## Integration Patterns

### Module-Context Integration

Modules integrate with `ContextManager` through:

1. **Direct Data**: Domain-specific data structures
2. **Notes**: Structured observations with confidence
3. **Relations**: Entity-to-entity connections
4. **Temporal Events**: Timestamped events for POL analysis

**Example**:
```python
# Direct data
self.context.add_tech_intel("example.com", tech_data)

# Notes
self.context.add_note(
    text="Outdated nginx version detected",
    source="tech_detect",
    severity="high",
    confidence=0.9
)

# Relations
self.context.add_relation(
    src_type="domain", src_value="example.com",
    relation="runs_on_server",
    dst_type="server", dst_value="nginx",
    evidence="Server header",
    confidence=0.9
)

# Temporal events (v0.9)
self.log_event("phone_analyzed", entity="phone:+905321234567", metadata={...})
```

### Vault-Context Integration

The Intelligence Vault reads from and writes to `ContextManager`:

1. **Read**: `get_clean_data()` for normalized data
2. **Write**: `append_event()` for persistent event logging
3. **Confirm**: `confirm_event()` for manual evidence promotion
4. **Load**: `load_state()` for session restoration

### POL-Vault Integration

The POL Engine reads from both Vault and Session:

1. **Vault events**: Confirmed, persistent evidence
2. **Session events**: Temporary, current-session data
3. **Source labeling**: `_source: vault` vs `_source: session`

## Design Patterns

### 1. Module Pattern

All modules follow the Module Pattern for consistency:

- Abstract base class (`BaseModule`)
- Standardized interface (`execute()`)
- Common initialization parameters
- Normalized return format

### 2. Context Pattern

Centralized state management through `ContextManager`:

- Single source of truth
- Thread-safe operations
- Event tracking
- Data normalization

### 3. Strategy Pattern

Nexus Engine uses Strategy Pattern for correlation rules:

- Each rule is a separate strategy
- Rules can be added/removed independently
- Rules share common interface

### 4. Builder Pattern

Nexus Exporter uses Builder Pattern for report generation:

- Step-by-step report construction
- Multiple export formats
- Reusable components

### 5. Observer Pattern

ContextManager uses Observer Pattern for event tracking:

- Event logging on data changes
- Recent events tracking
- Event count monitoring

### 6. Three-Layer Architecture (v0.9)

The system uses a three-layer intelligence architecture:

- **Session Context (RAM)**: Temporary, fast, lost on session end
- **Intelligence Vault (Disk)**: Persistent, confirmed, survives sessions
- **POL Engine (Analysis)**: Reads from vault, extracts behavior patterns

## Performance Considerations

### Module Performance

- **Timeout Handling**: All modules respect configured timeout
- **Connection Pooling**: Reuse connections where possible
- **Caching**: DNS resolver caching
- **Parallel Processing**: Multi-threaded port scanning

### Nexus Performance

- **Efficient Correlation**: O(n) complexity for most rules
- **Indexing**: Build lookup indices for fast correlation
- **Lazy Evaluation**: Only calculate risk when needed

### Vault Performance

- **Append-only log**: O(1) append, no file rewriting
- **Index-based querying**: `index.json` for fast entity/action lookup
- **Line-number addressing**: Direct file seek for specific events

### Export Performance

- **Streaming**: Large exports use streaming
- **Memory Management**: Efficient data structures
- **Compression**: Optional compression for large exports

## Security Considerations

### Data Privacy

- **No Data Exfiltration**: All data stays local
- **Public APIs Only**: Only use public APIs
- **No Authentication**: No credentials stored
- **Log Sanitization**: Sensitive data not logged

### Ethical Design (v0.9)

- **Candidate/possible model**: Phone/email/username/org/wallet links are CANDIDATE, not confirmed ownership
- **Breach meta-data only**: No raw credentials, credit cards, or personal content stored
- **k-anonymity**: HIBP Pwned Passwords — full password never transmitted, only 5-char SHA-1 prefix
- **Public OSINT only**: All data from publicly available sources
- **VPN warning**: Movement analysis always warns about possible VPN/recording errors

### Input Validation

- **IP Validation**: Validate IP addresses
- **URL Validation**: Validate URL formats
- **Domain Validation**: Validate domain names
- **Path Traversal**: Prevent path traversal attacks

### Error Handling

- **Graceful Degradation**: Continue on partial failures
- **Error Isolation**: Module errors don't crash system
- **Timeout Protection**: All operations have timeouts
- **Rate Limiting**: Respect API rate limits

## Extensibility

### Adding New Modules

1. Create module file in `modules/`
2. Inherit from `BaseModule`
3. Implement `execute()` method
4. Return standardized payload
5. Module auto-loaded by loader

### Adding New Correlation Rules

1. Add rule method to `NexusEngine`
2. Call rule in `correlate()` method
3. Use `add_derived_relation()` for results
4. Update documentation

### Adding New Export Formats

1. Add method to `NexusExporter`
2. Implement data transformation
3. Add CLI command in `nexus.py`
4. Update help documentation

### Adding New Entity Types

1. Use `add_entity()` with new type
2. Add to `node_colors` in `rules.json`
3. Add to `EvidenceType` in `admiralty.py` (if needed)
4. Update documentation

## Testing Strategy

### Unit Testing

- Test individual module logic
- Test correlation rules
- Test scoring algorithms
- Mock external dependencies

### Integration Testing

- Test module-context integration
- Test nexus-context integration
- Test vault-context integration
- Test POL-vault integration
- Test full workflow

### End-to-End Testing

- Test complete reconnaissance workflows
- Test export functionality
- Test CLI interface
- Test error handling
- Test persistence (save/load)

## Deployment

### Requirements

- Python 3.7+
- Standard library only (no external dependencies for core)
- Optional: dnspython for DNS module

### Installation

```bash
git clone https://github.com/username/corvus_corax.git
cd corvus_corax
python main.py
```

### Configuration

Edit `config/config.json` for custom settings.
Edit `config/rules.json` for centralized rules (v0.9).

### Logging

Logs stored in `logs/corvus.log`.

### Persistence

Intelligence Vault stored in `vault/` directory (v0.9).

## Future Architecture Enhancements

### 1. Plugin System

- Dynamic plugin loading
- Plugin marketplace
- Plugin versioning
- Plugin dependencies

### 2. Database Backend

- SQLite/PostgreSQL support
- Persistent context storage
- Query optimization
- Data retention policies

### 3. Distributed Processing

- Multi-node processing
- Task queue system
- Result aggregation
- Load balancing

### 4. API Layer

- REST API interface
- WebSocket support
- Authentication/Authorization
- Rate limiting

### 5. Web Interface

- React-based UI
- Real-time updates
- Interactive graphs
- Report generation

### 6. Real-time Monitoring

- Live data streams for continuous POL analysis
- Real-time anomaly detection
- Alerting system