"""Corvus Agent Layer — Agent (Ana Döngü).

observation -> action -> observation döngüsünün orkestratörü:
  1. Intent + hedef -> Planner -> InvestigationPlan
  2. Her adım: SafetyPolicy.decide() (onay akışı) -> ToolExecutor.run()
  3. Her gözlemden sonra REFLECT: yeni varlık var mı? daha derine inelim mi?
  4. Iteration limiti ile döngüyü sonlandır
  5. Rapor üret (uç kullanıcıya özet + pivot önerileri)
"""

from __future__ import annotations
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
                 learning: bool = True):
        self.modules = module_registry or {}
        self.registry = ToolRegistry(self.modules)
        self.policy = SafetyPolicy(approval_mode=approval_mode, ask_callback=ask_callback)
        self.planner = Planner()
        self.executor = ToolExecutor(config=config, logger=logger, context=context, dry_run=dry_run)
        self.iterations = 0

        # v1.1.2 — Self-Learning (varsayılan AÇIK)
        self.learning = learning and _LEARNING_AVAILABLE
        self.store = None
        self.failure = None
        self.selection = None
        self.audit = None
        if self.learning:
            self.store = ExperienceStore()
            from core.learning.patterns import PatternLearning
            self.failure = FailureLearner(self.store)
            self.selection = ExperienceBasedSelection(self.store)
            self.audit = AuditLog()

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

        for step in plan.steps:
            if self.iterations >= self.policy.MAX_ITERATIONS:
                break

            # --- Güvenlik / onay kararı ---
            decision = self.policy.decide(step.tool, self.registry)

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

            # --- Aksiyon ---
            obs = self.executor.run(step.tool, step.target, self.modules)
            observations.append(obs)
            step.applied = True
            step.observation_ref = obs.summary
            applied_steps.append(step)
            self.iterations += 1

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

            # --- REFLECT: yeni varlık bulundu mu? daha derine? ---
            if obs.new_entities:
                self._reflect(obs)

        report = self._finalize(intent, target, plan, observations, applied_steps)
        return report

    def _reflect(self, obs: Observation) -> None:
        """Gözlemdeki yeni varlıkları yorumlar (iç monolog) — döngünün kalbi."""
        # Bu adım şimdilik only observasyon logu; gelecekte pivot planlama yapar.
        new_types = set()
        for key in obs.new_entities:
            ent_type = key.split(":", 1)[0]
            new_types.add(ent_type)
        self._reflection_notes = getattr(self, "_reflection_notes", [])
        self._reflection_notes.append(
            f"{obs.tool} -> {len(obs.new_entities)} yeni varlık ({', '.join(sorted(new_types))})"
        )

    # ------------------------------------------------------------------
    # Raporlama
    # ------------------------------------------------------------------
    def _finalize(self, intent, target, plan, observations, applied_steps) -> Dict:
        success = [o for o in observations if o.status == "success"]
        denied = [o for o in observations if o.status == "denied"]
        errors = [o for o in observations if o.status == "error"]

        return {
            "intent": intent,
            "target": target,
            "target_type": plan.target_type,
            "plan": [s.tool for s in plan.steps],
            "executed": [s.tool for s in applied_steps],
            "observations": [o.to_dict() for o in observations],
            "summary": {
                "total_steps": len(observations),
                "success": len(success),
                "denied": len(denied),
                "errors": len(errors),
                "iterations": self.iterations,
            },
            "pivot_leads": getattr(self, "_reflection_notes", []),
        }