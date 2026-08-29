"""Corvus Corax Cross-Source Corroboration & Conflict Detection Engine.

Farklı bağımsız modüllerden gelen kanıtların birbirini teyit etmesini (Corroboration)
veya birbiriyle çelişmesini (Conflict Detection) hesaplar.
"""
from collections import defaultdict


class Corroborator:
    """Çapraz Kaynak Teyit ve Çelişki Tespit Motoru."""

    def __init__(self):
        self.conflicts = []

    def corroborate_evidence_list(self, evidence_list: list) -> tuple:
        """
        Kanıt listesini tarayarak teyitleri ve çelişkileri bulur.

        Returns:
            (corroborated_evidence_list, conflicts_list)
        """
        # Hedef ve type bazında grupla: (target, type) -> list of Evidence
        grouped = defaultdict(list)
        for ev in evidence_list:
            grouped[(ev.target, ev.evidence_type)].append(ev)

        self.conflicts = []

        for (target, ev_type), items in grouped.items():
            if len(items) <= 1:
                continue

            # Kaynaklar ve değerler haritası
            value_map = defaultdict(set)
            for ev in items:
                value_map[ev.observed_value].add(ev.source_module)

            # 1. Corroboration (Teyit): Aynı değer birden fazla farklı modül tarafından bulundu mu?
            for val, sources in value_map.items():
                if len(sources) > 1:
                    for ev in items:
                        if ev.observed_value == val:
                            ev.corroborating_sources.update(sources)
                            # Bağımsız teyit puanı artışı (NATO Admiralty boost)
                            ev.confidence = min(0.99, round(ev.confidence + (0.1 * (len(sources) - 1)), 2))
                            ev.admiralty_code = "A1" if ev.confidence >= 0.9 else "B1"

            # 2. Conflict Detection (Çelişki Tespiti): Aynı tip için farklı çelişkili değerler var mı?
            if len(value_map) > 1:
                conflict_entry = {
                    "target": target,
                    "evidence_type": ev_type,
                    "competing_values": [],
                    "resolution": None,
                }
                highest_conf = -1.0
                best_val = None

                for val, sources in value_map.items():
                    # Bu değer için max güven puanı
                    val_conf = max(e.confidence for e in items if e.observed_value == val)
                    conflict_entry["competing_values"].append({
                        "value": val,
                        "sources": list(sources),
                        "confidence": val_conf,
                    })
                    if val_conf > highest_conf:
                        highest_conf = val_conf
                        best_val = val

                conflict_entry["resolution"] = f"Weighted Resolution favors '{best_val}' (confidence: {highest_conf})"
                self.conflicts.append(conflict_entry)

                # Çelişkili kanıtları bayrakla
                for ev in items:
                    if ev.observed_value != best_val:
                        ev.status = "CONFLICT"
                        ev.confidence = round(ev.confidence * 0.5, 2)

        return evidence_list, self.conflicts
