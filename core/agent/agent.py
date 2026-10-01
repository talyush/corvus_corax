"""Corvus Agent Layer â€” Agent (Ä°cra).

v1.4: Agent artÄ±k araÅŸtÄ±rmanÄ±n SAHÄ°BÄ° deÄŸildir â€” InvestigationEngine'in
kararÄ±nÄ± AYNY yÃ¼rÃ¼tme sÃ¶zleÅŸmesiyle uygular:

    Investigation Engine â†’ decision â†’ Agent â†’ SafetyPolicy â†’ ActionGuard
        â†’ Tool â†’ ToolResult â†’ Investigation Engine (state update)

Agent'Ä±n sorumluluklarÄ±:
    - interpret_query      : doÄŸal dil â†’ intent + hedef (salt okuma)
    - execute(step, state) : Engine kararÄ± â†’ SafetyPolicy + ActionGuard â†’
                             ToolExecutor â†’ ToolResult (state'e DOKUNMAZ)
    - investigate()        : geriye uyumlu API â€” InvestigationEngine'i kurup
                             Ã§alÄ±ÅŸtÄ±rÄ±r; rapor, Engine'in state'inden Ã¼retilir.

Loop state'i (queue/seen/budget/reflect/stop) yalnÄ±zca Engine'dedir.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional, Callable

from .tools import ToolRegistry
from .policy import SafetyPolicy, Approval
from .planner import Planner, InvestigationPlan, PlanStep
from .executor import ToolExecutor, ToolResult, Observation

# v1.1.2 â€” Self-Learning entegrasyonu (opsiyonel; yoksa agent eskisi gibi Ã§alÄ±ÅŸÄ±r)
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
    """GÃ¼venli otonom istihbarat ajanÄ± â€” Investigation Engine'in icra kolu."""

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

        # KalÄ±cÄ± depolarÄ±n dizini: varsayÄ±lan vault/ (storage_dir verilirse oraya)
        from core import vault_path
        root_vault = vault_path()
        self.storage_dir = storage_dir or root_vault

        # v1.1.2 â€” Self-Learning (varsayÄ±lan AÃ‡IK; dry_run Ã¶ÄŸrenmeyi ATLAR)
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

        # v1.1.2+ â€” Knowledge baÄŸlantÄ±sÄ± (mimar dersleri -> plan tavsiyeleri)
        try:
            from core.alignment.knowledge import KnowledgeStore
            self.knowledge = KnowledgeStore(path=os.path.join(self.storage_dir, "knowledge.json"))
        except Exception:
            self.knowledge = None

        # v1.4 â€” ActionGuard (capability sÄ±nÄ±rÄ±): SafetyPolicy'den SONRA, Tool'DAN Ã–NCE
        self.guard = None
        try:
            from core.alignment.guard import ActionGuard
            self.guard = ActionGuard(knowledge=self.knowledge,
                                     log_path=os.path.join(self.storage_dir, "guard_log.jsonl"))
        except Exception:
            self.guard = None

        # v1.4 â€” Engine'in salt-okuyacaÄŸÄ± gÃ¶zlem deposu (state DEÄÄ°L; yalnÄ±zca iz)
        self._observations: List[Observation] = []

    # ------------------------------------------------------------------
    # Girdi yorumlama: doÄŸal dil -> intent + hedef
    # ------------------------------------------------------------------
    def interpret_query(self, query: str, nlu=None) -> tuple:
        """'example.com araÅŸtÄ±r' gibi bir isteÄŸi (intent, target) olarak Ã§Ã¶zÃ¼mler."""
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
    # v1.4 — GİRİŞ: Investigation Engine'i kurar ve çalıştırır
    # ------------------------------------------------------------------
    def investigate(self, query: str, nlu=None) -> Dict:
        """Araştırmayı InvestigationEngine üzerinden başlatır.

        v1.4 katmanı: bu metot YALNIZCA engine'i kurar ve raporu döndürür.
        Döngü/state (queue, seen, budget, reflect, stop) engine'dedir.
        """
        from core.investigation.engine import InvestigationEngine
        engine = InvestigationEngine(
            agent=self,
            context=self.executor.context if hasattr(self.executor, "context") else None,
            logger=None,
        )
        return engine.investigate(query, nlu)

    # ------------------------------------------------------------------
    # v1.4 — İCRA SÖZLEŞMESİ (Engine -> Agent -> SafetyPolicy -> Guard -> Tool)
    # ------------------------------------------------------------------
    def execute(self, step: PlanStep, state=None) -> ToolResult:
        """Engine'in kararını uygular; state'e DOKUNMAZ.

        Akış:
          SafetyPolicy.decide  -> eylem izni
          ActionGuard.check    -> capability/scope sınırı (mevcut ise)
          ToolExecutor.execute -> ToolResult (canonical)

        Her çağrıda gerçekleşen aksiyon gözlemini `self._observations` (iz deposu)
        içine bırakır — bu salt okunurdur (state DEĞİL; rapor Engine tarafından
        okunur).
        """
        decision = self.policy.decide(step.tool, self.registry)
        if decision.scope.value == "denied":
            return self._tool_result_with_obs(
                step, ToolResult(ok=False, tool=step.tool, data={},
                                 error=f"Kısıtlı araç ({decision.reason})"),
                status="denied")

        if decision.requires_approval and not decision.approved:
            return self._tool_result_with_obs(
                step, ToolResult(ok=False, tool=step.tool, data={},
                                 error="Onay verilmedi"),
                status="denied")

        # v1.4 — ActionGuard (capability sınırı): SafetyPolicy sonrası, Tool öncesi
        if self.guard is not None:
            try:
                verdict = self.guard.check(step.target)
                if not getattr(verdict, "allowed", True):
                    return self._tool_result_with_obs(
                        step, ToolResult(ok=False, tool=step.tool, data={},
                                         error="capability_restricted"),
                        status="denied")
            except Exception:
                pass  # guard hatası yutulur — eylemi engellemez (geriye uyum)

        tool_result = self.executor.execute(step.tool, step.target, self.modules)
        return self._tool_result_with_obs(step, tool_result, status=tool_result.observation.status)

    def _tool_result_with_obs(self, step: PlanStep, tool_result: ToolResult,
                              status: Optional[str] = None) -> ToolResult:
        """ToolResult'ı iz deposuna gözlem olarak yazar (state DEĞİL; salt iz)."""
        obs = tool_result.observation
        if obs is None:
            obs = Observation(
                tool=step.tool, target=step.target,
                status=status or ("success" if tool_result.ok else "error"),
                summary=tool_result.error or "sonuç yok")
        self._observations.append(obs)
        if tool_result.observation is None:
            tool_result.observation = obs
            tool_result.observation_ref = obs.obs_id
        return tool_result
        return "investigate", target
