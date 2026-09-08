"""Corvus Corax v1.2 — Faz C: Agent Layer.

Corvus'u pasif sohbetten AKTİF araca dönüştürür:
    intent -> plan -> tool selection -> action -> observation -> reflect -> (repeat)

Güvenli otonom politika:
  - Yerel analiz/context araçları (nexus, evidence, resolve, pol, pivot) OTOMATİK.
  - Dış ağ çağrısı yapan araçlar (whois, dns, geoip, scan, social...) KULLANICI ONAYI ister.
  - Her gözlem, yeni varlık/pivot adaylarını reflec'ler ve döngü iteration limitiyle sınırlıdır.

Reflection: her gözlemin sonunda "yeni ne öğrendim, hangi varlıklar daha derine inmeye değer?"
sorusunu sorar. observation -> action -> observation döngüsünün kalbi budur.
"""

from .tools import ToolRegistry, ToolSpec
from .policy import SafetyPolicy, Approval, ToolScope
from .planner import Planner, PlanStep, InvestigationPlan
from .executor import ToolExecutor, Observation
from .agent import Agent

__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "SafetyPolicy",
    "Approval",
    "ToolScope",
    "Planner",
    "PlanStep",
    "InvestigationPlan",
    "ToolExecutor",
    "Observation",
    "Agent",
]