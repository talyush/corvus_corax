"""Corvus Corax v0.9.1-autonomous — Autonomous Strategy & Investigation Engine.

Düşünen, hipotez kuran, hedefleri ayrıştıran (goal decomposition),
başarısızlıkları yöneten (failure awareness) ve dinamik olarak yön değiştiren (pivoting)
otonom istihbarat beyni.
"""

from datetime import datetime, timezone
from core.capabilities.identity_capability import IdentityCapability
from core.capabilities.search_capability import SearchCapability
from core.capabilities.enrichment_capability import EnrichmentCapability


class Hypothesis:
    """Tekil bir istihbarat hipotezi."""

    def __init__(self, hypothesis_id, statement, rationale, target_type, target_value, confidence=0.5):
        self.id = hypothesis_id
        self.statement = statement
        self.rationale = rationale
        self.target_type = target_type
        self.target_value = target_value
        self.confidence = confidence
        self.status = "UNTESTED"  # UNTESTED, CONFIRMED, REFUTED, EXHAUSTED
        self.actions_taken = []
        self.findings = []

    def to_dict(self):
        return {
            "id": self.id,
            "statement": self.statement,
            "rationale": self.rationale,
            "target_type": self.target_type,
            "target_value": self.target_value,
            "confidence": self.confidence,
            "status": self.status,
            "findings_count": len(self.findings),
        }


class InvestigationGoal:
    """Araştırma hedefi ve ayrıştırılmış alt hedefler."""

    def __init__(self, seed_value, seed_type="person"):
        self.seed_value = seed_value
        self.seed_type = seed_type
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.sub_goals = self._decompose_goals()

    def _decompose_goals(self):
        if self.seed_type in ("person", "unknown"):
            return [
                {"phase": 1, "name": "IDENTITY_PERMUTATION", "desc": "Normalize name, generate handles & candidate emails"},
                {"phase": 2, "name": "PUBLIC_SEARCH_PROBING", "desc": "Perform web dorking & search engine probing"},
                {"phase": 3, "name": "DIGITAL_FOOTPRINT_SWEEP", "desc": "Sweep social platforms, repos, breach databases & academic registries"},
                {"phase": 4, "name": "CORRELATION_&_PIVOTING", "desc": "Correlate discovered entities & pivot to secondary targets"},
            ]
        elif self.seed_type == "domain":
            return [
                {"phase": 1, "name": "DNS_&_INFRASTRUCTURE", "desc": "Resolve A/AAAA, MX, NS, CAA & TLS certificates"},
                {"phase": 2, "name": "METADATA_&_TECH_STACK", "desc": "Harvest robots.txt, sitemaps, favicon hash & tech stack"},
                {"phase": 3, "name": "ORGANIZATION_&_EMAILS", "desc": "Discover personnel, email patterns & breach footprints"},
                {"phase": 4, "name": "CORRELATION_&_PIVOTING", "desc": "Correlate infrastructure & map corporate topology"},
            ]
        else:
            return [
                {"phase": 1, "name": "TARGET_PROBING", "desc": "Gather core intelligence payload for target"},
                {"phase": 2, "name": "RELATIONSHIP_EXPANSION", "desc": "Expand entity graph & perform cross-entity pivots"},
                {"phase": 3, "name": "CORRELATION_&_PIVOTING", "desc": "Synthesize risk ratings & store intelligence in vault"},
            ]


