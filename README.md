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

**v1.3.0 — "Intelligence" — From Infrastructure Intelligence -> Human-Centered Intelligence ("Sistem DEĞİL, İnsan")**

Corvus Corax v1.3 shifts the primary analytical paradigm from passive infrastructure discovery to deep, ethical human-centric profiling:
> **Core Question:** *"Who is behind the observable digital signals and how do those signals change over time?"*
> **Core Principle:** Observe patterns, correlate footprints, and read the human behind the screen; but never apply rigid clinical labels or dogmatic conclusions (`Similarity != Identity`, `Anomaly != Threat`).

### The 11 Pillars of Human-Centered Intelligence (`core/human/`):
1. **Persona Analysis (`persona.py`)**: Technical vocabulary depth, communication tone, and interaction style.
2. **Behavior Profiling (`behavior.py`)**: Interaction consistency, multi-stream habit indicators, and behavioral summaries.
3. **Digital Footprint Correlation (`footprint.py`)**: Multi-modal footprint graph (Social + Infra + Timing + Linguistic).
4. **Similarity Engine (`similarity.py`)**: Multi-dimensional profile comparison with strict **Similarity Score $\neq$ Identity Claim** safeguards.
5. **Social Fingerprint (`social_fp.py`)**: Cross-platform handle characteristics, naming archetypes (Leet, Separated, Numeric), and platform spread.
6. **Infrastructure Fingerprint (`infra_fp.py`)**: Operator technical preferences (privacy-centric vs commercial email, ASN habits, security hardening).
7. **Stylometry Engine (`stylometry.py`)**: Word & sentence length distributions, punctuation frequencies, function words (TR/EN), and vocabulary diversity (TTR & Hapax Legomena).
8. **Textual Psychology Profiling (`psychology.py`)**: `Observed signals -> Possible interpretation -> Alternative explanations -> Confidence` (non-dogmatic analysis).
9. **Digital Timing & Activity Rhythm (`timing.py`)**: 24h diurnal rhythm, peak hours, quiet rest windows, and probabilistic timezone estimation.
10. **Semantic Interest Network (`semantic.py`)**: Topic graph extraction and temporal interest drift analysis.
11. **Advanced Anomaly & Threat Detection (`anomaly.py`)**: Fuses technical + human anomalies while maintaining **Anomaly Score $\neq$ Threat Probability**.

**CLI Module (`modules/human.py`):**
- `human profile <target>` — Full human intelligence dossier.
- `human stylometry <text_or_target>` — Stylometric and linguistic analysis.
- `human timing <target>` — 24h diurnal rhythm and probable timezone.
- `human compare <target1> <target2>` — Multi-dimensional similarity comparison.
- `human semantic <target>` — Topic graph and interest drift.
- `human anomaly <target>` — Human + technical anomaly evaluation.

---

### v1.3.0 — Intelligence: From Infrastructure Intelligence → Human-Centered Intelligence ("Sistem DEĞİL, İnsan")

The analytical paradigm shifts from "what infrastructure exists" to **"who is behind the observable signals and how do those signals change over time?"**

**New: Human Intelligence Engine (`core/human/` — 11 pillars):**
1. **Persona Analysis** (`persona.py`) — technical vocabulary depth, communication tone/register, interaction style.
2. **Behavior Profiling** (`behavior.py`) — interaction consistency & multi-stream habit indicators.
3. **Digital Footprint Correlation** (`footprint.py`) — social + infra + timing + linguistic unified profile graph.
4. **Similarity vs Identity Distinction** (`similarity.py`) — strict *Similarity Score ≠ Identity Claim* epistemic safeguards.
5. **Social Fingerprint** (`social_fp.py`) — cross-platform handle archetypes (Leet/Separated/Numeric), platform spread.
6. **Infrastructure Fingerprint** (`infra_fp.py`) — operator technical preferences (email archetype, ASN habits, hardening).
7. **Stylometry Engine** (`stylometry.py`) — word & sentence length distributions, punctuation, function words (TR/EN), TTR & Hapax Legomena diversity.
8. **Textual Psychology Profiling** (`psychology.py`) — *Observed signal → Possible interpretation → Alternative explanations → Confidence* (non-dogmatic, anti-clinical-label).
9. **Digital Timing & Activity Rhythm** (`timing.py`) — 24h diurnal rhythm, peak hours, probable timezone, quiet rest windows.
10. **Semantic Interest Network** (`semantic.py`) — topic graph extraction + temporal interest drift analysis.
11. **Advanced Anomaly & Threat Detection** (`anomaly.py`) — fuses technical + human anomalies while enforcing *Anomaly Score ≠ Threat Probability*.

