"""Corvus Corax v1.2 - Huginn Reasoning CLI Module.

"Huginn thinks."
Commands:
  huginn explain <target>    - Full structured reasoning explanation
  huginn why <target>        - Justification rationale & why alternatives were filtered
  huginn trace <target>      - Step-by-step Observation -> Interpretation -> Hypothesis -> Decision
  huginn hypotheses <target> - Bayesian hypotheses breakdown
  huginn synergy <target>    - Full synergy report (Muninn memory + Huginn reasoning + Corvus decision)
"""
from core.module_base import BaseModule
from core.huginn.explainer import HuginnExplainer
from core.decision.corvus_mind import CorvusDecisionCore


class HuginnModule(BaseModule):
    name = "huginn"
    description = "Huginn Reasoning & Analytical Explainer Engine"

    def execute(self):
        args = self.target or []
        if isinstance(args, str):
            args = args.split()

        action = args[0] if len(args) > 0 else "explain"
        target = args[1] if len(args) > 1 else ""

        valid_actions = {"explain", "why", "trace", "hypotheses", "synergy", "drift"}
        if action not in valid_actions and not target:
            target = action
            action = "explain"

        if not target:
            return self.error("Target parameter is required. Usage: huginn explain <target>")

        inv = self.begin_investigation(
            f"Huginn Reasoning Assessment: {action} on '{target}'",
            ["ANALYTICAL REASONING", "PROVENANCE EXPLANATION"]
        )

        with inv.phase(0):
            self.status_step(f"Building reasoning trace for '{target}' via action '{action}'")

        explainer = HuginnExplainer(context_manager=self.context)
        decision_core = CorvusDecisionCore(context_manager=self.context)

        if action == "why":
            report = explainer.why(target)
            self.add_note(f"Justification report generated for '{target}'", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "why",
                    "target": target,
                    "report": report,
                }
            )

        if action == "trace":
            report = explainer.trace(target)
            self.add_note(f"Step-by-step reasoning trace generated for '{target}'", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "trace",
                    "target": target,
                    "report": report,
                }
            )

        if action == "drift":
            report = decision_core.why_conclusion_changed(target)
            self.add_note(f"Conclusion drift rationale generated for '{target}'", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "drift",
                    "target": target,
                    "report": report,
                }
            )

        if action == "synergy":
            report = decision_core.explain_with_history(target)
            self.add_note(f"Huginn-Muninn synergy report generated for '{target}'", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "synergy",
                    "target": target,
                    "report": report,
                }
            )

        # Default: explain
        report = explainer.explain(target)
        self.add_note(f"Reasoning explanation generated for '{target}'", severity="info")
        return self.success(
            target=target,
            data={
                "action": "explain",
                "target": target,
                "report": report,
            }
        )
