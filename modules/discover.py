from core.module_base import BaseModule
from colorama import Fore, Style


class DiscoverModule(BaseModule):
    """
    v0.9.1-autonomous — Autonomous Strategy & Discovery.

    Kullanıcının verdiği seed'den başlayarak otonom strateji motorunu çalıştırır.
    Hipotezler üretir, hedefleri ayrıştırır (Goal Decomposition), başarısızlıkları
    yönetir (Failure Awareness) ve dinamik yön değiştirmelerle (Pivoting) istihbarat toplar.
    """
    name = "discover"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: discover <seed> [--depth=N]")

        seed = args[0]

        from core.discovery import DiscoveryEngine
        from core.loader import load_modules

        module_registry = {}
        try:
            module_registry = load_modules()
        except Exception:
            pass

        inv = self.begin_investigation(
            f"Autonomous Investigation Strategy & Capability Probing for '{seed}'",
            ["HYPOTHESIS FORMULATION", "PUBLIC SEARCH PROBING", "PIVOTING & CORRELATION"]
        )

        def status_cb(msg):
            self.status_step(msg)

        engine = DiscoveryEngine(self.context, self.config, self.logger, module_registry)

        with inv.phase(0):
            report = engine.investigate(seed_value=seed, status_callback=status_cb)

        total_entities = report.get("total_entities", 0)
        total_relations = report.get("total_relations", 0)

        self.add_note(
            f"Autonomous Strategy finished for '{seed}': {total_entities} entities, {total_relations} relations in graph",
            severity="info",
        )

        return self.success(target=seed, data=report)