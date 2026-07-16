# Corvus Corax v0.8 — Architecture Documentation

This directory contains detailed technical documentation about the Corvus Corax system architecture, including component design, data flow, integration patterns, and implementation details.

## System Overview

Corvus Corax is a modular reconnaissance and intelligence analysis framework built on a centralized intelligence graph architecture. The system is designed to collect, normalize, correlate, and export reconnaissance data through a unified intelligence flow with NATO-standard confidence scoring.

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

### 2. Context Manager (`core/context.py`)

The `ContextManager` maintains a centralized intelligence graph updated by every module.

**Data Structure**:
```python
{
    "ips": {
        "ip_address": {
            "ports": [...],
            "geo": {...},
            "hostname": "..."
        }
    },
    "domains": {
        "domain": {
            "ips": [...]
        }
    },
    "certificates": {...},
    "dns_records": {...},
    "http_headers": {...},
    "email_intel": {...},
    "metadata_intel": {...},
    "asn_intel": {...},
    "tech_intel": {...},
    "notes": [...],
    "relations": [...],
    "derived_relations": [...],
    "meta": {
        "created_at": "...",
        "updated_at": "...",
        "event_count": 0,
        "recent_events": [...]
    }
}
```

**Key Methods**:
- `add_ip()`, `add_domain()`, `add_port()`
- `add_certificate()`, `add_dns_record()`, `add_http_headers()`
- `add_email_intel()`, `add_metadata_intel()`, `add_asn_intel()`
- `add_tech_intel()`
- `add_note()`, `add_relation()`, `add_derived_relation()`
- `get_clean_data()` for Nexus compatibility
- `get_admiralty_summary()`, `get_entity_admiralty()`

### 3. Nexus Engine (`core/nexus.py`)

The `NexusEngine` performs correlation and risk scoring using Admiralty confidence scoring.

**Correlation Rules**:
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

### 4. Nexus Exporter (`core/exporter.py`)

The `NexusExporter` generates reports in multiple formats.

**Export Formats**:
- **HTML**: Interactive intelligence dossier with tabs
- **Neo4j JSON**: Graph database import format
- **Graph JSON**: AI/ML pipeline format

**HTML Export Features**:
- Executive Summary tab
- Risk Profiles tab with expandable cards
- Graph Relations Explorer tab
- Glassmorphism dark UI
- No external dependencies

**Neo4j JSON Format**:
```json
{
  "nodes": [
    {
      "id": "ip:192.168.1.1",
      "label": "IP",
      "properties": {
        "value": "192.168.1.1",
        "risk_score": 75,
        "risk_level": "High"
      }
    }
  ],
  "relationships": [
    {
      "id": "rel_1",
      "type": "RESOLVES_TO",
      "startNode": "domain:example.com",
      "endNode": "ip:192.168.1.1",
      "properties": {
        "evidence": "A record",
        "confidence": 1.0
      }
    }
  ]
}
```

**Graph JSON Format**:
```json
{
  "metadata": {
    "version": "0.8",
    "format": "corvus_graph_v1",
    "generated_at": "2024-01-01T00:00:00Z"
  },
  "nodes": [
    {
      "id": "ip:192.168.1.1",
      "type": "ip",
      "value": "192.168.1.1",
      "properties": {
        "risk_score": 75,
        "admiralty_rating": "B2",
        "evidence_count": 4,
        "asn": "AS15169",
        "organization": "Google Cloud"
      }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "domain:example.com",
      "target": "ip:192.168.1.1",
      "relation": "resolves_to",
      "properties": {
        "evidence": "dns mapping",
        "confidence": 1.0,
        "derived": false
      }
    }
  ]
}
```

### 5. Output Manager (`output/output_manager.py`)

The `OutputManager` handles terminal presentation and formatting.

**Output Modes**:
- **Text**: Colored terminal output with ANSI codes
- **JSON**: Raw JSON payload for programmatic use

**Module-Specific Formatting**:
- Each module has custom formatting logic
- Nexus supports verbose mode for detailed evidence chains
- Color-coded severity indicators
- Structured section dividers

### 6. Configuration System (`config/config.json`)

Runtime configuration for all components.

**Configuration Structure**:
```json
{
  "log_level": "INFO",
  "threads": 20,
  "timeout": 3.0,
  "user_agent": "CorvusCorax/0.8",
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

### 7. Module Loader (`core/loader.py`)

Dynamic module loading system.

**Loading Process**:
1. Scan `modules/` directory for Python files
2. Import each module file
3. Identify classes inheriting from `BaseModule`
4. Store in dictionary keyed by module name
5. Handle duplicate module names

### 8. Logger (`core/logger.py`)

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
├─ Add Domain Data                 └─ Log Summary
├─ Add IP Data
├─ Add Tech Intel
└─ Add ASN Intel
```

### Nexus Correlation Flow

```
ContextManager.get_clean_data()
    ↓
NexusEngine.correlate()
    ↓
Apply 12 Correlation Rules
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
```

### Nexus-Context Integration

Nexus Engine reads from and writes to `ContextManager`:

1. **Read**: `get_clean_data()` for normalized data
2. **Write**: `add_derived_relation()` for inferred relationships
3. **Read**: Risk profiles for export

### Exporter-Context Integration

Nexus Exporter reads from both `ContextManager` and Nexus report:

1. **Context Data**: Raw intelligence data
2. **Nexus Report**: Risk profiles and derived relations
3. **Output**: Formatted export files

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

## Testing Strategy

### Unit Testing

- Test individual module logic
- Test correlation rules
- Test scoring algorithms
- Mock external dependencies

### Integration Testing

- Test module-context integration
- Test nexus-context integration
- Test exporter-context integration
- Test full workflow

### End-to-End Testing

- Test complete reconnaissance workflows
- Test export functionality
- Test CLI interface
- Test error handling

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

### Logging

Logs stored in `logs/corvus.log`.

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
