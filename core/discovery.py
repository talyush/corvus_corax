"""Corvus Corax v0.9/Faz 6 — Discovery Engine.

Kullanıcı tarafından verilen seed'i başlangıç noktası olarak kabul eder,
otomatik keşif zinciri başlatır ve KULLANICININ BİLMEDİĞİ yeni entity'ler,
evidence'ler ve bağlantılar üretir.

Akış:
  user -> seed -> investigation -> new evidence -> new entities -> pivots -> unexpected relationships

Seed ≠ Evidence:
  - source=user_input olan veri seed'dir, ASLA evidence değildir.
  - source=corvus (modül) tarafından bulunan veri evidence'dır.
"""
from datetime import datetime, timezone


from core.strategy import AutonomousStrategyEngine


class DiscoveryEngine:
    """Otomatik keşif motoru — seed'den başlayarak akıllı hipotezler ve yön değiştirmelerle yeni istihbarat bulur."""

    def __init__(self, context_manager, config=None, logger=None, module_registry=None):
        self.context = context_manager
        self.config = config or {}
        self.logger = logger
        self.modules = module_registry or {}
        self.strategy_engine = AutonomousStrategyEngine(
            context_manager=self.context,
            module_registry=self.modules,
            logger=self.logger,
        )

    def _infer_seed_type(self, seed_value: str) -> str:
        """Seed değerinin türünü tahmin eder (person, domain, ip, email, phone)."""
        val = seed_value.strip().lower()
        if "@" in val:
            return "email"
        if val.startswith("+") or (val.replace(" ", "").isdigit() and len(val.replace(" ", "")) >= 7):
            return "phone"
        if "." in val and not any(char.isalpha() for char in val.split(".")[-1]) and len(val.split(".")) == 4:
            return "ip"
        if "." in val and len(val.split(".")) >= 2:
            return "domain"
        return "person"

    def investigate(self, seed_value, max_depth=3, max_entities=25, status_callback=None):
        """
        Seed değerinden başlayarak otonom stratejik keşif zinciri çalıştırır.
        """
        seed_type = self._infer_seed_type(seed_value)

        # 1. Context'e seed ekle
        self.context.add_entity(
            seed_type, seed_value,
            provenance={"source": "user_input", "status": "seed"}
        )

        # 2. Otonom Strateji Motorunu çalıştır
        report = self.strategy_engine.execute_autonomous_investigation(
            seed_value=seed_value,
            seed_type=seed_type,
            status_callback=status_callback
        )

        return report

    def print_report(self, report):
        """İnsanokuyanablir keşif raporu üretir."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"INVESTIGATION REPORT — Seed: {report['seed']}")
        lines.append("=" * 70)

        if report.get("no_new_findings"):
            lines.append("\n  No new entities discovered beyond seed.")
            return "\n".join(lines)

        lines.append(f"\n  Seed: {report['seed']} [source=user_input, status=seed]")
        for p in report.get("discovered_path", []):
            prefix = "  ├─" if p["depth"] == 1 else f"  │ {' ' * (p['depth']*2)}└─"
            line = f"{prefix} [DISCOVERED] {p['entity_type']}:{p['entity_value']}"
            line += f" (discovered_by={p['discovered_by']})"
            if p.get("via"):
                line += f" via {p['via']}"
            lines.append(line)
            if p.get("evidence"):
                lines.append(f"  │ {' ' * (p['depth']*2)}   evidence: {p['evidence']}")

        lines.append("\n" + "-" * 70)
        lines.append(f"  Novelty Score: {report['novelty_score']:.2f} ({report['discovered_count']} new entities / {report['total_entities']} total)")
        lines.append(f"  Discovery Depth: {report['max_depth']}")
        lines.append(f"  Unexpected Connections: {len(report['unexpected_connections'])}")
        lines.append("=" * 70)
        lines.append("  [NOTE] Seed is user-provided; all discovered entities are Corvus evidence.")
        lines.append("  [NOTE] Found ≠ Verified. Confidence reflects discovery method.")
        return "\n".join(lines)