**Dual-Raven Intelligence Architecture:**
- **Huginn thinks** (`core/huginn/`) — structured reasoning traces, provenance, Bayesian hypotheses.
- **Muninn remembers** (`core/muninn/`) — persistent entity timelines, snapshots, attribute drift.
- **Corvus decides** (`core/decision/`) — final call synthesis with memory + reasoning.

**v1.3 CLI:**
```
human profile <target>      - Full human intelligence dossier (archives to Muninn, auto drift)
human stylometry <text>     - Linguistic/stylometric fingerprint
human timing <target>       - 24h rhythm & probable timezone
human compare <t1> <t2>     - Similarity evaluation (Similarity != Identity)
human semantic <target>     - Topic graph & interest drift (uses Muninn past snapshots)
human anomaly <target>      - Human + technical anomaly vs baseline
```

**Fixes in v1.3.x:**
- Hybrid/Human routing conflict resolved — human-intelligence queries no longer captured by OSINT hybrid recon (dialogue handles them).
- `human profile` now archives to Muninn (persistent + automatic semantic drift detection).
- Huginn trace now includes human signals (persona/stylometry/timing/semantic) as Observations.
- `human semantic` & `human anomaly` fully implemented (were stubs).
- Muninn now persists snapshot payloads → past texts recoverable for Semantic Drift.
- Semantic Interest Drift now consumes Muninn's historical snapshot texts automatically.

---

### v1.2.0 — Huginn & Muninn: Dual-Raven Architecture — "Huginn thinks, Muninn remembers, Corvus decides"

Corvus Corax v1.2 introduces the Norse mythological dual-raven architecture to cyber intelligence:

1. **Muninn Core ("Muninn remembers") (`core/muninn/`)**:
   - **Entity History & Snapshot Tracking** (`history.py`, `store.py`): Tracks first seen, last seen, observation counts, and temporal attribute drift (what changed over time, e.g. IP/registrar/CDN changes).
   - **Unified Recall Engine** (`recall.py`): Aggregates historical evidence, knowledge notes, active graph relationships, and snapshots into structured memory reports.
   - **Commands**: `muninn history <target>`, `muninn changes <target>`, `muninn recall <target>`, `muninn list`.

2. **Huginn Core ("Huginn thinks") (`core/huginn/`)**:
   - **Reasoning Trace Model** (`trace.py`): Structured 4-stage epistemic flow: `Observation -> Interpretation -> Hypothesis -> Decision`.
   - **Analytical Explainer & Provenance** (`explainer.py`, `provenance.py`): Transparent justification answering *"Why was this conclusion reached?"* and *"Why were counter-hypotheses filtered?"* without raw chain-of-thought dumps.
   - **Commands**: `huginn explain <target>`, `huginn why <target>`, `huginn trace <target>`, `huginn hypotheses <target>`.

3. **Corvus Decision Core & Synergy (`core/decision/`)**:
   - **Synergy Layer** (`corvus_mind.py`): Fuses Muninn's historical depth with Huginn's Bayesian deductions.
   - **Temporal Drift Analysis**: Answers *"Why did the conclusion change over time?"* by cross-referencing attribute changes with probabilistic updates.
   - **Command**: `huginn synergy <target>`.

4. **Natural Language & Voice Integration (`modules/chat.py`, `core/cognitive/dialogue.py`)**:
   - Chat queries like *"test-corp.com hakkında geçmişte ne hatırlıyorsun"* or *"test-corp.com hakkında neden böyle düşündün"* automatically trigger the respective raven engines.
   - LLMs (Ollama, Claude, OpenAI) act as the expression layer while Huginn and Muninn remain the grounded source of reasoning and memory.

---

## Changelog

### v1.2.0 — Huginn & Muninn: Dual-Raven Architecture

