import os
from core.module_base import BaseModule
from core.config import load_rules


class GeoIntModule(BaseModule):
    """
    v0.9 — GEOINT Görselleştirme Modülü.

    Komutlar:
      geoint map [file]          → Interaktif harita üret (Leaflet.js + OpenStreetMap)
      geoint graph [file]        → Interaktif ilişki grafiği üret (D3.js)
      geoint timeline <entity>   → Zaman çizelgesi export (POL hazır)
      geoint export [file]       → GeoJSON export
    """
    name = "geoint"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: geoint <map|graph|timeline|export> [file] [entity]")

        action = args[0].lower()
        filepath = None
        entity = None

        for arg in args[1:]:
            if arg.startswith("--"):
                continue
            if entity is None and action == "timeline":
                entity = arg
            elif filepath is None:
                filepath = arg

        rules = load_rules()
        geoint_cfg = rules.get("geoint", {})

        # --- MAP ---
        if action == "map":
            from core.geoint import GeoIntEngine
            engine = GeoIntEngine(self.context)
            if not filepath:
                filepath = geoint_cfg.get("default_map_path", "logs/geo_map.html")
            ok, msg, path = engine.export_map_html(filepath)
            if not ok:
                return self.error(msg)
            self.add_note(msg, severity="info")
            return self.success(target="map", data={
                "export_type": "map",
                "filepath": path,
                "message": msg,
            })

        # --- GRAPH ---
        elif action == "graph":
            from core.visualizer import GraphVisualizer
            viz = GraphVisualizer(self.context)
            if not filepath:
                filepath = geoint_cfg.get("default_graph_path", "logs/graph_viz.html")
            ok, msg, path = viz.export_graph_html(filepath)
            if not ok:
                return self.error(msg)
            self.add_note(msg, severity="info")
            return self.success(target="graph", data={
                "export_type": "graph",
                "filepath": path,
                "message": msg,
            })

        # --- TIMELINE ---
        elif action == "timeline":
            if not entity:
                return self.error("usage: geoint timeline <entity> [file]")
            from core.db import save_timeline
            if not filepath:
                filepath = f"{geoint_cfg.get('default_timeline_path', 'logs/timeline')}_{entity.replace(':', '_')}.json"
            ok, msg, data = save_timeline(self.context, entity, filepath)
            if not ok:
                return self.error(msg)
            self.add_note(msg, severity="info")
            return self.success(target=entity, data={
                "export_type": "timeline",
                "filepath": filepath,
                "message": msg,
                "event_count": len(data.get("timeline", [])),
            })

        # --- EXPORT (GeoJSON) ---
        elif action == "export":
            from core.db import save_geoint
            if not filepath:
                filepath = geoint_cfg.get("default_geojson_path", "logs/geoint.geojson")
            ok, msg, data = save_geoint(self.context, filepath)
            if not ok:
                return self.error(msg)
            self.add_note(msg, severity="info")
            return self.success(target="geojson", data={
                "export_type": "geojson",
                "filepath": filepath,
                "message": msg,
                "feature_count": len(data.get("features", [])),
            })

        return self.error(f"Unknown geoint action: {action}. Use: map, graph, timeline, export")