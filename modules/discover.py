from core.module_base import BaseModule


class DiscoverModule(BaseModule):
    """
    v0.9/Faz 6 — Discovery Semantics.

    Kullanıcının verdiği seed'den başlayarak otomatik keşif zinciri başlatır.
    Kullanıcının bilmediği yeni entity'ler, evidence'ler ve bağlantılar üretir.
    Novelty Score hesaplar (Corvus'un başarısı = kaç YENİ bağlantı buldu).

    Seed ≠ Evidence: Kullanıcı verisi seed'dir, Corvus'un bulduğu evidence'dır.
    """
    name = "discover"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: discover <seed> [--depth=N]")

        seed = args[0]
        depth = 3
        for arg in args[1:]:
            if arg.startswith("--depth="):
                try:
                    depth = int(arg.split("=", 1)[1])
                except ValueError:
                    pass

        from core.discovery import DiscoveryEngine

        # Modül registry'sini al
        module_registry = None
        try:
            from core.loader import load_modules
            module_registry = load_modules()
        except Exception:
            module_registry = {}

        engine = DiscoveryEngine(self.context, self.config, self.logger, module_registry)
        report = engine.investigate(seed, max_depth=depth)

        self.add_note(
            f"Discovery for {seed}: {report['discovered_count']} new entities "
            f"(novelty: {report['novelty_score']:.2f})",
            severity="info",
        )

        # İnsan okunabilir raporu üret
        report_text = engine.print_report(report) if hasattr(engine, "print_report") else str(report)

        data = {
            "seed": seed,
            "novelty_score": report["novelty_score"],
            "total_entities": report["total_entities"],
            "discovered_count": report["discovered_count"],
            "unexpected_connections": len(report["unexpected_connections"]),
            "discovered_path": report["discovered_path"],
            "report_text": report_text,
        }
        return self.success(target=seed, data=data)