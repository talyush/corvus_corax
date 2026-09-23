"""Corvus Corax v1.3 - Human Intelligence CLI Module.

"From Infrastructure Intelligence -> Human-Centered Intelligence."
Commands:
  human profile <target>           - Generate full human intelligence profile
  human stylometry <text_sample>   - Run stylometric analysis on text
  human timing <target>            - Analyze 24h activity rhythm & probable timezone
  human compare <target1> <target2>- Compare two profiles (Similarity != Identity)
  human semantic <target>          - Topic graph & interest drift analysis
  human anomaly <target>           - Human + Technical anomaly detection
"""
from core.module_base import BaseModule
from core.human.engine import HumanIntelligenceEngine


class HumanModule(BaseModule):
    name = "human"
    description = "Human-Centered Intelligence, Stylometry & Behavioral Profiling Engine"

    def execute(self):
        args = self.target or []
        if isinstance(args, str):
            args = args.split()

        action = args[0] if len(args) > 0 else "profile"
        target = args[1] if len(args) > 1 else ""

        valid_actions = {"profile", "stylometry", "timing", "compare", "semantic", "anomaly"}
        if action not in valid_actions and not target:
            target = action
            action = "profile"

        if not target:
            return self.error("Target parameter is required. Usage: human profile <target>")

        inv = self.begin_investigation(
            f"Human Intelligence Assessment: {action} on '{target}'",
            ["PERSONA EXTRACTION", "BEHAVIORAL PROFILING", "STYLOMETRY & RHYTHM"]
        )

        engine = HumanIntelligenceEngine(context_manager=self.context)

        with inv.phase(0):
            self.status_step(f"Engaging Human Intelligence Engine for action '{action}'")

        if action == "stylometry":
            # Text veya hedef analizi
            text_sample = " ".join(args[1:]) if len(args) > 1 else target
            res = engine.stylometry.analyze(text_sample)
            self.add_note(f"Stylometric profile generated (Total words: {res['total_words']})", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "stylometry",
                    "target": target,
                    "stylometry": res,
                }
            )

        if action == "timing":
            # Context'teki olay zaman damgalarını topla
            events = self.context.get_entity_events(target) if self.context and hasattr(self.context, "get_entity_events") else []
            timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
            res = engine.timing.analyze_timestamps(timestamps)
            self.add_note(f"Timing rhythm analyzed ({res['total_samples']} samples)", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "timing",
                    "target": target,
                    "timing": res,
                }
            )

        if action == "compare":
            target2 = args[2] if len(args) > 2 else "target2"
            prof_a = engine.generate_human_profile(target, texts=[target])
            prof_b = engine.generate_human_profile(target2, texts=[target2])
            comparison = engine.similarity.compare_profiles(prof_a, prof_b)
            self.add_note(f"Similarity comparison: {comparison['overall_similarity_percentage']} (Similarity != Identity)", severity="info")
            return self.success(
                target=f"{target} <-> {target2}",
                data={
                    "action": "compare",
                    "target1": target,
                    "target2": target2,
                    "comparison": comparison,
                }
            )

        # Default: Full human profile
        events = self.context.get_entity_events(target) if self.context and hasattr(self.context, "get_entity_events") else []
        timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
        sample_texts = [target, f"{target} security analysis and infrastructure reconnaissance"]
        
        full_profile = engine.generate_human_profile(
            target=target,
            texts=sample_texts,
            timestamps=timestamps
        )
        report = engine.format_human_report(full_profile)

        self.add_note(f"Full human intelligence profile compiled for '{target}'", severity="info")
        return self.success(
            target=target,
            data={
                "action": "profile",
                "target": target,
                "profile": full_profile,
                "report": report,
            }
        )