class AutonomousStrategyEngine:
    """Otonom Akıllı Araştırma ve Strateji Motoru."""

    def __init__(self, context_manager, module_registry=None, logger=None):
        self.context = context_manager
        self.modules = module_registry or {}
        self.logger = logger
        self.hypotheses = []
        self.execution_log = []

    def _log(self, msg, level="info"):
        if self.logger:
            getattr(self.logger, level, self.logger.info)(f"[Strategy] {msg}")

    def generate_initial_hypotheses(self, seed_value, seed_type):
        """Seed girdisine dayanarak başlangıç hipotez kümesini oluşturur."""
        self.hypotheses = []

        if seed_type == "person":
            norm_name = IdentityCapability.normalize_text(seed_value)
            handles = IdentityCapability.generate_username_permutations(seed_value)

            h1 = Hypothesis(
                hypothesis_id="HYP-01",
                statement=f"Target '{seed_value}' uses standardized username handles (e.g. {', '.join(handles[:3])})",
                rationale="Individuals consistently reuse a small set of handle permutations across social/digital platforms",
                target_type="person",
                target_value=seed_value,
                confidence=0.7,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-02",
                statement=f"Target '{seed_value}' has public web mentions indexed by search engines",
                rationale="Public search queries reveal secondary identifiers (emails, phone numbers, location, company)",
                target_type="person",
                target_value=norm_name,
                confidence=0.6,
            )
            h3 = Hypothesis(
                hypothesis_id="HYP-03",
                statement=f"Target '{seed_value}' may have candidate emails registered on public services (Gravatar, Breach DBs)",
                rationale="Corporate and personal emails leave metadata traces on public avatar and breach registries",
                target_type="person",
                target_value=seed_value,
                confidence=0.5,
            )
            self.hypotheses.extend([h1, h2, h3])

        elif seed_type == "domain":
            h1 = Hypothesis(
                hypothesis_id="HYP-01",
                statement=f"Domain '{seed_value}' exposes DNS, email security records (SPF/DMARC) & web tech stack",
                rationale="Active corporate domains configure mail servers and web application frameworks",
                target_type="domain",
                target_value=seed_value,
                confidence=0.9,
            )
            h2 = Hypothesis(
                hypothesis_id="HYP-02",
                statement=f"Domain '{seed_value}' exposes administrative metadata & favicon hashes for infrastructure tracking",
                rationale="Robots.txt, sitemaps, and favicon hashes correlate hidden web origins",
                target_type="domain",
                target_value=seed_value,
                confidence=0.8,
            )
            self.hypotheses.extend([h1, h2])

        else:
            h1 = Hypothesis(
                hypothesis_id="HYP-01",
                statement=f"Target '{seed_value}' ({seed_type}) can be attributed to related network/identity entities",
                rationale="Core recon modules provide attribution & geolocation payloads",
                target_type=seed_type,
                target_value=seed_value,
                confidence=0.8,
            )
            self.hypotheses.append(h1)

        return self.hypotheses

    def execute_autonomous_investigation(self, seed_value, seed_type="person", status_callback=None):
        """
        Otonom hipotez sınama, yetenek çalıştırma, başarısızlık yönetimi (failure awareness) ve canlı yön değiştirme (pivoting) döngüsü.
        """
        goal = InvestigationGoal(seed_value, seed_type)
        self.generate_initial_hypotheses(seed_value, seed_type)

        report = {
            "seed": seed_value,
            "seed_type": seed_type,
            "goal": goal,
            "hypotheses": self.hypotheses,
            "discovered_entities": {},
            "strategy_actions": [],
            "pivots": [],
        }

        # -------------------------------------------------------------
        # Phase 1: Identity Permutation & Internal Capability Execution
        # -------------------------------------------------------------
        if status_callback:
            status_callback("Phase 1: Formulating hypotheses & generating identity permutations")

        handles = IdentityCapability.generate_username_permutations(seed_value)
        emails = IdentityCapability.generate_candidate_emails(seed_value)

        # Context'e aday permutasyonları ekle
        for h in handles[:5]:
            self.context.add_entity("social_profile", f"candidate:{h}", provenance={"source": "identity_capability", "status": "candidate"})
        for em in emails[:5]:
            self.context.add_entity("email", em, provenance={"source": "identity_capability", "status": "candidate"})

        report["strategy_actions"].append({
            "phase": 1,
            "action": "identity_permutation",
            "status": "success",
            "output": f"Generated {len(handles)} handle permutations and {len(emails)} candidate emails.",
        })

        # -------------------------------------------------------------
        # Phase 2: Web Search Engine Probing & OSINT Dorking
        # -------------------------------------------------------------
        if status_callback:
            status_callback("Phase 2: Probing public web search indices & OSINT dorks")

        norm_name = IdentityCapability.normalize_text(seed_value)
        dorks = SearchCapability.generate_osint_dorks(norm_name)
        web_results = SearchCapability.search_duckduckgo(dorks[0], max_results=5)

        discovered_from_search = []
        if web_results.get("status") == "success" and (web_results.get("urls") or web_results.get("discovered_emails")):
            for url in web_results.get("urls", []):
                self.context.add_entity("url", url, provenance={"source": "search_capability", "query": dorks[0]})
                discovered_from_search.append(url)
            for em in web_results.get("discovered_emails", []):
                self.context.add_entity("email", em, provenance={"source": "search_capability", "query": dorks[0]})
                discovered_from_search.append(em)

            self.hypotheses[1].status = "CONFIRMED"
            self.hypotheses[1].findings.extend(discovered_from_search)
        else:
            # FAILURE AWARENESS: Arama boş geldiyse pes etme, 2. dork kalıbını ve soyad aramalarını dene!
            self.hypotheses[1].status = "REFUTED"
            if status_callback:
                status_callback("Phase 2 [Failure Fallback]: Primary search query empty — executing 2nd wave dorking")

            fallback_results = SearchCapability.search_duckduckgo(dorks[1], max_results=5)
            if fallback_results.get("status") == "success" and fallback_results.get("urls"):
                for url in fallback_results.get("urls", []):
                    self.context.add_entity("url", url, provenance={"source": "search_capability_fallback"})
                    discovered_from_search.append(url)

        report["strategy_actions"].append({
            "phase": 2,
            "action": "web_search_probing",
            "status": "success" if discovered_from_search else "empty",
            "output": f"Discovered {len(discovered_from_search)} web references/emails via OSINT dorking.",
        })

        # -------------------------------------------------------------
        # Phase 3: Module Pipeline Execution & Avatar Enrichment
        # -------------------------------------------------------------
        if status_callback:
            status_callback("Phase 3: Executing module pipeline & Gravatar avatar hash enrichment")

        # Gravatar Avatar Hash lookup for top candidate emails
        gravatar_hits = []
        for em in emails[:3]:
            grav_res = EnrichmentCapability.check_gravatar_profile(em)
            if grav_res.get("status") == "found":
                gravatar_hits.append(grav_res)
                self.context.add_entity(
                    "person", grav_res.get("display_name") or seed_value,
                    provenance={"source": "enrichment_capability", "gravatar": grav_res.get("profile_url")}
                )

        if gravatar_hits:
            self.hypotheses[2].status = "CONFIRMED"
            self.hypotheses[2].findings.extend([g["profile_url"] for g in gravatar_hits])

        # CLI Modüllerini çalıştır
        modules_to_run = []
        if seed_type in ("person", "unknown"):
            modules_to_run = ["social", "phone", "email", "github", "academic"]
        elif seed_type == "domain":
            modules_to_run = ["dns", "cert", "tech", "metadata", "footprint", "whois", "subdomain"]

        module_results = []
        for mod_name in modules_to_run:
            if mod_name in self.modules:
                try:
                    if status_callback:
                        status_callback(f"Executing module '{mod_name}' for target '{seed_value}'")
                    mod_cls = self.modules[mod_name]
                    mod_inst = mod_cls(target=[seed_value], config={}, logger=self.logger, context=self.context)
                    res = mod_inst.execute()
                    if res and res.get("status") == "success":
                        module_results.append(mod_name)
                except Exception as e:
                    self._log(f"Module {mod_name} execution error: {e}", level="warning")

        # FAILURE AWARENESS & DYNAMIC PIVOTING: Eğer ana modüller sıfır bulgu ürettiyse, permutasyon mahlaslarını sosyal modüle besle!
        if not module_results and handles:
            if status_callback:
                status_callback("Phase 3 [Failure Pivoting]: Direct target search empty — probing top handle permutations on social/github")

            for top_handle in handles[:2]:
                for fallback_mod in ("social", "github"):
                    if fallback_mod in self.modules:
                        try:
                            mod_cls = self.modules[fallback_mod]
                            mod_inst = mod_cls(target=[top_handle], config={}, logger=self.logger, context=self.context)
                            res = mod_inst.execute()
                            if res and res.get("status") == "success":
                                module_results.append(f"{fallback_mod}:{top_handle}")
                                report["pivots"].append(f"Pivoted to handle '{top_handle}' on module {fallback_mod}")
                        except Exception:
                            pass

        report["strategy_actions"].append({
            "phase": 3,
            "action": "module_pipeline_execution",
            "status": "success" if module_results else "fallback_executed",
            "output": f"Executed {len(module_results)} module investigations (gravatar hits: {len(gravatar_hits)}).",
        })

        # -------------------------------------------------------------
        # Phase 4: Correlation, Synthesis & Final Report
        # -------------------------------------------------------------
        if status_callback:
            status_callback("Phase 4: Synthesizing entity relationships & finalizing strategy report")

        entities = self.context.data.get("entities", {})
        report["discovered_entities"] = entities
        report["total_entities"] = len(entities)
        report["total_relations"] = len(self.context.data.get("relations", []))

        return report
