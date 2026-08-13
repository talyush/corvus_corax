import os
from core.module_base import BaseModule
from core.config import load_rules


class PolModule(BaseModule):
    """
    v0.9 — Pattern of Life (POL) Analiz Modülü.

    Komutlar:
      pol analyze <entity> [--vault-only]   → Davranış deseni + anomali skoru
      pol compare <e1> <e2>                 → İki varlığın davranış karşılaştırması
      pol casefile <entity> [file]          → Soruşturma dosyası üret
      pol timeline <entity>                 → Temporal zaman çizelgesi
    """
    name = "pol"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: pol <analyze|compare|casefile|timeline> <entity> [--vault-only]")

        action = args[0].lower()
        vault_only = "--vault-only" in args
        entities = [a for a in args[1:] if not a.startswith("--")]

        rules = load_rules()
        pol_cfg = rules.get("pol", {})
        vault_dir = pol_cfg.get("vault_dir", "vault")

        # Vault'u başlat
        from core.db import IntelligenceVault
        vault = IntelligenceVault(vault_dir)

        from core.pol import PatternOfLifeEngine
        engine = PatternOfLifeEngine(self.context, vault)

        # --- ANALYZE ---
        if action == "analyze":
            if not entities:
                return self.error("usage: pol analyze <entity> [--vault-only]")
            entity = entities[0]

            activity = engine.analyze_activity(entity, vault_only)
            movement = engine.analyze_movement(entity, vault_only)
            comm = engine.analyze_communications(entity, vault_only)
            anomalies = engine.detect_anomalies(entity, vault_only)

            self.add_note(
                f"POL analysis for {entity}: anomaly score {anomalies['score']}/100 ({anomalies['level']})",
                severity="warning" if anomalies["score"] >= 50 else "info",
            )

            return self.success(target=entity, data={
                "action": "analyze",
                "entity": entity,
                "vault_only": vault_only,
                "activity": activity,
                "movement": movement,
                "communications": comm,
                "anomaly": anomalies,
            })

        # --- COMPARE ---
        elif action == "compare":
            if len(entities) < 2:
                return self.error("usage: pol compare <entity1> <entity2>")
            e1, e2 = entities[0], entities[1]

            a1 = engine.detect_anomalies(e1, vault_only)
            a2 = engine.detect_anomalies(e2, vault_only)

            self.add_note(
                f"POL comparison: {e1} (score {a1['score']}) vs {e2} (score {a2['score']})",
                severity="info",
            )

            return self.success(target=f"{e1} vs {e2}", data={
                "action": "compare",
                "entity1": e1,
                "entity2": e2,
                "anomaly1": a1,
                "anomaly2": a2,
            })

        # --- CASEFILE ---
        elif action == "casefile":
            if not entities:
                return self.error("usage: pol casefile <entity> [file]")
            entity = entities[0]
            filepath = entities[1] if len(entities) > 1 else None

            ok, msg, casefile = engine.save_casefile(entity, filepath, vault_only)
            if not ok:
                return self.error(msg)
            self.add_note(msg, severity="info")
            return self.success(target=entity, data={
                "action": "casefile",
                "entity": entity,
                "filepath": msg.split("to ")[-1] if "to " in msg else filepath,
                "message": msg,
                "anomaly_score": casefile.get("anomaly", {}).get("score", 0),
            })

        # --- TIMELINE ---
        elif action == "timeline":
            if not entities:
                return self.error("usage: pol timeline <entity>")
            entity = entities[0]

            events = engine._get_events(entity, vault_only)
            self.add_note(f"POL timeline for {entity}: {len(events)} events", severity="info")
            return self.success(target=entity, data={
                "action": "timeline",
                "entity": entity,
                "event_count": len(events),
                "events": events[:50],
            })

        return self.error(f"Unknown pol action: {action}. Use: analyze, compare, casefile, timeline")