"""Corvus Corax v1.2 Faz C — Agent Module (CLI).

Kullanım:  agent <hedef>
           agent example.com
           agent 8.8.8.8 araştır

Doğal dil 'X araştır' talebi CLI'a 'agent X' olarak da ulaşabilir.
Güvenli otonom akış: plan üret -> onay (network araçları) -> aksiyon -> gözlem -> özet.
"""

from core.module_base import BaseModule
from core.agent.agent import Agent
from core.agent.policy import Approval


class AgentModule(BaseModule):
    """Faz C — Otonom İstihbarat Ajanı (plan+araç+gözlem döngüsü)."""

    name = "agent"

    def _resolve_approval(self, value):
        """'güvenli', 'auto', 'ask', 'deny' tanıyıcıları."""
        v = (value or "").lower()
        if v in ("auto", "yes", "1", "true"):
            return Approval.AUTO
        if v == "ask":
            return Approval.ASK
        return Approval.ASK  # varsayılan güvenli

    def execute(self):
        args = self.target or []
        args = list(args) if isinstance(args, (list, tuple)) else str(args).split()

        if not args:
            return self.success(
                target="agent",
                data={
                    "usage": "agent <hedef> [--guvenli|--auto]",
                    "example": "agent example.com",
                    "help": "Hedef tipi otomatik algılanır; network araçları onay ister.",
                },
            )

        # [--ignore] seçeneklerini ayıkla
        mode = "ask"
        clean = []
        for a in args:
            if a.startswith("--"):
                mode = a[2:]
            else:
                clean.append(a)

        target_text = " ".join(clean)

        inv = self.begin_investigation(
            f"Autonomous Investigation — {target_text}",
            ["PLANNING", "INTENT → PLAN", "OBSERVE → ACT → OBSERVE"],
        )

        with inv.phase(0):
            self.status_step("Parsing target and building tool plan")

        # Agent'ı kur; approval_mode: auto->AUTO, _->ASK (kullanıcı onayı)
        approval = Approval.AUTO if mode in ("auto", "yes") else Approval.ASK
        agent = Agent(
            module_registry=(
                self.context and getattr(self.context, "_modules", None)
            ) or {},
            config=self.config,
            logger=self.logger,
            context=self.context,
            approval_mode=approval,
        )

        # Registry'yi gerçek modüllerle doldur — context üzerinden taşınmadıysa
        if not agent.registry.available:
            from core.loader import load_modules
            modules = load_modules()
            agent.registry.sync_with_modules(modules)
            agent.modules = modules

        with inv.phase(1):
            self.status_step("Running observation→action→observation loop")
            report = agent.investigate(target_text)

        return self.success(
            target=target_text,
            data={
                "intent": report["intent"],
                "target_type": report["target_type"],
                "plan": report["plan"],
                "executed": report["executed"],
                "observations": report["observations"],
                "summary": report["summary"],
                "pivot_leads": report["pivot_leads"],
            },
        )