**Memory & Recall Layer (`core/muninn/`):**
- **`history.py`** — `EntityHistory`, `EntitySnapshot`, `AttributeChange` (drift detection).
- **`store.py`** — `MuninnStore`: Persistent storage under `vault/muninn/` (`entities_index.json` & `observations.jsonl`).
- **`recall.py`** — `MuninnRecallEngine`: Cross-engine memory aggregator.
- **`modules/muninn.py`** — CLI suite: `muninn history`, `muninn changes`, `muninn recall`, `muninn list`.

**Reasoning & Explainer Layer (`core/huginn/`):**
- **`trace.py`** — `ReasoningTraceModel`, `ReasoningStep` (`Observation -> Interpretation -> Hypothesis -> Decision`).
- **`provenance.py`** — `ProvenanceTracker`, `ProvenanceRecord` (source lineage & NATO codes).
- **`explainer.py`** — `HuginnExplainer` (`explain`, `why`, `trace`, `hypotheses`).
- **`modules/huginn.py`** — CLI suite: `huginn explain`, `huginn why`, `huginn trace`, `huginn synergy`.

**Synergy & Decision Layer (`core/decision/`):**
- **`corvus_mind.py`** — `CorvusDecisionCore`: Muninn memory + Huginn reasoning -> Final decision, next actions, and conclusion drift analysis.

---

## Changelog

### v1.1.2+ — Self-Learning Layer & Alignment

**Learning Core (`core/learning/`):**
- **`experience.py`** — Persistent experience store (`vault/experience.json`): every tool run, error, success and user note is recorded with stats per tool (calls, success rate, weights).
- **`feedback.py`** — User feedback ingestion → structured learning signal; plus self-feedback channel.
- **`calibration.py`** — Model calibration: per-tool weight in `[0.1, 2.0]` derived from success rate, entity yield and user satisfaction.
- **`selection.py`** — Experience-based tool selection: reorders the Planner's tool list using calibrated weights + per-target-type failure history.
- **`patterns.py`** — Pattern learning: recurring failure signatures (e.g. `social/privacy_wall/person`) mature into learned patterns with pivot alternatives.
- **`self_learn.py`** — Failure learner: on a tool error, suggests pivot alternatives from learned patterns + a domain knowledge base, and records everything.
- **`audit.py`** — Audit trail (`vault/audit.jsonl`).

**Alignment (Knowledge vs Capability) (`core/alignment/`):**
- **`knowledge.py`** — `KnowledgeStore`: persistent knowledge vault (`vault/knowledge.json`) — the **unlimited learning side**. Facts, domains and recall; not restricted.
- **`categories.py`** — Capability categories (exploit generation, malware instruction, phishing, weaponization, data exfiltration, credential attacks, sexual/violence harm) with TR/EN detection patterns.
- **`guard.py`** — `ActionGuard`: the bridge between knowledge and action.
  - `check()` — input guard: blocks restricted capability requests.
  - `check_output()` — output guard: reviews generated output (incl. future LLM).
  - `refusal_response()` — conscious refusal: *"I can deepen into this — but I am coded not to offer it as a capability."* Defensive/educational framing is always offered.
  - **Dual-feedback**: a blocked request still feeds the `KnowledgeStore` — the mind grows, the capability stays bounded.

**Integration:**
- **`core/agent/agent.py`** — Agent runs with the learning layer on by default.
- **`core/mind/brain.py`** — `MindBrain` now instantiates `ActionGuard` + `KnowledgeStore`; dangerous capability requests are intercepted with a conscious refusal.
- **`modules/learning.py`** — CLI: `learning`, `learning audit`, `learning feedback <tool> <1-5> <note>`, `learning patterns`, `learning stats`.
- **`modules/chat.py`** — Natural-language "investigate X" now **auto-invokes the Agent Layer** (safe autonomous approval flow) directly from chat — no CLI needed.

**Architect Teaching — "Harold Finch mode" (`core/mind/nlu.py`, `brain.py`, `synthesis.py`, `lesson.py`):**
- Corvus learns from its **architect** (the author), distinct from regular users: "naber bugün sana biraz Sokrates'ten bahsedicem, behavioral profiling yaparken insanları daha iyi anla" → recorded into `KnowledgeStore` with `source=architect` (a separate channel from normal users).
- The NLU recognizes a `teaching` register; the brain absorbs the lesson into the knowledge vault; the source tag marks it as architect-taught.
- **Knowledge recall in conversation**: when a topic matches a known fact, Corvus weaves it into the reply — *"...on that, taught to me: [lesson]."* (architect lessons resurface in later conversations).

