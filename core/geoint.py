"""Corvus Corax v0.9 — GEOINT Harita Motoru.

Context'teki tüm location varlıklarını toplar ve Leaflet.js + OpenStreetMap
ile interaktif HTML harita üretir. Person movement tracking, heatmap ve
katman kontrolü destekler.
"""
import os
import json
from datetime import datetime, timezone

from core.config import load_rules


class GeoIntEngine:
    """GEOINT harita motoru — context'teki konum verilerini görselleştirir."""

    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.rules = load_rules()
        self.geoint_cfg = self.rules.get("geoint", {})
        self.node_colors = self.rules.get("node_colors", {})

    def _collect_locations(self):
        """
        Context'teki tüm konum verilerini toplar.
        Returns: list of {lat, lon, label, type, entities, details}
        """
        locations = []
        ip_data = self.context_manager.data.get("ips", {})
        entities = self.context_manager.data.get("entities", {})

        # 1. IP'lerin geo bilgileri
        for ip, ipd in ip_data.items():
            geo = ipd.get("geo", {})
            lat = geo.get("latitude") or geo.get("lat")
            lon = geo.get("longitude") or geo.get("lon")
            if lat is None or lon is None:
                continue
            label = f"{geo.get('city', '')}, {geo.get('country', '')}".strip(", ")
            locations.append({
                "lat": float(lat),
                "lon": float(lon),
                "label": label or ip,
                "type": "ip",
                "entity": ip,
                "details": {
                    "isp": geo.get("isp") or geo.get("org") or "",
                    "hostname": ipd.get("hostname") or "",
                    "ports": [p.get("port") for p in ipd.get("ports", [])],
                    "country": geo.get("country", ""),
                    "city": geo.get("city", ""),
                }
            })

        # 2. Location entity'leri (geo verisi olanlar)
        for key, ent in entities.items():
            ent_type = ent.get("type")
            ent_val = ent.get("value")
            props = ent.get("properties", {})
            if ent_type == "location":
                lat = props.get("latitude") or props.get("lat")
                lon = props.get("longitude") or props.get("lon")
                if lat is None or lon is None:
                    continue
                locations.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "label": ent_val,
                    "type": "location",
                    "entity": ent_val,
                    "details": {
                        "ip": props.get("ip", ""),
                        "country": props.get("country", ""),
                        "city": props.get("city", ""),
                    }
                })

        return locations

    def _build_movement(self):
        """
        Person/entity hareket rotalarını temporal event store'dan çıkarır.
        Returns: list of {entity, points: [{lat, lon, time, label}]}
        """
        if not self.geoint_cfg.get("movement_tracking_enabled", True):
            return []

        events = self.context_manager.data.get("events", [])
        ip_data = self.context_manager.data.get("ips", {})

        # IP'lerin konumlarını zamanla eşleştir
        ip_locations = {}  # ip -> {lat, lon, label, time}
        for ip, ipd in ip_data.items():
            geo = ipd.get("geo", {})
            lat = geo.get("latitude") or geo.get("lat")
            lon = geo.get("longitude") or geo.get("lon")
            if lat is None or lon is None:
                continue
            ip_locations[ip] = {
                "lat": float(lat),
                "lon": float(lon),
                "label": f"{geo.get('city', '')}, {geo.get('country', '')}".strip(", "),
            }

        # Entity → IP ilişkilerini bul (relations'dan)
        relations = self.context_manager.data.get("relations", [])
        entity_ips = {}  # entity -> [ip, ...]
        for rel in relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            # person/domain → ip ilişkileri
            if dst.get("type") == "ip" and src.get("type") in ("person", "domain", "organization"):
                entity = f"{src.get('type')}:{src.get('value')}"
                entity_ips.setdefault(entity, []).append(dst.get("value"))

        # Movement rotaları
        movements = []
        for entity, ips in entity_ips.items():
            points = []
            for ip in ips:
                if ip in ip_locations:
                    loc = ip_locations[ip]
                    points.append({
                        "lat": loc["lat"],
                        "lon": loc["lon"],
                        "label": loc["label"],
                        "ip": ip,
                    })
            if len(points) >= 2:
                movements.append({
                    "entity": entity,
                    "points": points,
                })

        return movements

    def _generate_html(self, locations, movements, offline=False):
        """
        Leaflet.js + OpenStreetMap ile interaktif HTML harita üretir.
        """
        # CDN veya offline mod
        if offline:
            leaflet_css = ""
            leaflet_js = ""
            leaflet_init = "// Offline mode: Leaflet CDN yok — basit görünüm"
        else:
            leaflet_css = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />'
            leaflet_js = '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'

        # Marker verilerini JSON'a çevir
        markers_json = json.dumps(locations, ensure_ascii=False)
        movements_json = json.dumps(movements, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Corvus Corax — GEOINT Map</title>
    {leaflet_css}
    <style>
        body {{ margin: 0; font-family: 'Segoe UI', sans-serif; background: #0d0e15; color: #e2e8f0; }}
        #map {{ height: 100vh; width: 100%; }}
        .header {{
            position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
            z-index: 1000; background: rgba(13,14,21,0.9); padding: 8px 20px;
            border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
            font-size: 14px; font-weight: 600; letter-spacing: 1px;
        }}
        .header span {{ color: #06b6d4; }}
        .legend {{
            position: absolute; bottom: 20px; left: 20px; z-index: 1000;
            background: rgba(13,14,21,0.9); padding: 12px; border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.1); font-size: 12px;
        }}
        .legend-item {{ display: flex; align-items: center; margin: 4px 0; }}
        .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .popup-content {{ color: #0d0e15; font-size: 12px; }}
        .popup-content h4 {{ margin: 0 0 4px 0; }}
        .popup-content p {{ margin: 2px 0; }}
    </style>
</head>
<body>
    <div class="header">CORVUS CORAX <span>GEOINT</span> — Intelligence Map</div>
    <div id="map"></div>
    <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#10b981;"></div> IP</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div> Person</div>
        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6;"></div> Organization</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ec4899;"></div> Location</div>
        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;"></div> Movement Route</div>
    </div>
    {leaflet_js}
    <script>
        const markers = {markers_json};
        const movements = {movements_json};

        // Harita başlat
        const map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19,
        }}).addTo(map);

        // Marker renkleri
        const typeColors = {{
            'ip': '#10b981',
            'person': '#ef4444',
            'organization': '#3b82f6',
            'location': '#ec4899',
            'default': '#64748b'
        }};

        // Marker'ları ekle
        markers.forEach(m => {{
            const color = typeColors[m.type] || typeColors['default'];
            const icon = L.divIcon({{
                className: 'custom-div-icon',
                html: `<div style="background:${{color}};width:14px;height:14px;border-radius:50%;border:2px solid white;"></div>`,
                iconSize: [14, 14],
                iconAnchor: [7, 7],
            }});
            const popupContent = `
                <div class="popup-content">
                    <h4>${{m.label}}</h4>
                    <p><b>Type:</b> ${{m.type}}</p>
                    <p><b>Entity:</b> ${{m.entity}}</p>
                    ${{m.details.isp ? `<p><b>ISP:</b> ${{m.details.isp}}</p>` : ''}}
                    ${{m.details.hostname ? `<p><b>Hostname:</b> ${{m.details.hostname}}</p>` : ''}}
                    ${{m.details.ports && m.details.ports.length ? `<p><b>Ports:</b> ${{m.details.ports.join(', ')}}</p>` : ''}}
                    ${{m.details.country ? `<p><b>Country:</b> ${{m.details.country}}</p>` : ''}}
                    ${{m.details.city ? `<p><b>City:</b> ${{m.details.city}}</p>` : ''}}
                </div>`;
            L.marker([m.lat, m.lon], {{ icon }}).addTo(map).bindPopup(popupContent);
        }});

        // Hareket rotaları
        movements.forEach(mv => {{
            const points = mv.points.map(p => [p.lat, p.lon]);
            const polyline = L.polyline(points, {{
                color: '#f59e0b',
                weight: 3,
                opacity: 0.7,
                dashArray: '5, 5',
            }}).addTo(map);
            polyline.bindPopup(`<div class="popup-content"><h4>${{mv.entity}}</h4><p>Movement route (${{points.length}} locations)</p></div>`);
        }});

        // Heatmap (opsiyonel — basit yoğunluk göstergesi)
        const heatmapEnabled = {str(self.geoint_cfg.get("heatmap_enabled", True)).lower()};
        if (heatmapEnabled && markers.length > 0) {{
            // Basit heatmap: marker yoğunluğuna göre daireler
            const seen = {{}};
            markers.forEach(m => {{
                const key = m.lat.toFixed(1) + ',' + m.lon.toFixed(1);
                seen[key] = (seen[key] || 0) + 1;
            }});
            Object.entries(seen).forEach(([key, count]) => {{
                if (count >= 2) {{
                    const [lat, lon] = key.split(',').map(Number);
                    L.circle([lat, lon], {{
                        radius: 50000 * count,
                        color: '#f59e0b',
                        fillColor: '#f59e0b',
                        fillOpacity: 0.2,
                        weight: 1,
                    }}).addTo(map);
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        return html

    def export_map_html(self, filepath=None, offline=False):
        """
        Interaktif haritayı HTML dosyası olarak diske yazar.
        Returns: (bool, message, filepath)
        """
        if not filepath:
            filepath = self.geoint_cfg.get("default_map_path", "logs/geo_map.html")

        locations = self._collect_locations()
        movements = self._build_movement()

        html = self._generate_html(locations, movements, offline=offline)

        try:
            dir_name = os.path.dirname(filepath) if filepath else ""
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            return True, f"Map exported to {filepath} ({len(locations)} markers, {len(movements)} routes)", filepath
        except Exception as e:
            return False, f"Failed to export map: {e}", filepath

    def get_map_data(self):
        """Harita verisini (locations + movements) döndürür — test/debug için."""
        return {
            "locations": self._collect_locations(),
            "movements": self._build_movement(),
        }