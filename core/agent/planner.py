"""Corvus Agent Layer — Planner.

Kullanıcı niyetini (intent) ve hedef varlığı; aksiyona dönüştürülecek
adımlardan (InvestigationPlan) oluşan bir plana çevirir.
Plan, hangi araçların hangi sırayla çalışacağını ve her adımın neden
seçildiğini (rationale) içerir — tam şeffaflık.

Akış: intent + target -> plan adımları -> onay -> aksiyon
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class PlanStep:
    tool: str
    target: str
    target_type: str
    rationale: str = ""
    applied: bool = False
    observation_ref: str = ""     # bu adımın ürettiği gözlem özeti


@dataclass
class InvestigationPlan:
    intent: str
    target: str
    target_type: str
    steps: List[PlanStep] = field(default_factory=list)

    def to_summary(self) -> str:
        steps = "\n".join(
            f"    {i+1}. {s.tool}({s.target}:{s.target_type}) — {s.rationale}"
            for i, s in enumerate(self.steps)
        )
        return f"PLAN [{self.intent}]: {self.target}\n{steps}"


class Planner:
    """Niyeti ve hedefi plan adımlarına çevirir."""

    # Hedef tipi -> öncelikli araçlar (registry order'ı tamamlar)
    PREFERENCES = {
        "domain": ["whois", "dns", "tech", "cert", "metadata", "footprint"],
        "ip": ["geoip", "asn"],
        "person": ["social", "github", "academic"],
        "organization": ["org"],
        "email": ["breach", "email"],
        "phone": ["phone"],
        "wallet": ["wallet"],
        "username": ["social", "github"],
    }

    IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,15}$")

    def classify(self, target: str) -> str:
        t = target.strip().lower()
        if self.EMAIL_RE.match(t):
            return "email"
        if self.IP_RE.match(t):
            return "ip"
        if self.PHONE_RE.match(t):
            return "phone"
        if "." in t and " " not in t and not t.endswith((".com", ".org", ".net", ".io", ".ai", ".gov", ".edu")):
            # generic domain-ish
            if " " not in t:
                return "domain"
        if "." in t and " " not in t:
            return "domain"
        return "person"

    # ------------------------------------------------------------------
    def plan(self, intent: str, target: str, registry, max_steps: int = 6) -> InvestigationPlan:
        target_type = self.classify(target)
        pref = self.PREFERENCES.get(target_type, [])
        steps: List[PlanStep] = []

        # Registry'den hedef için uygun araçları al, pref'leri öne al
        candidates = registry.tools_for_target(target_type)
        ordered = [t for t in pref if t in candidates] + [t for t in candidates if t not in pref]

        for tool in ordered[:max_steps]:
            if not registry.is_available(tool):
                continue
            spec = registry.get(tool)
            scope_label = "NET" if registry.is_network(tool) else "LOCAL"
            rationale = f"{scope_label} — {spec.description if spec else ''}".strip()
            steps.append(PlanStep(
                tool=tool,
                target=target,
                target_type=target_type,
                rationale=rationale,
            ))

        return InvestigationPlan(intent=intent, target=target, target_type=target_type, steps=steps)