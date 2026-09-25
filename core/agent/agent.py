"""Corvus Agent Layer — Agent (Ana Döngü).

observation -> action -> observation döngüsünün orkestratörü:
  1. Intent + hedef -> Planner -> InvestigationPlan
  2. Her adım: SafetyPolicy.decide() (onay akışı) -> ToolExecutor.run()
  3. Her gözlemden sonra REFLECT: yeni varlık var mı? daha derine inelim mi?
  4. Iteration limiti ile döngüyü sonlandır
  5. Rapor üret (uç kullanıcıya özet + pivot önerileri)
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional, Callable

from .tools import ToolRegistry
from .policy import SafetyPolicy, Approval
from .planner import Planner, InvestigationPlan, PlanStep
from .executor import ToolExecutor, Observation

# v1.1.2 — Self-Learning entegrasyonu (opsiyonel; yoksa agent eskisi gibi çalışır)
try:
    from core.learning.experience import ExperienceStore
    from core.learning.calibration import CalibrationEngine
    from core.learning.selection import ExperienceBasedSelection
    from core.learning.self_learn import FailureLearner
    from core.learning.audit import AuditLog

    _LEARNING_AVAILABLE = True
except Exception:
    _LEARNING_AVAILABLE = False


class Agent:
    """Güvenli otonom istihbarat ajanı."""

    def __init__(self, module_registry: Optional[Dict] = None,
                 config: Optional[Dict] = None, logger=None, context=None,
                 approval_mode: Approval = Approval.ASK,
                 ask_callback: Optional[Callable[[str], bool]] = None,
                 dry_run: bool = False,
                 learning: bool = True,
                 storage_dir: Optional[str] = None):
        self.modules = module_registry or {}
        self.registry = ToolRegistry(self.modules)
        self.policy = SafetyPolicy(approval_mode=approval_mode, ask_callback=ask_callback)
        self.planner = Planner()
        self.executor = ToolExecutor(config=config, logger=logger, context=context, dry_run=dry_run)
        self.iterations = 0

        # Kalıcı depoların dizini: varsayılan vault/ (storage_dir verilirse oraya)
        from core import vault_path
        root_vault = vault_path()
        self.storage_dir = storage_dir or root_vault

        # v1.1.2 — Self-Learning (varsayılan AÇIK; dry_run öğrenmeyi ATLAR)
        self.learning = learning and _LEARNING_AVAILABLE and not dry_run
        self.store = None
        self.failure = None
        self.selection = None
        self.audit = None
        self.knowledge = None
        if self.learning:
            self.store = ExperienceStore(path=os.path.join(self.storage_dir, "experience.json"))
            from core.learning.patterns import PatternLearning
            self.failure = FailureLearner(self.store)
            self.selection = ExperienceBasedSelection(self.store)
            self.audit = AuditLog(path=os.path.join(self.storage_dir, "audit.jsonl"))

        # v1.1.2+ — Knowledge bağlantısı (mimar dersleri -> plan tavsiyeleri)
        try:
            from core.alignment.knowledge import KnowledgeStore
            self.knowledge = KnowledgeStore(path=os.path.join(self.storage_dir, "knowledge.json"))
        except Exception:
            self.knowledge = None

        # v1.3.5 — Autonomy: gözlemden doğan pivot adımlarının izi (rapor "pivot_path")
        self._pivot_path: List[Dict] = []
        self._reflection_notes: List[str] = []

    # ------------------------------------------------------------------
    # Girdi yorumlama: doğal dil -> intent + hedef
    # ------------------------------------------------------------------
    def interpret_query(self, query: str, nlu=None) -> tuple:
        """'example.com araştır' gibi bir isteği (intent, target) olarak çözümler."""
        if nlu is not None:
            parsed = nlu.parse(query)
            target = parsed.entities[0] if parsed.entities else query.strip()
            intent = "investigate" if parsed.register == "investigate" else "explore"
            return intent, target
        # fallback: regex-ilkel
        import re
        ip_re = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        dom_re = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")
        m = ip_re.search(query) or dom_re.search(query)
        target = m.group(0) if m else query.strip()
        return "investigate", target

    # ------------------------------------------------------------------
    # Ana döngü
    # ------------------------------------------------------------------
    def investigate(self, query: str, nlu=None) -> Dict:
        """observation -> action -> observation döngüsü."""
        intent, target = self.interpret_query(query, nlu)
        plan = self.planner.plan(intent, target, self.registry)

        # v1.1.2+ — MİMAR DERSLERİNDEN GELEN ARAÇ ÖNERİLERİNİ UYGULA
        # (knowledge.agent_hints: "domain hedefinde cert kullan" gibi derler)
        if self.knowledge is not None:
            hint_tools = self.knowledge.hints_for(plan.target_type)
            if hint_tools:
                by_tool = {s.tool: s for s in plan.steps}
                hinted = [by_tool[t] for t in hint_tools if t in by_tool]
                rest = [s for s in plan.steps if s.tool not in hint_tools]
                plan.steps = hinted + rest

        # v1.1.2 — Deneyim tabanlı araç seçimi (otonom)
        if self.selection is not None:
            original_order = [s.tool for s in plan.steps]
            reordered_tools = self.selection.reorder(original_order, plan.target_type)
            # PlanStep sırasını yeni düzene göre yeniden kur
            by_tool = {s.tool: s for s in plan.steps}
            plan.steps = [by_tool[t] for t in reordered_tools if t in by_tool]
            if self.audit is not None:
                self.audit.log_selection(plan.target_type, original_order, [s.tool for s in plan.steps])

        observations: List[Observation] = []
        applied_steps: List[PlanStep] = []

        # v1.3.5 — Autonomy: statik plan yerine DİNAMİK KUYRUK.
        # Plan adımları + gözlemden doğan PİVOT adımları aynı kuyruktan koşar.
        #   - seen: (tool, target) tekrar koruması (döngü/pivot şişmesi engeli)
        #   - net_used / local_used: kaynak bütçesi (politika limitleri)
        #   - pivots_used: otonom pivot sayısı (sonsuz derinleşme koruması)
        queue: List[PlanStep] = list(plan.steps)
        seen: set = set()
        net_used = 0
        local_used = 0
        pivots_used = 0

        while queue:
            if self.iterations >= self.policy.MAX_ITERATIONS:
                break
            step = queue.pop(0)
            key = (step.tool, step.target.strip().lower())
            if key in seen:
                continue
            seen.add(key)

            # --- Güvenlik / onay kararı ---
            decision = self.policy.decide(step.tool, self.registry)
            is_net = self.registry.is_network(step.tool)

            # v1.3.5 — kaynak bütçesi: ağ/yerel çağrı limiti aşılırsa adım atlanır
            if decision.scope.value == "denied":
                obs = Observation(tool=step.tool, target=step.target, status="denied",
                                  summary=f"Kısıtlı araç ({decision.reason}) — çalıştırılmadı")
                observations.append(obs)
                # v1.1.2 — deneyime kaydet (denied)
                if self.store is not None:
                    self.store.record(step.tool, plan.target_type, step.target, status="denied",
                                      error_type="policy_denied")
                continue

            if decision.requires_approval and not decision.approved:
                obs = Observation(tool=step.tool, target=step.target, status="denied",
                                  summary=f"Onay verilmedi — {step.tool} atlandı")
                observations.append(obs)
                continue

            if is_net and net_used >= self.policy.MAX_NETWORK_TOOLS_PER_TASK:
                obs = Observation(tool=step.tool, target=step.target, status="skipped",
                                  summary=f"Ağ bütçesi doldu (max {self.policy.MAX_NETWORK_TOOLS_PER_TASK}) — {step.tool} atlandı")
                observations.append(obs)
                continue
            if not is_net and local_used >= self.policy.MAX_LOCAL_TOOLS_PER_TASK:
                obs = Observation(tool=step.tool, target=step.target, status="skipped",
                                  summary=f"Yerel bütçe doldu (max {self.policy.MAX_LOCAL_TOOLS_PER_TASK}) — {step.tool} atlandı")
                observations.append(obs)
                continue

            # --- Aksiyon ---
            obs = self.executor.run(step.tool, step.target, self.modules)
            observations.append(obs)
            step.applied = True
            step.observation_ref = obs.summary
            applied_steps.append(step)
            self.iterations += 1

            # v1.3.5 — gerçek kaynak tüketen aksiyonlar bütçeden düşülür
            if obs.status in ("success", "error"):
                if is_net:
                    net_used += 1
                else:
                    local_used += 1

            # --- v1.1.2: deneyimden öğren (başarı + hata) ---
            if self.store is not None and not getattr(self.executor, "dry_run", False):
                if obs.status == "success":
                    self.failure.learn_from_success(
                        step.tool, plan.target_type,
                        new_entities=len(obs.new_entities), summary=obs.summary,
                    )
                    if self.audit is not None:
                        self.audit.log_experience(step.tool, "success", plan.target_type)
                elif obs.status == "error":
                    self.failure.learn_from_failure(
                        step.tool, plan.target_type,
                        error_type="runtime_error", summary=obs.summary,
                    )
                    if self.audit is not None:
                        self.audit.log_experience(step.tool, "error", plan.target_type,
                                                  error_type="runtime_error")

            # --- v1.3.5 REFLECT: yeni varlık -> PİVOT adımı (otonom derinleşme) ---
            if obs.status == "success" and obs.new_entities \
                    and pivots_used < self.policy.MAX_PIVOTS_PER_TASK:
                # Yalnızca henüz koşmamış (tool,target) çiftlerini pivot kabul et —
                # kendi hedefini tekrar arayan araçlar (person:hedef -> social) elenir.
                followups = [
                    f for f in self._reflect(obs, plan)
                    if (f.tool, f.target.strip().lower()) not in seen
                ]
                for f in followups:
                    if pivots_used >= self.policy.MAX_PIVOTS_PER_TASK:
                        break
                    fkey = (f.tool, f.target.strip().lower())
                    seen.add(fkey)
                    queue.append(f)
                    pivots_used += 1
                if followups:
                    self._pivot_path.append({
                        "from": obs.tool,
                        "target": obs.target,
                        "steps": [{
                            "tool": f.tool,
                            "target": f.target,
                            "target_type": f.target_type,
                            "rationale": f.rationale,
                        } for f in followups],
                    })

        report = self._finalize(intent, target, plan, observations, applied_steps)
        return report

    # v1.3.5 — Autonomy: gözlemden doğan yeni varlık tipi -> en uygun pivot aracı.
    # Kaynak kısıtlılığı bilinci: her tür için TEK derinleştirme aracı seçilir;
    # registry'de yoksa sessizce atlanır (araç "çoğaltma" değil, "derinleştirme").
    PIVOT_MAP: Dict[str, List[str]] = {
        "email": ["breach"],
        "domain": ["whois", "dns", "cert"],
        "ip": ["geoip", "asn"],
        "person": ["social"],
        "username": ["github"],
        "phone": ["phone"],
        "wallet": ["wallet"],
        "organization": ["org"],
    }

    def _reflect(self, obs: Observation, plan: InvestigationPlan) -> List[PlanStep]:
        """Gözlemdeki yeni varlıkları PİVOT adımlarına çevirir.

        v1.3.5 — Autonomy: 'observation -> REFLECT -> yeni PlanStep' halkası artık
        gerçek: modül yeni bir email/domain/ip/person bulduğunda, o varlığı
        derinleştiren bir pivot adımı üretilir ve ana kuyruğa eklenir. Aynı
        varlık türü başına tek pivot üretilir (şişme kontrolü); aracı kullanılamazsa
        sessizce atlanır. Böylece gözlem AKTİF aksiyona dönüşür — insanın her
        adımı tekrar komut etmesi gerekmez.
        """
        steps: List[PlanStep] = []
        seen_types: set = set()
        for key in obs.new_entities:
            ent_type, sep, value = key.partition(":")
            if not sep or not value or ent_type in seen_types:
                continue
            seen_types.add(ent_type)
            for tool in self.PIVOT_MAP.get(ent_type, []):
                if not self.registry.is_available(tool):
                    continue
                scope = "NET" if self.registry.is_network(tool) else "LOCAL"
                steps.append(PlanStep(
                    tool=tool,
                    target=value,
                    target_type=ent_type,
                    rationale=f"PİVOT ({scope}): {obs.tool}'un bulduğu {ent_type}:{value} hedefini derinleştir",
                ))
                break  # her tür için tek pivot aracı yeter

        if steps:
            new_types = sorted(seen_types)
            self._reflection_notes.append(
                f"{obs.tool} -> {len(obs.new_entities)} yeni varlık ({', '.join(new_types)})"
                f" + {len(steps)} pivot adımı"
            )
        return steps

    # ------------------------------------------------------------------
    # Raporlama
    # ------------------------------------------------------------------
    def _finalize(self, intent, target, plan, observations, applied_steps) -> Dict:
        success = [o for o in observations if o.status == "success"]
        denied = [o for o in observations if o.status == "denied"]
        errors = [o for o in observations if o.status == "error"]

        # v1.3.5 — evidence özeti: 2+ farklı araç aynı varlığı bulduysa
        # "corroborated" (çapraz doğrulama) sayılır — v1.5 Evidence temasının temeli.
        entity_tools: Dict[str, set] = {}
        for o in observations:
            if o.status != "success":
                continue
            for key in o.new_entities:
                entity_tools.setdefault(key, set()).add(o.tool)
        corroborated = {k: sorted(v) for k, v in entity_tools.items() if len(v) >= 2}

        return {
            "intent": intent,
            "target": target,
            "target_type": plan.target_type,
            "plan": [s.tool for s in plan.steps],
            "executed": [s.tool for s in applied_steps],
            "observations": [o.to_dict() for o in observations],
            "pivot_path": list(getattr(self, "_pivot_path", [])),
            "evidence": {
                "entities_found": sorted(entity_tools.keys()),
                "corroborated": corroborated,
                "corroboration_count": len(corroborated),
            },
            "summary": {
                "total_steps": len(observations),
                "success": len(success),
                "denied": len(denied),
                "errors": len(errors),
                "iterations": self.iterations,
                "pivots": len(getattr(self, "_pivot_path", [])),
            },
            "pivot_leads": getattr(self, "_reflection_notes", []),
        }