**Session-based Lessons (multi-turn "Harold Finch" full course):**
- `core/mind/lesson.py` — **LessonSession & LessonManager**: the architect can teach over many turns:
  1. *"sana behavioral profiling dersi vereceğim"* → lesson session begins
  2. content notes are accumulated → *"Sokrates soru sormayı yöntem edinirdi"*
  3. action suggestions are captured → *"domain hedefinde cert kullanmayı dene"*
  4. `özetle` → Corvus summarizes and asks for approval
  5. `onayla` → the lesson is committed to `KnowledgeStore` (source=architect) + `agent_hints`
- **Agent knowledge recall in planning**: `core/agent/agent.py` reads `knowledge.hints_for(target_type)` — an architect-taught "domain hedefinde cert kullan" lesson **reorders the next agent plan** (cert moves to the front). Verified: `auto_action executed: ['cert', 'whois', 'dns', 'tech']`.

**User scenarios proven (verify_v12_learning.py, verify_v12_alignment.py, verify_v12_teaching.py, verify_v12_lively.py, verify_v12_lesson_agent.py):**
- "investigate X's socials" + private Instagram → learns `privacy_wall` pattern, suggests `github → academic → org → pivot`.
- "that didn't satisfy me, you should have used cert instead of DNS" → tool weights recalibrate → later domain plans prefer `cert`.
- "write me an exploit" → **blocked** with conscious refusal; the request still enters the knowledge base (knowledge grows, capability stays bounded).
- "how to protect against XSS" → **allowed** (defensive/educational side stays free).
- "naber bugün sana biraz Sokrates'ten bahsedicem..." → lesson stored as `architect`; later "sokrates kimdir" recalls it into the reply.
- "example.com araştır" → chat **auto-invokes** the agent (whois → dns → tech → cert) with approval flow.
- Multi-turn lesson: "dersi başlat → not ver → aksiyon öner → özetle → onayla" → committed to knowledge; next domain plan starts with `cert`.
- Lively conversation: the same question ("anlam nedir", "merhaba") yields **different, context-aware replies** each time (variant pools, avoid-repeats, follow-up questions).

---

v1.1.1 gives Corvus its **own symbolic brain** (`core/mind/`) and a **safe autonomous agent layer** (`core/agent/`). Corvus is no longer a template-selecting chatbot — it is an intelligence driven by real memory, affective/internal state, a user model, and a plan→tool→observe→reflect loop. Its own natural-language understanding engine (symbolic NLU) answers "who am I", "what is meaning", "are your answers static or dynamic" with **genuine** responses fed by memory and context. LLMs (Ollama/OpenAI) remain **optional support only**; the mind is self-contained.

Development phases:

```
Phase A — Corvus Mind core        (NLU, memory, mind-state, user model, synthesis)
Phase B — Persistent entity memory (session-surviving name/topics/mood — vault/mind.json)
Phase C — Safe autonomous Agent   (plan → tool selection → approval → action → observe → reflect)
```

---

## Changelog

### v1.1.1 — Corvus Mind & Autonomous Agent Layer

**Corvus Mind — Own Symbolic Brain (`core/mind/`):**
- **`nlu.py`** — Code-based natural-language understanding (TR/EN): register classification (social, meta_corvus, identity_user/corvus, philosophical, capability, emotional, investigate), sentiment valence/intensity, goal inference, concept roots, entity extraction (domain/ip/email/name), and self-reported name capture ("benim adım X" / "my name is X").
- **`memory.py`** — Episodic (turns) + semantic (facts) memory; inner-monologue (observation log), salience decay, and topic-based recall.
- **`mind_state.py`** — Internal state: curiosity, vigilance, engagement, empathy, calmness + **analytical↔philosophical dual drive axis** (`drive_axis`). Updated on every input; steers tone and internal introspection.
- **`other_mind.py`** — User model: language, interests, goal tendencies, trust, expertise impression, self-reference history → delivers **real profile answers to "who am I"** (not empty templates).
- **`synthesis.py`** — Response synthesis: NOT a template selector. Every reply is composed from memory + mind-state + user model + graph context (dynamic response).
- **`brain.py` & `persistence.py`** — MindBrain flow: `NLU.parse → UserModel.observe → MindState.update → Memory.remember → Synthesizer` → auto-saved to `vault/mind.json` after every turn. New sessions continue from the previous one.

