"""Corvus Corax v1.4 — Investigation Engine.

Araştırmanın SAHİBİ ve state'in TEK yazarı. Agent'tan ayrıştırılmıştır:

    Investigation Engine  (devlet, hedef çözümleme, hipotez, next-step, stop, rapor)
        -> karar           Agent'e iletilir
        -> Agent          SafetyPolicy -> Tool -> ToolResult döndürür
        -> Engine         ToolResult'ı state'e işler (record_tool_result)

Bu sınıf MODÜL ÇALIŞTIRMAZ; yalnızca karar üretir ve sonuçları işler.
Araç eklemek (execute) Agent'ın işidir (v1.4 kontrat 6.2).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from core.investigation.state import (
    InvestigationState,
    TargetResolution,
    TargetCandidate,
    StopConditions,
)
from core.agent.executor import ToolResult


class InvestigationEngine:
    """Kalıcı araştırma motoru — yeni bir investigation için yeni state kurar.

    agent: AgentExecutor arayüzü (execute + policy/safety sağlar).
    """

    # v1.3.5'ten taşınan pivot hedef haritası
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

    def __init__(self, agent=None, context=None, logger=None):
        self.agent = agent                # AgentExecutor arayüzü (mutabilis yok — yalnızca icra)
        self.context = context
        self.logger = logger

    # ------------------------------------------------------------------
    # ANA GİRİŞ — yeni araştırma başlatır
    # ------------------------------------------------------------------
    def investigate(self, query: str, nlu=None, intent: Optional[str] = None,
                    referent: Optional[str] = None) -> Dict:
        """Kullanıcı isteğini bir araştırmaya çevirir; tam rapor döndürür.

        Akış:
            request -> resolve_target (rule-based) -> plan_actions
            -> (next-step seçimi DÖNGÜSÜ) -> agent.execute -> record_tool_result
            -> check_stop -> finalize
        """
        # 1. Kullanıcı emri -> request
        if intent is None and referent is None and self.agent is not None:
            intent, referent = self.agent.interpret_query(query, nlu)
        intent = intent or "investigate"
        referent = referent or (query or "").strip()

        state = self._create_state(intent, referent)
        self.state = state

        # 2. Hedef çözümleme (rule-based) — v1.4
        self.resolve_target(referent, state)

        # 3. Plan oluştur (Planner + registry)
        plan = self._plan_actions(intent, referent, state)
        self.plan = plan

        # 4. Hipotezleri başlat
        state.hypotheses = self._init_hypotheses(referent, state)

        # 5. DÖNGÜ — next-step seçimi ve icra
        state.status = "IN_PROGRESS"
        self._run_loop(plan, state)

        # 6. Finalize -> rapor
        state.status = "FINALIZED"
        report = self._finalize(plan, state)
        state.finalized_report = report
        return report

    # ------------------------------------------------------------------
    # State yaşam döngüsü yardımcıları
    # ------------------------------------------------------------------
    def _create_state(self, intent: str, referent: str) -> InvestigationState:
        """InvestigationState kurar; constraints -> stop_conditions."""
        policy = self.agent.policy if self.agent is not None else None
        max_iter = getattr(policy, "MAX_ITERATIONS", 8) if policy else 8
        max_net = getattr(policy, "MAX_NETWORK_TOOLS_PER_TASK", 6) if policy else 6
        max_local = getattr(policy, "MAX_LOCAL_TOOLS_PER_TASK", 4) if policy else 4
        max_piv = getattr(policy, "MAX_PIVOTS_PER_TASK", 4) if policy else 4

        stop = StopConditions(
            max_steps=max_iter,
            max_network_calls=max_net,
            max_local_calls=max_local,
            max_pivots=max_piv,
        )
        return InvestigationState(
            request={"intent": intent, "referent": referent},
            status="PLANNING",
            stop_conditions=stop,
        )

    # ------------------------------------------------------------------
    # TARGET RESOLUTION — v1.4 (rule-based)
    # ------------------------------------------------------------------
    def resolve_target(self, referent: str, state: InvestigationState) -> TargetResolution:
        """Belirsiz referansı aday kümesi olarak modelle.

        v1.4 kuralı: tek aday doğrudan 'doğru kişi' olarak kabul edilmez;
        adaylar support_score + ambiguity ile taşınır. Rule-based başlangıç.
        """
        resolution = TargetResolution()
        target_type = self._classify(referent)

        # Rule-based: ilk aday, referansın normalize edilmiş hâli
        cand = TargetCandidate(
            entity=f"{target_type}:{referent.strip()}",
            support_score=1.0,
            ambiguity="low",
        )
        resolution.candidates.append(cand)
        resolution.primary = cand.entity if len(referent.strip()) > 0 else None
        resolution.status = "RESOLVED"
        state.resolution = resolution
        return resolution

    def _classify(self, referent: str) -> str:
        """Planner.classify mantığını kullanır (Agent'tan izole)."""
        if self.agent is not None and hasattr(self.agent, "planner"):
            try:
                return self.agent.planner.classify(referent)
            except Exception:
                pass
# ------------------------------------------------------------------
    # PLAN — aksiyon adımlarını üretir
    # ------------------------------------------------------------------
    def _plan_actions(self, intent: str, referent: str, state: InvestigationState):
        """Planner + Knowledge hints + Experience selection ile adımları kurar.

        (Mevcut Agent::investigate akışından taşınmıştır — davranış korunur.)
        """
        planner = self.agent.planner if self.agent is not None else None
        registry = self.agent.registry if self.agent is not None else None
        if planner is None or registry is None:
            return None

        plan = planner.plan(intent, referent, registry)

        # Mimar dersleri -> araç önerileri
        knowledge = getattr(self.agent, "knowledge", None)
        if knowledge is not None:
            hint_tools = knowledge.hints_for(plan.target_type)
            if hint_tools:
                by_tool = {s.tool: s for s in plan.steps}
                hinted = [by_tool[t] for t in hint_tools if t in by_tool]
                rest = [s for s in plan.steps if s.tool not in hint_tools]
                plan.steps = hinted + rest

        # Deneyim tabanlı araç sıralaması
        selection = getattr(self.agent, "selection", None)
        audit = getattr(self.agent, "audit", None)
        if selection is not None:
            original_order = [s.tool for s in plan.steps]
            reordered = selection.reorder(original_order, plan.target_type)
            by_tool = {s.tool: s for s in plan.steps}
            plan.steps = [by_tool[t] for t in reordered if t in by_tool]
            if audit is not None:
                audit.log_selection(plan.target_type, original_order, [s.tool for s in plan.steps])

        return plan

    # ------------------------------------------------------------------
    # HİPOTEZLER — sınanabilecek varsayım kümesi
    # ------------------------------------------------------------------
    def _init_hypotheses(self, referent: str, state: InvestigationState) -> List[Dict]:
        """Hedef için başlangıç hipotezleri (rule-based; tahmin değil, sınama)."""
        t = state.resolution.candidates[0].entity if state.resolution.candidates else referent
        return [
            {"id": "HYP-01",
             "statement": f"{t} hedefi doğrulanabilir dijital izler taşıyor",
             "status": "UNTESTED", "confidence": 0.5},
            {"id": "HYP-02",
             "statement": f"{t} birden fazla bağımsız kaynaktan teyit edilebilir",
             "status": "UNTESTED", "confidence": 0.5},
        ]
# ------------------------------------------------------------------
    # DÖNGÜ — next-step üretir, Agent'tan icra ister, sonucu state'e işler
    # ------------------------------------------------------------------
    def _run_loop(self, plan, state: InvestigationState) -> None:
        from core.agent.executor import Observation
        queue = list(plan.steps) if plan else []
        seen = state.seen
        pivots_used = 0

        while queue:
            if state.iterations >= state.stop_conditions.max_steps:
                break
            step = queue.pop(0)
            key = (step.tool, step.target.strip().lower())
            if key in seen:
                continue
            seen.add(key)

            # Karar gerekçesi — decisions zinciri (state üzerinden engine yazar)
            state.add_decision(
                next_step=f"{step.tool}({step.target})",
                why=self._decision_reason(step),
            )
            if self.agent is None:
                break

            # v1.3.5 Budget — kaynak kısıtı: ağ/yerel limit aşılırsa adım atlanır
            is_net = self._is_network(step.tool)
            if is_net and state.net_used >= state.stop_conditions.max_network_calls:
                self._skip_observation(step, f"Ağ bütçesi doldu (max {state.stop_conditions.max_network_calls}) — {step.tool} atlandı")
                continue
            if not is_net and state.local_used >= state.stop_conditions.max_local_calls:
                self._skip_observation(step, f"Yerel bütçe doldu (max {state.stop_conditions.max_local_calls}) — {step.tool} atlandı")
                continue

            # ICRA — Agent (SafetyPolicy -> ActionGuard -> Tool -> ToolResult)
            tool_result = self.agent.execute(step, state)
            obs = tool_result.observation if tool_result.observation else Observation(
                tool=step.tool, target=step.target, status="skipped",
                summary=tool_result.error or "sonuç yok")

            # STATE GÜNCELLEMESİ — yalnızca Engine
            state.iterations += 1
            state.steps.append(step)
            step.applied = True
            step.observation_ref = tool_result.observation_ref or obs.summary

            if obs.status in ("success", "error"):
                if is_net:
                    state.net_used += 1
                else:
                    state.local_used += 1

            # Deneyimden öğren (yalnızca gerçek aksiyonda)
            self._learn(step, plan, obs)

            # REFLECT: yeni varlık -> PİVOT adımı (otonom derinleşme)
            if obs.status == "success" and obs.new_entities \
                    and state.pivots_used < state.stop_conditions.max_pivots:
                followups = [
                    f for f in self._reflect(obs, plan)
                    if (f.tool, f.target.strip().lower()) not in seen
                ]
                for f in followups:
                    if state.pivots_used >= state.stop_conditions.max_pivots:
                        break
                    fkey = (f.tool, f.target.strip().lower())
                    seen.add(fkey)
                    queue.append(f)
                    state.pivots_used += 1
                    pivots_used += 1
                if followups:
                    state.pivot_path.append({
                        "from": obs.tool,
                        "target": obs.target,
                        "steps": [{
                            "tool": f.tool, "target": f.target,
                            "target_type": f.target_type, "rationale": f.rationale,
                        } for f in followups],
                    })
                    state.reflection_notes.append(
                        f"{obs.tool} -> {len(obs.new_entities)} yeni varlık → {len(followups)} pivot")

            # STOP kontrolü
            if self._check_stop(state, obs):
                break

    def _decision_reason(self, step) -> str:
        try:
            if self.agent is None:
                return ""
            spec = self.agent.registry.get(step.tool)
            return f"Planner: {step.target_type}->{step.tool} ({spec.description if spec else ''})"
        except Exception:
            return ""

    def _is_network(self, tool: str) -> bool:
        try:
            if self.agent is None:
                return False
            return self.agent.registry.is_network(tool)
        except Exception:
            return False
# ------------------------------------------------------------------
    # DENEYİM / ÖĞRENME (mevcut learning entegrasyonu — taşınmış hâli)
    # ------------------------------------------------------------------
    def _learn(self, step, plan, obs) -> None:
        if self.agent is None:
            return
        store = getattr(self.agent, "store", None)
        failure = getattr(self.agent, "failure", None)
        audit = getattr(self.agent, "audit", None)
        dry_run = getattr(getattr(self.agent, "executor", None), "dry_run", True)
        target_type = getattr(plan, "target_type", "unknown")

        if store is None or dry_run:
            return
        if obs.status == "success":
            if failure is not None:
                failure.learn_from_success(
                    step.tool, target_type,
                    new_entities=len(obs.new_entities), summary=obs.summary)
            if audit is not None:
                audit.log_experience(step.tool, "success", target_type)
        elif obs.status == "error":
            if failure is not None:
                failure.learn_from_failure(
                    step.tool, target_type,
                    error_type="runtime_error", summary=obs.summary)
            if audit is not None:
                audit.log_experience(step.tool, "error", target_type,
                                     error_type="runtime_error")

    # ------------------------------------------------------------------
    # REFLECT — gözlemden PİVOT adımları üretir (v1.3.5'ten taşınmış)
    # ------------------------------------------------------------------
    def _reflect(self, obs, plan) -> list:
        from core.agent.planner import PlanStep
        registry = self.agent.registry if self.agent is not None else None
        if registry is None:
            return []

        steps = []
        seen_types = set()
        for key in obs.new_entities:
            ent_type, sep, value = key.partition(":")
            if not sep or not value or ent_type in seen_types:
                continue
            seen_types.add(ent_type)
            for tool in self.PIVOT_MAP.get(ent_type, []):
                if not registry.is_available(tool):
                    continue
                scope = "NET" if registry.is_network(tool) else "LOCAL"
                steps.append(PlanStep(
                    tool=tool,
                    target=value,
                    target_type=ent_type,
                    rationale=f"PİVOT ({scope}): {obs.tool}'un bulduğu {ent_type}:{value} hedefini derinleştir",
                ))
                break  # her tür için tek pivot aracı yeter
        return steps

    # ------------------------------------------------------------------
    # STOP koşulu
    # ------------------------------------------------------------------
    def _check_stop(self, state: InvestigationState, obs) -> bool:
        if state.iterations >= state.stop_conditions.max_steps:
            return True
        if state.stop_conditions.coverage_required:
            success_count = sum(1 for s in state.steps
                                if getattr(s, "applied", False) and s.observation_ref)
            if success_count >= len(state.stop_conditions.coverage_required):
                return True
        return False
# ------------------------------------------------------------------
    # RAPOR — state'i uç kullanıcı raporuna dönüştürür
    # ------------------------------------------------------------------
    def _finalize(self, plan, state: InvestigationState) -> Dict:
        observations = self._collect_observations(state)

        entity_tools: Dict[str, set] = {}
        for o in observations:
            if o.get("status") != "success":
                continue
            for key in o.get("new_entities", []):
                entity_tools.setdefault(key, set()).add(o.get("tool", ""))
        corroborated = {k: sorted(v) for k, v in entity_tools.items() if len(v) >= 2}

        return {
            "intent": state.request.get("intent"),
            "target": state.request.get("referent"),
            "target_type": plan.target_type if plan else "unknown",
            "plan": [s.tool for s in plan.steps] if plan else [],
            "executed": [s.tool for s in state.steps if getattr(s, "applied", False)],
            "observations": observations,
            "pivot_path": list(state.pivot_path),
            "evidence": {
                "entities_found": sorted(entity_tools.keys()),
                "corroborated": corroborated,
                "corroboration_count": len(corroborated),
            },
            "summary": {
                "total_steps": len(observations),
                "success": len([o for o in observations if o.get("status") == "success"]),
                "denied": len([o for o in observations if o.get("status") == "denied"]),
                "errors": len([o for o in observations if o.get("status") == "error"]),
                "iterations": state.iterations,
                "pivots": len(state.pivot_path),
            },
            "pivot_leads": list(state.reflection_notes),
            "resolution": state.resolution.to_dict(),
            "hypotheses": state.hypotheses,
            "gaps": list(state.gaps),
        }

    def _collect_observations(self, state: InvestigationState) -> List[Dict]:
        """Kullanıcı raporu için observations listesi.

        Agent, execute() sırasında gerçek Observation'ları 'agent._observations'
        içinde biriktirir; engine, raporlama sırasında bunları okur (state'e
        değil — yalnızca salt okuma).
        """
        if self.agent is not None:
            obs_list = getattr(self.agent, "_observations", None)
            if obs_list:
                return [o.to_dict() for o in obs_list]
        return []
# ------------------------------------------------------------------
    # SKIP yardımcısı — budget/limit atlanan adımları state + iz deposuna işler
    # ------------------------------------------------------------------
    def _skip_observation(self, step, message: str) -> None:
        from core.agent.executor import Observation
        obs = Observation(
            tool=step.tool, target=step.target, status="skipped",
            summary=message)
        obs.notes.append(message)
        # state.steps'e skip kaydı (only engine writes); applied DEĞİL
        step.applied = False
        step.observation_ref = obs.obs_id
        if step not in self.state.steps:
            self.state.steps.append(step)
        # salt iz deposu (rapor için)
        if self.agent is not None:
            self.agent._observations.append(obs)
        return "person"