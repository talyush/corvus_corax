import os
from core.module_base import BaseModule
from core.nexus import NexusEngine
from core.exporter import NexusExporter

class NexusModule(BaseModule):
    """
    Corvus Corax v0.7 CLI Nexus Modülü.
    Merkezi zekadaki toplanmış verileri ilişkilendirir, risk puanlarını hesaplar
    ve HTML/JSON formatında dışa aktarır.
    """
    name = "nexus"

    # Varsayılan export dosya yolları
    DEFAULT_HTML_PATH = os.path.join("logs", "nexus_report.html")
    DEFAULT_JSON_PATH = os.path.join("logs", "nexus_neo4j.json")
    DEFAULT_GRAPH_PATH = os.path.join("logs", "nexus_graph.json")

    def execute(self):
        args = self.target or []

        if not self.context:
            return self.error("ContextManager is not initialized.", target="context")

        # Komut yönlendirme
        if not args or args[0].lower() in ("analyze", ""):
            # Check for --verbose flag
            verbose = "--verbose" in args or "-v" in args
            return self._run_analyze(verbose=verbose)

        if args[0].lower() == "export":
            if len(args) < 2:
                return self.error("Usage: nexus export [html|json|graph] [filepath]", target="context")

            export_type = args[1].lower()
            filepath = args[2] if len(args) > 2 else None

            if export_type == "html":
                return self._run_export_html(filepath)
            elif export_type == "json":
                return self._run_export_json(filepath)
            elif export_type == "graph":
                return self._run_export_graph(filepath)
            else:
                return self.error(f"Unknown export format: '{export_type}'. Use: html | json | graph", target="context")

        return self.error("Usage: nexus [analyze] [--verbose] | nexus export [html|json|graph] [filepath]", target="context")

    def _run_analyze(self, verbose=False):
        """Nexus Korelasyon Motoru'nu çalıştırır ve terminale özet raporu basar."""
        inv = self.begin_investigation(
            "Synthesize cross-domain intelligence graph & compute threat correlation rules",
            ["GRAPH INGESTION", "RULE CORRELATION & THREAT INFERENCE", "ADMIRALTY RATING SYNTHESIS"]
        )

        report = None
        try:
            with inv.phase(0):
                self.status_step("Ingesting nodes, edges & notes from ContextManager graph")

            with inv.phase(1):
                def run_engine():
                    nonlocal report
                    self.logger.info("Executing Nexus Correlation Engine...")
                    engine = NexusEngine(self.context)
                    report = engine.generate_report()

                self.status_step("Executing 11 threat correlation rules & pivot algorithms", work=run_engine)

            with inv.phase(2):
                self.status_step("Synthesizing Admiralty System credibility ratings & threat findings")
                # Yüksek seviyeli bulguları modül notu olarak kaydet
                for finding in report.get("threat_findings", []):
                    self.add_note(
                        text=f"Tehdit Tespiti ({finding.get('type')}): {finding.get('description')}",
                        severity="high" if "exposure" in finding.get("type", "").lower() else "medium",
                        confidence=finding.get("confidence", 1.0)
                    )
                    self.analyst_log(f"Threat finding [{finding.get('type')}]: {finding.get('description')}")

            self.logger.info("Nexus Correlation execution completed successfully.")
            report["verbose"] = verbose
            return self.success(target="context", data=report)

        except Exception as e:
            self.logger.error(f"Nexus analyze error: {e}")
            return self.error(f"Nexus analyze failed: {e}", target="context")

    def _run_export_html(self, filepath=None):
        """Nexus verilerini interaktif HTML dossier olarak dışa aktarır."""
        filepath = filepath or self.DEFAULT_HTML_PATH
        try:
            self.logger.info(f"Generating HTML dossier: {filepath}")
            engine = NexusEngine(self.context)
            report = engine.generate_report()
            exporter = NexusExporter(self.context, report_data=report)
            saved_path = exporter.export_html(filepath)

            self.add_note(
                text=f"HTML dossier successfully exported to: {saved_path}",
                severity="info"
            )
            self.logger.info(f"HTML export completed: {saved_path}")
            return self.success(
                target="context",
                data={
                    "export_type": "html",
                    "filepath": saved_path,
                    "entities": report.get("stats", {}).get("total_entities", 0),
                    "relations": report.get("stats", {}).get("total_raw_relations", 0),
                    "derived_relations": report.get("stats", {}).get("total_derived_relations", 0),
                }
            )
        except Exception as e:
            self.logger.error(f"HTML export error: {e}")
            return self.error(f"HTML export failed: {e}", target=filepath)

    def _run_export_json(self, filepath=None):
        """Nexus verilerini Neo4j uyumlu JSON şeması olarak dışa aktarır."""
        filepath = filepath or self.DEFAULT_JSON_PATH
        try:
            self.logger.info(f"Generating Neo4j JSON export: {filepath}")
            engine = NexusEngine(self.context)
            report = engine.generate_report()
            exporter = NexusExporter(self.context, report_data=report)
            neo4j_data = exporter.generate_neo4j_data()
            saved_path = exporter.export_neo4j_json(filepath)

            self.add_note(
                text=f"Neo4j JSON schema exported to: {saved_path}",
                severity="info"
            )
            self.logger.info(f"JSON export completed: {saved_path}")
            return self.success(
                target="context",
                data={
                    "export_type": "neo4j_json",
                    "filepath": saved_path,
                    "nodes": len(neo4j_data.get("nodes", [])),
                    "relationships": len(neo4j_data.get("relationships", [])),
                }
            )
        except Exception as e:
            self.logger.error(f"JSON export error: {e}")
            return self.error(f"JSON export failed: {e}", target=filepath)

    def _run_export_graph(self, filepath=None):
        """Nexus verilerini generic graph format (AI/ML ready) olarak dışa aktarır."""
        filepath = filepath or self.DEFAULT_GRAPH_PATH
        try:
            self.logger.info(f"Generating generic graph JSON export: {filepath}")
            engine = NexusEngine(self.context)
            report = engine.generate_report()
            exporter = NexusExporter(self.context, report_data=report)
            graph_data = exporter.generate_graph_data()
            saved_path = exporter.export_graph_json(filepath)

            self.add_note(
                text=f"Generic graph JSON exported to: {saved_path}",
                severity="info"
            )
            self.logger.info(f"Graph export completed: {saved_path}")
            return self.success(
                target="context",
                data={
                    "export_type": "graph_json",
                    "filepath": saved_path,
                    "nodes": len(graph_data.get("nodes", [])),
                    "edges": len(graph_data.get("edges", [])),
                    "format": graph_data.get("metadata", {}).get("format", "corvus_graph_v1")
                }
            )
        except Exception as e:
            self.logger.error(f"Graph export error: {e}")
            return self.error(f"Graph export failed: {e}", target=filepath)