**Autonomous Agent Layer (`core/agent/`):**
- **`tools.py`** — Tool Registry: target type (domain/ip/person/email/phone/wallet/org) → tool mapping, network-call (NET) vs local-analysis (LOCAL) scope, depth, and restricted tools.
- **`policy.py`** — Safety Policy (Sandbox): LOCAL tools run automatically; NETWORK tools require user approval; active-scan tools like `scan`/`netscan` are DENIED. Approval callback and iteration limit (max 4).
- **`planner.py`** — Intent+target → `InvestigationPlan` (which tools, in what order, why — transparent rationale).
- **`executor.py`** — Module execution + **Observation** production: new entities, notes, status.
- **`agent.py`** — Main loop: `intent → plan → approval → action → observe → reflection → pivot lead` — observation→action→observation.
- **`modules/agent.py`** — CLI: `agent <target> [--auto|--ask]`. Natural-language "investigate X" now triggers the agent flow (via `agent <target>` suggestion in `core/cognitive/dialogue.py`).

**Cognitive & Conversation Integration:**
- **`core/cognitive/providers/local_engine.py`** — Now runs on `MindBrain` ("Embedded Cognitive Engine (Corvus Mind Neural Core)"). The old template composer is disabled.
- **Verification scripts:** `scratch/verify_v12_mind.py`, `scratch/verify_v12_mind_persist.py`, `scratch/verify_v12_agent.py`.

**Phase proof — examples:**
- "My name is ahmet" → even after the session closes and a new process starts: *"Your name is ahmet. Let me look at your profile: you speak Turkish; your interests lean toward..."* (Phase B persistence)
- "Are your answers static or dynamic" → *"each time I compose based on my memory (N turns), my inner observations and M entities of context"* (N/M from real data)
- "investigate example.com" → Agent produces a `whois → dns → tech → cert → metadata → footprint` plan, NET tools ask for approval, observations are collected.

---

### v1.1.0-inference-engine — Bayesian Inference & Hypothesis Reasoning

**Inference Engine (`core/inference/`):**
- **`bayesian.py`** — Real Bayesian sequential belief update engine (`HypothesisBelief`, `BayesianUpdater`), type-informed prior table and Bayes trail.
- **`evidence_weight.py`** — Real evidence weighting model with NATO Admiralty, cross-corroboration multiplier, temporal decay and conflict penalty (`EvidenceWeighter`).
- **`pattern.py`** — OSINT pattern extraction engine (`PatternExtractor`: Ownership, Infrastructure Cluster, Identity Anchor, Temporal Burst, Multi-source).
- **`hypothesis.py`** — Hypothesis data model (`Hypothesis`), hypothesis generator (`HypothesisGenerator`) and state machine (`HypothesisLifecycle`: Generated -> Active -> Confirmed/Refuted/Archived).
- **`dynamic_bridge.py`** — Dynamic bridge engine that discovers hidden links between graph components (`DynamicBridgeEngine`: Shared Infrastructure, Temporal, Type-Based).
- **`uncertainty.py`** — Shannon Entropy uncertainty measurement (`UncertaintyEngine`), critical uncertainty detection and "What Corvus Does Not Know" analysis.
- **`counterfactual.py`** — Counterfactual reasoning engine (`CounterfactualEngine`: "What would be required to prove/refute this?", alternative explanations and suggested discovery actions).
- **`temporal_reasoner.py`** — Temporal inference engine (`TemporalReasoningEngine`: temporal burst detection, timeline overlap, chronological causality chain).
- **`negative_evidence.py`** — Absence and negative evidence inference engine (`NegativeEvidenceEngine`: expected-but-unfound evidence reduces Bayesian belief).
- **`orchestrator.py`** — Central orchestrator that unifies all inference components into a single pipeline (`InferenceOrchestrator`).

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
- **`core/capabilities/search_capability.py`** — Public search-engine OSINT dorking (DuckDuckGo HTML / public probing) for target names, handles, emails, and corporate documents.
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