"""Corvus Corax v0.9 — D3.js Interaktif İlişki Grafiği Motoru.

exporter.generate_graph_data() çıktısını kullanarak D3.js force-directed graph
üretir. Node'lar entity türüne göre renkli, edge'ler ilişki türüne göre etiketli.
Sürükleme, zoom, hover tooltip, arama ve detay paneli destekler.
"""
import os
import json
from datetime import datetime, timezone

from core.config import load_rules


class GraphVisualizer:
    """D3.js force-directed graph görselleştirici."""

    def __init__(self, context_manager, graph_data=None):
        self.context_manager = context_manager
        self.rules = load_rules()
        self.node_colors = self.rules.get("node_colors", {})
        self.geoint_cfg = self.rules.get("geoint", {})

        # Graph verisi sağlanmadıysa exporter'dan üret
        if graph_data is None:
            from core.exporter import NexusExporter
            exporter = NexusExporter(context_manager)
            self.graph_data = exporter.generate_graph_data()
        else:
            self.graph_data = graph_data

    def _generate_html(self, offline=False):
        """
        D3.js force-directed graph HTML üretir.
        """
        # CDN veya offline mod
        if offline:
            d3_js = ""
            d3_init = "// Offline mode: D3 CDN yok — basit liste görünümü"
        else:
            d3_js = '<script src="https://d3js.org/d3.v7.min.js"></script>'
            d3_init = ""

        # Graph verisini JSON'a çevir
        nodes_json = json.dumps(self.graph_data.get("nodes", []), ensure_ascii=False)
        edges_json = json.dumps(self.graph_data.get("edges", []), ensure_ascii=False)
        node_colors_json = json.dumps(self.node_colors, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Corvus Corax — Intelligence Graph</title>
    <style>
        body {{ margin: 0; font-family: 'Segoe UI', sans-serif; background: #0d0e15; color: #e2e8f0; overflow: hidden; }}
        #graph {{ width: 100vw; height: 100vh; }}
        .header {{
            position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: rgba(13,14,21,0.9); padding: 8px 20px;
            border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
            font-size: 14px; font-weight: 600; letter-spacing: 1px;
        }}
        .header span {{ color: #a855f7; }}
        .search-box {{
            position: absolute; top: 60px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: rgba(13,14,21,0.9); padding: 8px 12px;
            border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
            display: flex; gap: 8px; align-items: center;
        }}
        .search-box input {{
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
            color: #e2e8f0; padding: 6px 10px; border-radius: 4px; outline: none;
            font-size: 12px; width: 200px;
        }}
        .search-box input:focus {{ border-color: #a855f7; }}
        .legend {{
            position: absolute; bottom: 20px; left: 20px; z-index: 1000;
            background: rgba(13,14,21,0.9); padding: 12px; border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1); font-size: 12px;
            max-height: 60vh; overflow-y: auto;
        }}
        .legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .detail-panel {{
            position: absolute; top: 60px; right: 20px; z-index: 1000;
            background: rgba(13,14,21,0.95); padding: 16px; border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1); font-size: 12px;
            width: 280px; display: none; max-height: 70vh; overflow-y: auto;
        }}
        .detail-panel h3 {{ margin: 0 0 8px 0; color: #a855f7; }}
        .detail-panel p {{ margin: 4px 0; }}
        .detail-panel .close {{ position: absolute; top: 8px; right: 12px; cursor: pointer; color: #94a3b8; }}
        .detail-panel .close:hover {{ color: #ef4444; }}
        .node-label {{ font-size: 10px; fill: #94a3b8; pointer-events: none; }}
        .edge-label {{ font-size: 8px; fill: #64748b; pointer-events: none; }}
        .tooltip {{
            position: absolute; background: rgba(13,14,21,0.95); color: #e2e8f0;
            padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);
            font-size: 11px; pointer-events: none; z-index: 2000; display: none;
        }}
    </style>
</head>
<body>
    <div class="header">CORVUS CORAX <span>INTELLIGENCE GRAPH</span> — Entity Relationship Map</div>
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search entities..." oninput="filterNodes(this.value)">
    </div>
    <div class="detail-panel" id="detailPanel">
        <span class="close" onclick="closeDetail()">✕</span>
        <h3 id="detailTitle"></h3>
        <div id="detailBody"></div>
    </div>
    <div class="legend" id="legend"></div>
    <div class="tooltip" id="tooltip"></div>
    <div id="graph"></div>
    {d3_js}
    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        const nodeColors = {node_colors_json};

        // Legend oluştur
        const legend = document.getElementById('legend');
        const types = [...new Set(nodes.map(n => n.type))];
        types.forEach(t => {{
            const color = nodeColors[t] || nodeColors['default'] || '#64748b';
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-dot" style="background:${{color}};"></div> ${{t}} (${{nodes.filter(n => n.type === t).length}})`;
            legend.appendChild(item);
        }});

        // SVG boyutları
        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Zoom
        svg.call(d3.zoom()
            .scaleExtent([0.1, 5])
            .on('zoom', (event) => g.attr('transform', event.transform)));

        // Force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges).id(d => d.id).distance(80))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Edge'ler
        const link = g.append('g')
            .selectAll('line')
            .data(edges)
            .enter().append('line')
            .attr('stroke', '#64748b')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 1);

        // Edge etiketleri
        const linkLabel = g.append('g')
            .selectAll('text')
            .data(edges)
            .enter().append('text')
            .attr('class', 'edge-label')
            .text(d => d.relation);

        // Node'lar
        const node = g.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', d => {{
                const risk = d.properties && d.properties.risk_score || 0;
                return 8 + (risk / 10);
            }})
            .attr('fill', d => nodeColors[d.type] || nodeColors['default'] || '#64748b')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5)
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        // Node etiketleri
        const nodeLabel = g.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .text(d => d.value)
            .attr('dx', 12)
            .attr('dy', 4);

        // Tooltip
        const tooltip = d3.select('#tooltip');

        node.on('mouseover', (event, d) => {{
            tooltip.style('display', 'block')
                .html(`<b>${{d.value}}</b><br>Type: ${{d.type}}<br>Risk: ${{d.properties && d.properties.risk_score || 0}}/100`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY + 10) + 'px');
        }}).on('mouseout', () => tooltip.style('display', 'none'));

        // Tıklayınca detay paneli
        node.on('click', (event, d) => {{
            const panel = document.getElementById('detailPanel');
            document.getElementById('detailTitle').textContent = `${{d.type}}: ${{d.value}}`;
            let body = '';
            if (d.properties) {{
                Object.entries(d.properties).forEach(([k, v]) => {{
                    if (v && typeof v !== 'object') {{
                        body += `<p><b>${{k}}:</b> ${{v}}</p>`;
                    }} else if (Array.isArray(v) && v.length) {{
                        body += `<p><b>${{k}}:</b> ${{v.join(', ')}}</p>`;
                    }}
                }});
            }}
            // İlişkileri göster
            const rels = edges.filter(e => e.source.id === d.id || e.target.id === d.id);
            if (rels.length) {{
                body += '<p><b>Relationships:</b></p>';
                rels.slice(0, 10).forEach(r => {{
                    const other = r.source.id === d.id ? r.target : r.source;
                    body += `<p>↳ ${{r.relation}} → ${{other.value}}</p>`;
                }});
            }}
            document.getElementById('detailBody').innerHTML = body || '<p>No details available.</p>';
            panel.style.display = 'block';
        }});

        // Arama
        window.filterNodes = function(query) {{
            const q = query.toLowerCase();
            node.attr('opacity', d => !q || d.value.toLowerCase().includes(q) ? 1 : 0.1);
            nodeLabel.attr('opacity', d => !q || d.value.toLowerCase().includes(q) ? 1 : 0.1);
            link.attr('opacity', d => {{
                if (!q) return 0.6;
                const src = d.source.value.toLowerCase();
                const tgt = d.target.value.toLowerCase();
                return (src.includes(q) || tgt.includes(q)) ? 1 : 0.05;
            }});
        }};

        window.closeDetail = function() {{
            document.getElementById('detailPanel').style.display = 'none';
        }};

        // Simulation tick
        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkLabel.attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2 - 4);

            node.attr('cx', d => d.x)
                .attr('cy', d => d.y);

            nodeLabel.attr('x', d => d.x)
                .attr('y', d => d.y);
        }});

        // Drag fonksiyonları
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
"""
        return html

    def export_graph_html(self, filepath=None, offline=False):
        """
        Interaktif grafiği HTML dosyası olarak diske yazar.
        Returns: (bool, message, filepath)
        """
        if not filepath:
            filepath = self.geoint_cfg.get("default_graph_path", "logs/graph_viz.html")

        html = self._generate_html(offline=offline)

        try:
            dir_name = os.path.dirname(filepath) if filepath else ""
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            node_count = len(self.graph_data.get("nodes", []))
            edge_count = len(self.graph_data.get("edges", []))
            return True, f"Graph exported to {filepath} ({node_count} nodes, {edge_count} edges)", filepath
        except Exception as e:
            return False, f"Failed to export graph: {e}", filepath