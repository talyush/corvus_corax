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
from typing import Dict, Any, Optional


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

        if action == "semantic":
            # v1.3: Topic graph & interest drift — Muninn geçmişinden past_texts alınır
            from core.human.semantic import SemanticInterestNetwork
            sem = SemanticInterestNetwork()
            sample_texts = [target, f"{target} cyber security analysis"]
            topics = sem.extract_topics(sample_texts)

            drift = None
            try:
                from core.muninn.store import MuninnStore
                store = MuninnStore()
                eh = store.get_history(target)
                if eh and len(eh.snapshots) >= 2:
                    past_texts = eh.snapshot_texts(limit=20)
                    drift = sem.analyze_interest_drift(past_texts, sample_texts)
            except Exception:
                drift = None

            self.add_note(f"Semantic interest graph generated ({len(topics)} topics)", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "semantic",
                    "target": target,
                    "topics": dict(topics.most_common(8)),
                    "dominant_topics": [t[0] for t in topics.most_common(3)],
                    "interest_drift": drift,
                }
            )

        if action == "anomaly":
            # v1.3: İnsan + teknik anomali — Muninn baseline ile karşılaştır
            events = self.context.get_entity_events(target) if self.context and hasattr(self.context, "get_entity_events") else []
            timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
            current = engine.generate_human_profile(
                target=target, texts=[target, f"{target} analysis"], timestamps=timestamps
            )

            baseline = None
            try:
                from core.muninn.store import MuninnStore
                store = MuninnStore()
                eh = store.get_history(target)
                if eh and eh.current_attributes:
                    baseline = {
                        "stylometry": {"sentence_length": {"mean": None}, "vocabulary_diversity": {"ttr": eh.current_attributes.get("stylometry_ttr", 0)}},
                        "timing": {"probable_timezone_estimate": eh.current_attributes.get("probable_timezone", "")},
                        "infrastructure": {"distinct_asns_used": []},
                    }
                    baseline["stylometry"]["sentence_length"]["mean"] = eh.current_attributes.get("stylometry_mean_sentence", 0)
            except Exception:
                baseline = None

            anomaly = engine.anomaly.detect_anomalies(target, current, baseline)
            self.add_note(f"Anomaly evaluation: score {anomaly['anomaly_score']} ({anomaly['anomaly_level']})", severity="info")
            return self.success(
                target=target,
                data={
                    "action": "anomaly",
                    "target": target,
                    "anomaly": anomaly,
                    "has_baseline": baseline is not None,
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

        # v1.3-2: Profili Muninn'e kaydet (kalıcı hafıza + gelecek drift analizi)
        muninn_data = self._save_to_muninn(full_profile, target)
        if muninn_data:
            self.add_note(f"Profile archived to Muninn ({muninn_data.get('note', '')})", severity="info")
            full_profile["muninn_archived"] = True
            full_profile["muninn_history"] = muninn_data

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

    def _save_to_muninn(self, profile: Dict[str, Any], target: str) -> Optional[Dict[str, Any]]:
        """v1.3-2: İnsan profilini Muninn kalıcı hafızasına yazar ve önceki
        profil varsa otomatik drift/anomali analizi üretir."""
        try:
            from core.muninn.store import MuninnStore

            store = MuninnStore()
            prev = store.get_history(target)

            # Önceki profil var mı? (baseline / drift için)
            has_baseline = prev is not None and bool(prev.current_attributes)

            era = len(prev.snapshots) if prev else 0
            changes = store.record_snapshot(
                entity_id=target,
                entity_type="person_human",
                attributes={
                    "persona_technical_depth": profile.get("persona", {}).get("technical_depth", ""),
                    "communication_tone": profile.get("persona", {}).get("communication_tone", ""),
                    "stylometry_mean_sentence": profile.get("stylometry", {}).get("sentence_length", {}).get("mean", 0),
                    "stylometry_ttr": profile.get("stylometry", {}).get("vocabulary_diversity", {}).get("ttr", 0),
                    "probable_timezone": profile.get("timing", {}).get("probable_timezone_estimate", ""),
                    "peak_hours_utc": profile.get("timing", {}).get("peak_hours_utc", ""),
                    "dominant_topics": ",".join(profile.get("dominant_topics", [])),
                    "anomaly_score": profile.get("anomaly_assessment", {}).get("anomaly_score", 0),
                },
                relations=profile.get("dominant_topics", []),
                source_module="human",
                confidence=0.8,
            )

            note = f"{len(changes)} öznitelik değişikliği, #{era + 1} gözlem"

            # Otomatik drift analizi (semantic)
            drift_data = None
            if has_baseline and prev is not None:
                try:
                    from core.human.semantic import SemanticInterestNetwork
                    sem = SemanticInterestNetwork()
                    past_texts = prev.snapshot_texts(limit=20)
                    current_texts = [target, " ".join(profile.get("dominant_topics", []))]
                    drift_data = sem.analyze_interest_drift(past_texts, current_texts)
                except Exception:
                    drift_data = None

            return {
                "note": note,
                "has_baseline": has_baseline,
                "snapshot_era": era + 1,
                "changes_detected": len(changes),
                "semantic_drift": drift_data,
            }
        except Exception as e:
            return {"note": f"Muninn kaydı başarısız: {e}", "has_baseline": False}
