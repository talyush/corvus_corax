"""Corvus Corax v1.1.2 — Self-Learning Module (CLI).

Kullanım:
  learning            -> öğrenme durumu + kalibrasyon özeti
  learning audit      -> mimar denetim raporu (son 30 değişiklik)
  learning feedback <arac> <memnuniyet 1-5> <not>  -> geri bildirim ekle
  learning patterns   -> öğrenilmiş başarısızlık desenleri
  learning stats      -> araç istatistikleri (calibrasyon)
"""

from core.module_base import BaseModule


class LearningModule(BaseModule):
    """v1.1.2 — Self-Learning görünümü ve geri bildirim kanalı."""

    name = "learning"

    def execute(self):
        args = self.target or []
        args = list(args) if isinstance(args, (list, tuple)) else str(args).split()

        from core.learning.experience import ExperienceStore
        from core.learning.calibration import CalibrationEngine
        from core.learning.patterns import PatternLearning
        from core.learning.feedback import FeedbackLoop
        from core.learning.audit import AuditLog

        store = ExperienceStore()
        cal = CalibrationEngine(store)
        patterns = PatternLearning(store)
        feedback = FeedbackLoop(store)
        audit = AuditLog()

        sub = args[0].lower() if args else "status"

        inv = self.begin_investigation(
            "Self-Learning Status",
            ["EXPERIENCE STORE", "CALIBRATION", "PATTERNS", "AUDIT"],
        )

        if sub == "audit":
            with inv.phase(3):
                self.status_step("Reading audit trail")
            entries = audit.recent(limit=30)
            lines = ["=" * 60, "AUDIT — Mimar Denetim Raporu", "=" * 60]
            for e in entries:
                ts = e.get("ts", "")[11:19]
                typ = e.get("type", "?")
                tool = e.get("tool", "")
                if typ == "calibration":
                    lines.append(f"  [{ts}] KALİBRASYON {tool}: {e.get('old_weight')} -> {e.get('new_weight')}")
                elif typ == "pattern_learned":
                    lines.append(f"  [{ts}] DESEN: {e.get('tool')} ({e.get('error_type')} x{e.get('count')})")
                elif typ == "user_feedback":
                    lines.append(f"  [{ts}] KULLANICI: {tool} (memnuniyet {e.get('satisfaction')}): {e.get('note','')[:60]}")
                elif typ == "selection_learned":
                    lines.append(f"  [{ts}] SEÇİM ({e.get('target_type')}): {e.get('original')} -> {e.get('reordered')}")
                else:
                    lines.append(f"  [{ts}] {typ}: {tool} {e.get('status','')}")
            return self.success(target="audit", data={"audit_entries": entries, "report": "\n".join(lines)})

        if sub == "feedback" and len(args) >= 3:
            with inv.phase(0):
                self.status_step("Recording user feedback")
            tool = args[1]
            try:
                sat = int(args[2])
            except ValueError:
                sat = 3
            note = " ".join(args[3:]) if len(args) > 3 else ""
            feedback.self_feedback(tool, sat, note)
            if self.context:
                self.context.add_note(f"Feedback: {tool} memnuniyet {sat}", source="learning", severity="info")
            return self.success(target=tool, data={"feedback_recorded": tool, "satisfaction": sat, "note": note})

        if sub == "patterns":
            with inv.phase(2):
                self.status_step("Extracting learned patterns")
            patterns.learn_from_recent()
            mature = patterns.mature_patterns()
            return self.success(target="patterns", data={
                "pattern_count": len(patterns.patterns),
                "mature": [p.to_dict() for p in mature],
            })

        if sub == "stats" or sub == "calibration":
            with inv.phase(1):
                self.status_step("Calibrating tool weights")
            cal.calibrate_all()
            stats = store.stats()
            return self.success(target="stats", data={"tool_stats": stats})

        # default: status
        with inv.phase(1):
            self.status_step("Calibrating tool weights")
        cal.calibrate_all()
        summary = store.summary()
        patterns.learn_from_recent()
        cal_summary = cal.summary()
        audit_summary = audit.summary()

        return self.success(target="learning", data={
            "summary": summary,
            "calibration": cal_summary,
            "patterns": [p.to_dict() for p in patterns.mature_patterns()],
            "audit": audit_summary,
        })