"""Corvus Corax v1.2 - Muninn Memory CLI Module.

"Muninn remembers."
Commands:
  muninn history <target>  - View complete historical timeline and snapshots
  muninn changes <target>  - View detected attribute changes and drift
  muninn recall <target>   - Deep recall across memory, knowledge, and active graph
  muninn list              - List all entities remembered by Muninn
"""
from core.module_base import BaseModule
from core.muninn.store import MuninnStore
from core.muninn.recall import MuninnRecallEngine


class MuninnModule(BaseModule):
    name = "muninn"
    description = "Muninn Historical Memory & Attribute Drift Engine"

    def execute(self):
        args = self.target or []
        if isinstance(args, str):
            args = args.split()

        action = args[0] if len(args) > 0 else "history"
        target = args[1] if len(args) > 1 else ""

        valid_actions = {"history", "changes", "drift", "recall", "list", "snapshot"}
        if action not in valid_actions and not target:
            target = action
            action = "history"

        inv = self.begin_investigation(
            f"Muninn Memory Query: {action} on '{target or 'all'}'",
            ["HISTORICAL MEMORY", "TEMPORAL RECALL"]
        )

        store = MuninnStore()
        engine = MuninnRecallEngine(store=store, context_manager=self.context)

        with inv.phase(0):
            self.status_step(f"Accessing Muninn Memory Vault for action '{action}'")

        if action == "list":
            entities = store.list_known_entities()
            self.add_note(f"Muninn tracks {len(entities)} entity histories", severity="info")
            return self.success(
                target="all",
                data={
                    "action": "list",
                    "known_entities": entities,
                    "count": len(entities),
                }
            )

        if not target:
            self.add_note("Target required for muninn query", severity="warning")
            return self.error("Target parameter is required. Usage: muninn history <target>")

        if action in ("changes", "drift"):
            changes = engine.detect_attribute_drift(target)
            report = engine.format_history_report(target)
            self.add_note(f"Found {len(changes)} attribute drift events for {target}", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "changes",
                    "target": target,
                    "changes": changes,
                    "report": report,
                }
            )

        # Default: history / recall
        recall_data = engine.recall_entity(target)
        report = engine.format_history_report(target)
        self.add_note(f"Recalled history for '{target}' (Observations: {recall_data['observation_count']})", severity="info")

        return self.success(
            target=target,
            data={
                "action": action,
                "target": target,
                "recall": recall_data,
                "report": report,
            }
        )
