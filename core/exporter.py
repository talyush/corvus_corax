import json
import os
from datetime import datetime

class NexusExporter:
    """
    Corvus Corax v0.7 Nexus Veri Ihracat ve Raporlama Motoru.
    Bağlam graflarını interaktif HTML panellerine ve Neo4j uyumlu grafik şemalarına dönüştürür.
    """
    def __init__(self, context_manager, report_data=None):
        self.context_manager = context_manager
        self.report_data = report_data
        
        # Rapor verileri sağlanmadıysa hesapla
        if not self.report_data:
            from core.nexus import NexusEngine
            engine = NexusEngine(self.context_manager)
            self.report_data = engine.generate_report()

    def generate_neo4j_data(self):
        """
        Merkezi bağlam graflarını Neo4j import formatına uygun (nodes ve relationships) şemaya dönüştürür.
        """
        nodes = {}
        relationships = []
        
        # Risk profillerini kolay erişim için indeksle
        profiles = {p["value"]: p for p in self.report_data.get("risk_profiles", [])}
        
        # 1. Düğümleri (Nodes) Çıkar: IP'ler ve Domainler
        ips = self.context_manager.data.get("ips", {})
        for ip, ip_data in ips.items():
            node_id = f"ip:{ip}"
            profile = profiles.get(ip, {})
            nodes[node_id] = {
                "id": node_id,
                "label": "IP",
                "properties": {
                    "value": ip,
                    "risk_score": profile.get("score", 0),
                    "risk_level": profile.get("level", "Low"),
                    "hostname": ip_data.get("hostname") or ""
                }
            }
            
        domains = self.context_manager.data.get("domains", {})
        for dom, dom_data in domains.items():
            node_id = f"domain:{dom}"
            profile = profiles.get(dom, {})
            nodes[node_id] = {
                "id": node_id,
                "label": "Domain",
                "properties": {
                    "value": dom,
                    "risk_score": profile.get("score", 0),
                    "risk_level": profile.get("level", "Low")
                }
            }

        # 2. İlişkilerden Diğer Düğüm Tiplerini (Port, Location, Server, Tech vb.) ve Bağları Çıkar
        all_rels = (self.context_manager.data.get("relations", []) + 
                    self.context_manager.data.get("derived_relations", []))
        
        rel_counter = 0
        for rel in all_rels:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation_type = rel.get("relation", "related_to")
            
            src_type = src.get("type", "unknown")
            src_val = src.get("value")
            dst_type = dst.get("type", "unknown")
            dst_val = dst.get("value")
            
            if not src_val or not dst_val:
                continue
                
            src_node_id = f"{src_type}:{src_val}"
            dst_node_id = f"{dst_type}:{dst_val}"
            
            # Kaynak düğüm ekli değilse ekle
            if src_node_id not in nodes:
                nodes[src_node_id] = {
                    "id": src_node_id,
                    "label": src_type.upper(),
                    "properties": {"value": src_val}
                }
                
            # Hedef düğüm ekli değilse ekle
            if dst_node_id not in nodes:
                nodes[dst_node_id] = {
                    "id": dst_node_id,
                    "label": dst_type.upper(),
                    "properties": {"value": dst_val}
                }
                
            # İlişkiyi ekle
            rel_counter += 1
            relationships.append({
                "id": f"rel_{rel_counter}",
                "type": relation_type.upper(),
                "startNode": src_node_id,
                "endNode": dst_node_id,
                "properties": {
                    "evidence": rel.get("evidence") or "",
                    "confidence": float(rel.get("confidence", 1.0)),
                    "timestamp": rel.get("timestamp") or ""
                }
            })
            
        return {
            "nodes": list(nodes.values()),
            "relationships": relationships
        }

    def generate_graph_data(self):
        """
        Generic graph format suitable for AI/ML pipelines and visualization.
        More flexible than Neo4j format, includes Admiralty intelligence.
        """
        nodes = {}
        edges = []
        
        # Risk profillerini indeksle
        profiles = {p["value"]: p for p in self.report_data.get("risk_profiles", [])}
        
        # 1. IP Nodes with full intelligence
        ips = self.context_manager.data.get("ips", {})
        asn_intel = self.context_manager.data.get("asn_intel", {})
        
        for ip, ip_data in ips.items():
            node_id = f"ip:{ip}"
            profile = profiles.get(ip, {})
            asn_data = asn_intel.get(ip, {})
            
            node = {
                "id": node_id,
                "type": "ip",
                "value": ip,
                "properties": {
                    "hostname": ip_data.get("hostname") or "",
                    "ports": [p.get("port") for p in ip_data.get("ports", [])],
                    "geo": ip_data.get("geo", {}),
                    "risk_score": profile.get("score", 0),
                    "risk_level": profile.get("level", "Low"),
                    "admiralty_rating": profile.get("admiralty_rating", "N/A"),
                    "evidence_count": profile.get("evidence_count", 0),
                    "asn": asn_data.get("asn") or "",
                    "organization": asn_data.get("organization") or "",
                    "cidr": asn_data.get("cidr") or "",
                    "country": asn_data.get("country") or ""
                }
            }
            nodes[node_id] = node
        
        # 2. Domain Nodes with tech intelligence
        domains = self.context_manager.data.get("domains", {})
        tech_intel = self.context_manager.data.get("tech_intel", {})
        
        for dom, dom_data in domains.items():
            node_id = f"domain:{dom}"
            profile = profiles.get(dom, {})
            tech_data = tech_intel.get(dom, {})
            
            node = {
                "id": node_id,
                "type": "domain",
                "value": dom,
                "properties": {
                    "ips": dom_data.get("ips", []),
                    "risk_score": profile.get("score", 0),
                    "risk_level": profile.get("level", "Low"),
                    "admiralty_rating": profile.get("admiralty_rating", "N/A"),
                    "evidence_count": profile.get("evidence_count", 0),
                    "server": tech_data.get("server") or "",
                    "runtime": tech_data.get("runtime") or "",
                    "cms": [cms.get("name") for cms in tech_data.get("cms", [])],
                    "frameworks": [fw.get("name") for fw in tech_data.get("frameworks", [])],
                    "waf_cdn": [waf.get("name") for waf in tech_data.get("waf_cdn", [])],
                    "stack_profile": tech_data.get("stack_profile") or ""
                }
            }
            nodes[node_id] = node

        # --- v0.9: Entity-agnostic node expansion ---
        # Merkezi entity registry'deki person, organization, phone, email,
        # social_profile, wallet, location gibi tüm varlıkları da node'lar olarak ekle.
        entity_registry = self.context_manager.data.get("entities", {})
        for key, ent in entity_registry.items():
            ent_type = ent.get("type")
            ent_val = ent.get("value")
            if not ent_type or not ent_val:
                continue
            node_id = f"{ent_type}:{ent_val}"
            # IP/domain zaten eklendi — atla
            if node_id in nodes:
                continue
            # Module-tipi geçici varlıkları atla
            if ent_type == "module":
                continue
            profile = profiles.get(ent_val, {})
            props = dict(ent.get("properties", {}))
            props.update({
                "risk_score": profile.get("score", 0),
                "risk_level": profile.get("level", "Low"),
                "admiralty_rating": profile.get("admiralty_rating", "N/A"),
                "evidence_count": profile.get("evidence_count", 0),
            })
            nodes[node_id] = {
                "id": node_id,
                "type": ent_type,
                "value": ent_val,
                "properties": props
            }
        
        # 3. Extract all relationships with full metadata
        all_rels = (self.context_manager.data.get("relations", []) + 
                    self.context_manager.data.get("derived_relations", []))
        
        edge_counter = 0
        for rel in all_rels:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation_type = rel.get("relation", "related_to")
            
            src_type = src.get("type", "unknown")
            src_val = src.get("value")
            dst_type = dst.get("type", "unknown")
            dst_val = dst.get("value")
            
            if not src_val or not dst_val:
                continue
                
            src_node_id = f"{src_type}:{src_val}"
            dst_node_id = f"{dst_type}:{dst_val}"
            
            # Create source node if not exists
            if src_node_id not in nodes:
                nodes[src_node_id] = {
                    "id": src_node_id,
                    "type": src_type,
                    "value": src_val,
                    "properties": {}
                }
            
            # Create destination node if not exists
            if dst_node_id not in nodes:
                nodes[dst_node_id] = {
                    "id": dst_node_id,
                    "type": dst_type,
                    "value": dst_val,
                    "properties": {}
                }
            
            # Add edge with full metadata
            edge_counter += 1
            edges.append({
                "id": f"edge_{edge_counter}",
                "source": src_node_id,
                "target": dst_node_id,
                "relation": relation_type,
                "properties": {
                    "evidence": rel.get("evidence") or "",
                    "confidence": float(rel.get("confidence", 1.0)),
                    "timestamp": rel.get("timestamp") or "",
                    "derived": rel in self.context_manager.data.get("derived_relations", [])
                }
            })
        
        # 4. Add metadata for AI/ML context
        graph_metadata = {
            "version": "0.9",
            "format": "corvus_graph_v2",
            "generated_at": datetime.now().isoformat(),
            "stats": self.report_data.get("stats", {}),
            "risk_distribution": self.report_data.get("risk_distribution", {}),
            "threat_findings": self.report_data.get("threat_findings", []),
            "temporal_events": len(self.context_manager.data.get("events", []))
        }
        
        return {
            "metadata": graph_metadata,
            "nodes": list(nodes.values()),
            "edges": edges
        }

    def export_neo4j_json(self, filepath):
        """Neo4j grafik şemasını JSON dosyası olarak diske yazar."""
        # Dizin yoksa oluştur
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        neo4j_data = self.generate_neo4j_data()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(neo4j_data, f, indent=4, ensure_ascii=False)
        return filepath

    def export_graph_json(self, filepath):
        """Generic graph format for AI/ML pipelines and visualization."""
        # Dizin yoksa oluştur
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        graph_data = self.generate_graph_data()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=4, ensure_ascii=False)
        return filepath

    def export_html(self, filepath):
        """Interaktif HTML Raporunu (Dossier) oluşturup diske kaydeder."""
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        stats = self.report_data.get("stats", {})
        dist = self.report_data.get("risk_distribution", {})
        profiles = sorted(self.report_data.get("risk_profiles", []), key=lambda x: x.get("score", 0), reverse=True)
        threats = self.report_data.get("threat_findings", [])
        
        raw_relations = self.context_manager.data.get("relations", [])
        derived_relations = self.context_manager.data.get("derived_relations", [])
        
        # Ağ Sağlığı Puanı Hesaplama
        avg_score = 0
        if profiles:
            avg_score = sum(p.get("score", 0) for p in profiles) / len(profiles)
        health_score = int(100 - avg_score)
        
        # Sağlık rengi tayini
        health_color = "#10b981" # Green
        if health_score < 50:
            health_color = "#ef4444" # Red
        elif health_score < 75:
            health_color = "#f59e0b" # Yellow
            
        # HTML Şablon Oluşturma
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Corvus Corax - Nexus Intelligence Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Mono&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0d0e15;
            --card-bg: rgba(23, 24, 33, 0.85);
            --border-color: rgba(255, 255, 255, 0.05);
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --purple: #a855f7;
            --cyan: #06b6d4;
            --red: #ef4444;
            --yellow: #f59e0b;
            --green: #10b981;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            padding: 2rem;
        }}
        
        /* Layout */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .logo h1 {{
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: 2px;
            background: linear-gradient(to right, var(--purple), var(--cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .logo span {{
            font-family: 'Space Mono', monospace;
            font-size: 0.8rem;
            color: var(--cyan);
            border: 1px solid var(--cyan);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .meta-info {{
            text-align: right;
            font-family: 'Space Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Stats Panel */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            backdrop-filter: blur(10px);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(168, 85, 247, 0.2);
        }}
        
        .stat-card h3 {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        .stat-card .value {{
            font-size: 2.2rem;
            font-weight: 800;
            font-family: 'Space Mono', monospace;
        }}
        
        .stat-card.health-card .value {{
            color: {health_color};
            text-shadow: 0 0 10px rgba({health_color == '#ef4444' and '239,68,68' or health_color == '#f59e0b' and '245,158,11' or '16,185,129'}, 0.3);
        }}
        
        /* Navigation Tabs */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1px;
        }}
        
        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-secondary);
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }}
        
        .tab-btn:hover {{
            color: var(--text-primary);
        }}
        
        .tab-btn.active {{
            color: var(--purple);
            border-bottom-color: var(--purple);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.4s ease-out;
        }}
        
        /* Alerts & Threat Cards */
        .alert-box {{
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .alert-box.outdated {{
            background: rgba(245, 158, 11, 0.05);
            border: 1px solid rgba(245, 158, 11, 0.15);
        }}
        
        .alert-title {{
            font-weight: 600;
            font-size: 1.05rem;
            color: var(--text-primary);
            margin-bottom: 2px;
        }}
        
        .alert-desc {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        
        .badge {{
            font-family: 'Space Mono', monospace;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .badge.critical {{ background-color: rgba(239, 68, 68, 0.15); color: var(--red); border: 1px solid var(--red); }}
        .badge.high {{ background-color: rgba(239, 68, 68, 0.15); color: var(--red); border: 1px solid var(--red); }}
        .badge.medium {{ background-color: rgba(245, 158, 11, 0.15); color: var(--yellow); border: 1px solid var(--yellow); }}
        .badge.low {{ background-color: rgba(16, 185, 129, 0.15); color: var(--green); border: 1px solid var(--green); }}
        .badge.ip {{ background-color: rgba(6, 182, 212, 0.15); color: var(--cyan); border: 1px solid var(--cyan); }}
        .badge.domain {{ background-color: rgba(168, 85, 247, 0.15); color: var(--purple); border: 1px solid var(--purple); }}

        /* Risk Cards & Accordion */
        .entity-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        }}
        
        .entity-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}
        
        .entity-title {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .entity-name {{
            font-size: 1.25rem;
            font-weight: 600;
        }}
        
        .risk-gauge {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .progress-bar-bg {{
            width: 150px;
            height: 8px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-bar-fill {{
            height: 100%;
            border-radius: 4px;
        }}
        
        .arrow-icon {{
            font-size: 1.2rem;
            transition: transform 0.2s;
            color: var(--text-secondary);
        }}
        
        .entity-card.collapsed .arrow-icon {{
            transform: rotate(-90deg);
        }}
        
        .evidence-section {{
            margin-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
            animation: slideDown 0.3s ease-out;
        }}
        
        .entity-card.collapsed .evidence-section {{
            display: none;
        }}
        
        .evidence-list {{
            list-style-type: none;
            padding-left: 0.5rem;
        }}
        
        .evidence-item {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 0.5rem;
            font-size: 0.95rem;
            color: var(--text-secondary);
        }}
        
        .evidence-item::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: var(--purple);
            font-weight: bold;
            font-size: 1.2rem;
            top: -2px;
        }}
        
        /* Tables */
        .search-container {{
            margin-bottom: 1rem;
            display: flex;
            gap: 10px;
        }}
        
        .search-input {{
            flex: 1;
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.6rem 1rem;
            border-radius: 8px;
            outline: none;
            font-family: inherit;
        }}
        
        .search-input:focus {{
            border-color: var(--purple);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            backdrop-filter: blur(10px);
            margin-bottom: 2rem;
        }}
        
        th, td {{
            padding: 0.9rem 1.2rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        th {{
            background-color: rgba(255, 255, 255, 0.02);
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.01);
        }}
        
        .rel-type {{
            font-family: 'Space Mono', monospace;
            font-size: 0.8rem;
            background-color: rgba(168, 85, 247, 0.08);
            color: var(--purple);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(168, 85, 247, 0.15);
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(5px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes slideDown {{
            from {{ opacity: 0; max-height: 0; }}
            to {{ opacity: 1; max-height: 500px; }}
        }}
        
        /* Grid layouts */
        .tab-columns {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
        }}
        
        .panel {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .panel h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.2rem;
            border-left: 3px solid var(--cyan);
            padding-left: 10px;
        }}

        .event-log {{
            font-family: 'Space Mono', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            max-height: 350px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        
        .event-item {{
            margin-bottom: 6px;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.02);
            padding-bottom: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <h1>CORVUS CORAX</h1>
                <span>v0.9</span>
            </div>
            <div class="meta-info">
                <p>NEXUS INTELLIGENCE REPORT</p>
                <p style="font-size: 0.75rem; margin-top: 4px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </header>
        
        <!-- Stats Widgets -->
        <div class="stats-grid">
            <div class="stat-card health-card">
                <h3>Network Health Score</h3>
                <div class="value">{health_score}%</div>
            </div>
            <div class="stat-card">
                <h3>Discovered Entities</h3>
                <div class="value">{stats.get('total_entities', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Raw Graph Relations</h3>
                <div class="value">{stats.get('total_raw_relations', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Nexus Inferred Links</h3>
                <div class="value" style="color: var(--purple);">{stats.get('total_derived_relations', 0)}</div>
            </div>
        </div>
        
        <!-- Navigation Menu -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('exec')">Executive Summary</button>
            <button class="tab-btn" onclick="switchTab('risk')">Risk Profiles</button>
            <button class="tab-btn" onclick="switchTab('relations')">Graph Relations Explorer</button>
        </div>
        
        <!-- EXECUTIVE SUMMARY TAB -->
        <div id="exec-tab" class="tab-content active">
            <div class="tab-columns">
                <div>
                    <!-- Threat List -->
                    <div class="panel">
                        <h2>Threat findings & Critical Alerts</h2>
                        """
        
        if not threats:
            html_content += "<p style='color: var(--text-secondary);'>No high priority threat exposures detected in the current scope.</p>"
        else:
            for threat in threats:
                t_type = threat.get("type", "Security Finding")
                t_class = "outdated" if "outdated" in t_type.lower() else "exposure"
                html_content += f"""
                        <div class="alert-box {t_class}">
                            <div>
                                <div class="alert-title">[{t_type}] {threat.get('entity')}</div>
                                <div class="alert-desc">{threat.get('description')}</div>
                            </div>
                            <span class="badge critical">Conf: {threat.get('confidence', 1.0)}</span>
                        </div>
                """
        
        # Geolocation info summary card
        html_content += """
                    </div>
                </div>
                <div>
                    <!-- Event logs -->
                    <div class="panel">
                        <h2>Audit Event Log</h2>
                        <div class="event-log">
        """
        recent_events = self.context_manager.get_clean_data().get("meta", {}).get("recent_events", [])
        if not recent_events:
            html_content += "<p>No active auditing events logged.</p>"
        else:
            for ev in reversed(recent_events):
                html_content += f'<div class="event-item">&gt; {ev}</div>'
                
        html_content += """
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- RISK PROFILES TAB -->
        <div id="risk-tab" class="tab-content">
            <div class="panel">
                <h2>Asset Risk Profiles & Critical Vulnerabilities</h2>
        """
        
        if not profiles:
            html_content += "<p style='color: var(--text-secondary);'>No target assets discovered in the active memory context.</p>"
        else:
            for prof in profiles:
                val = prof.get("value")
                p_type = prof.get("type")
                score = prof.get("score")
                level = prof.get("level")
                ev = prof.get("evidence", [])
                
                # Bar progress bar color
                p_color = "var(--green)"
                if level == "Critical": p_color = "var(--red)"
                elif level == "High": p_color = "var(--red)"
                elif level == "Medium": p_color = "var(--yellow)"
                
                html_content += f"""
                <div class="entity-card collapsed" id="card-{val.replace('.', '_')}">
                    <div class="entity-header" onclick="toggleCard('{val.replace('.', '_')}')">
                        <div class="entity-title">
                            <span class="badge {p_type.lower()}">{p_type}</span>
                            <span class="entity-name">{val}</span>
                        </div>
                        <div class="risk-gauge">
                            <span class="badge {level.lower()}">{level} ({score})</span>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: {score}%; background-color: {p_color};"></div>
                            </div>
                            <span class="arrow-icon">&#9660;</span>
                        </div>
                    </div>
                    <div class="evidence-section">
                        <h4 style="margin-bottom: 0.5rem; font-size: 0.95rem; color: var(--text-primary);">Vulnerability Evidence Chain:</h4>
                        <ul class="evidence-list">
                """
                if not ev:
                    html_content += "<li class=\"evidence-item\" style=\"color: var(--text-secondary);\">No adverse security evidence detected.</li>"
                else:
                    for item in ev:
                        html_content += f'<li class="evidence-item">{item}</li>'
                        
                html_content += """
                        </ul>
                    </div>
                </div>
                """
                
        html_content += """
            </div>
        </div>
        
        <!-- RELATIONSHIPS EXPLORER TAB -->
        <div id="relations-tab" class="tab-content">
            <div class="panel">
                <h2>Recon Relationships Graph Explorer</h2>
                <div class="search-container">
                    <input type="text" id="relSearch" class="search-input" placeholder="Search relationships (e.g. resolves_to, has_open_port, domain name)..." onkeyup="filterRelations()">
                </div>
                <table id="relationsTable">
                    <thead>
                        <tr>
                            <th>Subject (Source)</th>
                            <th>Relation Type</th>
                            <th>Object (Destination)</th>
                            <th>Evidence</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Raw ve derived relationships listele
        def get_row_html(rel, origin):
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "related_to")
            evidence = rel.get("evidence") or "N/A"
            conf = rel.get("confidence", 1.0)
            
            src_str = f"({src.get('type', 'Unknown')}) {src.get('value', '')}"
            dst_str = f"({dst.get('type', 'Unknown')}) {dst.get('value', '')}"
            
            origin_badge = f'<span class="badge {origin == "derived" and "critical" or "ip"}" style="font-size: 0.65rem; padding: 1px 4px; margin-left: 5px;">{origin}</span>'
            
            return f"""
                        <tr>
                            <td>{src_str}</td>
                            <td><span class="rel-type">{relation.upper()}</span>{origin_badge}</td>
                            <td>{dst_str}</td>
                            <td style="color: var(--text-secondary); font-size: 0.9rem;">{evidence}</td>
                            <td><span class="badge low" style="padding: 1px 4px;">{conf}</span></td>
                        </tr>
            """
            
        for rel in raw_relations:
            html_content += get_row_html(rel, "raw")
        for rel in derived_relations:
            html_content += get_row_html(rel, "derived")
            
        if not raw_relations and not derived_relations:
            html_content += "<tr><td colspan='5' style='text-align: center; color: var(--text-secondary);'>No relations registered in current context graph.</td></tr>"
            
        html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.currentTarget.classList.add('active');
            document.getElementById(tabId + '-tab').classList.add('active');
        }
        
        function toggleCard(cardId) {
            const card = document.getElementById('card-' + cardId);
            card.classList.toggle('collapsed');
        }
        
        function filterRelations() {
            const input = document.getElementById('relSearch');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('relationsTable');
            const trs = table.getElementsByTagName('tr');
            
            for (let i = 1; i < trs.length; i++) {
                const tr = trs[i];
                const textContent = tr.innerText.toLowerCase();
                if (textContent.includes(filter)) {
                    tr.style.display = "";
                } else {
                    tr.style.display = "none";
                }
            }
        }
    </script>
</body>
</html>
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return filepath
