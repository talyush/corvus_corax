from core.module_base import BaseModule
from core.nexus import NexusEngine

class NexusModule(BaseModule):
    """
    Corvus Corax v0.6 CLI Nexus Modülü.
    Merkezi zekadaki toplanmış verileri ilişkilendirir ve risk puanlarını hesaplar.
    """
    name = "nexus"

    def execute(self):
        args = self.target or []
        
        # Sadece boş kullanımı veya 'analyze' komutunu destekle
        if args and args[0].lower() not in ("analyze",):
            return self.error("Usage: nexus [analyze]", target="context")

        if not self.context:
            return self.error("ContextManager is not initialized.", target="context")

        try:
            self.logger.info("Executing Nexus Correlation Engine...")
            engine = NexusEngine(self.context)
            report = engine.generate_report()

            # Nexus Engine'in ürettiği yüksek seviyeli bulguları modül notu olarak ekle
            # Böylece to_text çıktısında da görüntülenebilir hale gelecektir.
            for finding in report.get("threat_findings", []):
                self.add_note(
                    text=f"Tehdit Tespiti ({finding.get('type')}): {finding.get('description')}",
                    severity="high" if "exposure" in finding.get("type").lower() else "medium",
                    confidence=finding.get("confidence", 1.0)
                )

            self.logger.info("Nexus Correlation execution completed successfully.")
            return self.success(
                target="context",
                data=report
            )
        except Exception as e:
            self.logger.error(f"Nexus execution error: {e}")
            return self.error(f"Nexus execution failed: {e}", target="context")
