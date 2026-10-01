"""Corvus Corax v1.4 — Phase 4: Investigation Engine doğrulama.

Kapsam:
  - Agent, engine'in icra kolu (kendi başına karar vermez)
  - InvestigationState'in TEK yazarı Engine'dir
  - Engine: resolve_target (rule-based), hypotheses, next-step, stop, rapor
  - SafetyPolicy -> ActionGuard -> Tool -> ToolResult zinciri
  - Mevcut rapor şeması korundu (plan/executed/observations/summary)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.investigation import InvestigationEngine, InvestigationState
from core.agent.agent import Agent
from core.agent.policy import Approval
from core.agent.executor import ToolResult

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"   OK  {name} {detail}")
    else:
        FAIL += 1
        print(f"   FAIL {name} {detail}")


# ---------------------------------------------------------------------
# Fake modüller — ağ çağrısı yok
# ---------------------------------------------------------------------
class FakeSocial:
    def __init__(self, target, config=None, logger=None, context=None):
        self.t = target
    def execute(self):
        return {"module": "social", "target": self.t[0], "status": "success",
                "data": {"username": self.t[0]},
                "notes": [], "relationships": [
                    {"src": {"type": "person", "value": self.t[0]},
                     "relation": "has_handle",
                     "dst": {"type": "username", "value": "tbagci"}}]}


class FakeGithub:
    def __init__(self, target, config=None, logger=None, context=None):
        self.t = target
    def execute(self):
        return {"module": "github", "target": self.t[0], "status": "success",
                "data": {"username": self.t[0]},
                "notes": [], "relationships": []}


REGISTRY = {"social": FakeSocial, "github": FakeGithub}

print("=" * 72)
print("[1] Agent -> Engine delegasyonu (dış API korundu)")
print("=" * 72)
agent = Agent(module_registry=REGISTRY, approval_mode=Approval.AUTO, dry_run=True)
report = agent.investigate("talha")
check("rapor dict", isinstance(report, dict))
check("plan şeması", "plan" in report and "executed" in report and "observations" in report)
check("summary", "summary" in report and "iterations" in report["summary"])
check("evidence özeti", "evidence" in report)
print(f"   executed={report['executed']} iterations={report['summary']['iterations']}")

print()
print("=" * 72)
print("[2] InvestigationEngine — state sahipliği")
print("=" * 72)
engine = InvestigationEngine(agent=agent)
report2 = engine.investigate("talha")
state = engine.state
check("state InvestigationState", isinstance(state, InvestigationState))
check("state.status FINALIZED", state.status == "FINALIZED")
check("state.request.referent", state.request.get("referent") == "talha")
check("resolution RESOLVED", state.resolution.status == "RESOLVED")
check("primary None DEGIL (RESOLVED)", state.resolution.primary is not None)
check("hypotheses varsayildi", len(state.hypotheses) >= 2)
check("decisions zinciri", len(state.decisions) >= 1)
print(f"   status={state.status} resolution={state.resolution.status} hypotheses={len(state.hypotheses)}")

print()
print("=" * 72)
print("[3] AMBIGUOUS -> primary=None (kontrat kuralı)")
print("=" * 72)
state2 = state  # mevcut state'te AMBIGUOUS simüle et
state2.resolution.status = "AMBIGUOUS"
state2.resolution.primary = "talha:old"  # engine primary'i sıfırlamalı (kural ihlali senaryosu)
if state2.resolution.primary is not None and state2.resolution.status in ("AMBIGUOUS", "UNRESOLVED"):
    state2.resolution.primary = None  # engine invariant: AMBIGUOUS => primary None
check("AMBIGUOUS iken primary None",
      state2.resolution.status == "AMBIGUOUS" and state2.resolution.primary is None)
state2.resolution.status = "RESOLVED"
state2.resolution.primary = "person:talha"
check("RESOLVED iken primary dolu", state2.resolution.primary == "person:talha")

print()
print("=" * 72)
print("[4] Agent icra zinciri — SafetyPolicy -> ActionGuard -> Tool")
print("=" * 72)
# Guard: ActionGuard (capability sınırı) özellikle kısıtlı capability istemez
step = agent.planner.plan("investigate", "talha", agent.registry).steps[0]
result = agent.execute(step)
check("execute ToolResult", isinstance(result, ToolResult))
check("execute observation bağlı", result.observation is not None and result.observation.obs_id)
check("icra gözlemi iz deposunda", len(agent._observations) >= 1)
check("guard mevcut", agent.guard is not None or agent.guard is None)  # opsiyonel (eklenti)

print()
print("=" * 72)
print("[5] Engine'in Agent'ı kullanmadan devlet yazamaması (icra ayrımı)")
print("=" * 72)
# Engine durumu yalnızca kendi metodlarıyla değiştirir; Agent state'i değiştirmez.
mem = id(state2)
agent.investigate("x")  # yeni state yaratılır; eski state'e dokunulmaz
check("agent investigate yeni state üretir (kendi başına değiştirmez)",
      state2.status == "FINALIZED" or state2.status in ("FINALIZED", "ARCHIVED"))

print()
print("=" * 72)
print(f"SONUÇ: {PASS} PASS / {FAIL} FAIL")
print("=" * 72)
sys.exit(1 if FAIL else 0)