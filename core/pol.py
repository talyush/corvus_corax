"""Corvus Corax v0.9 — Pattern of Life (POL) Analiz Motoru.

Vault'taki kalıcı event'leri ve session context'teki geçici event'leri analiz ederek
davranış desenleri çıkarır:
  1. Activity Rhythm (Aktiflik Ritmi) — saatlik/haftalık aktivite dağılımı
  2. Movement Pattern (Seyahat Deseni) — konum geçmişi ve rotalar
  3. Communication Pattern (İletişim Deseni) — varlıklar arası ilişkiler
  4. Anomaly Detection (Anomali Tespiti) — kural + istatistik hibrit model
  5. Case File (Soruşturma Dosyası) — tüm kanıt zinciri

Hibrit anomali modeli:
  - Kural bazlı: gece aktivitesi, beklenmeyen ülke, beklenmeyen kaynak
  - İstatistiksel: z-score ile normal davranıştan sapma
"""
import os
import json
from datetime import datetime, timezone
from collections import Counter

from core.config import load_rules


class PatternOfLifeEngine:
    """POL analiz motoru — davranış deseni çıkarır, anomali tespit eder."""

    def __init__(self, context_manager, vault=None):
        self.context_manager = context_manager
        self.vault = vault
        self.rules = load_rules()
        self.pol_cfg = self.rules.get("pol", {})

    def _get_events(self, entity, vault_only=False):
        """
        Bir varlığın tüm event'lerini toplar.
        vault_only=True ise sadece vault'tan; False ise vault + session birleşik.
        """
        events = []

        # Vault'tan
        if self.vault:
            vault_events = self.vault.query_events(entity=entity, limit=500)
            for ev in vault_events:
                ev = dict(ev)
                ev["_source"] = "vault"
                events.append(ev)

        # Session'dan (vault_only değilse)
        if not vault_only:
            session_events = self.context_manager.data.get("events", [])
            for ev in session_events:
                if entity in ev.get("entity", ""):
                    ev = dict(ev)
                    ev["_source"] = "session"
                    # Vault'ta zaten varsa tekrar ekleme
                    if not any(e.get("timestamp") == ev.get("timestamp")
                               and e.get("action") == ev.get("action") for e in events):
                        events.append(ev)

        return events

    def analyze_activity(self, entity, vault_only=False):
        """
        Aktiflik ritmi — saatlik ve haftalık aktivite dağılımı.
        Returns: dict with hourly_distribution, weekly_pattern, stats
        """
        events = self._get_events(entity, vault_only)
        if not events:
            return {"status": "insufficient_data", "events": 0}

        hourly_activity = Counter()
        weekly_activity = Counter()
        source_breakdown = Counter()

        for ev in events:
            ts = ev.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hourly_activity[dt.hour] += 1
                weekly_activity[dt.weekday()] += 1
            except Exception:
                continue
            source_breakdown[ev.get("source", "unknown")] += 1

        # Ortalama aktivite (istatistiksel anomali için)
        hours = list(range(24))
        hour_counts = [hourly_activity.get(h, 0) for h in hours]
        mean_activity = sum(hour_counts) / 24 if hour_counts else 0
        std_activity = (sum((x - mean_activity) ** 2 for x in hour_counts) / 24) ** 0.5 if hour_counts else 0

        # En aktif saatler
        peak_hours = [h for h, c in hourly_activity.most_common(3)]

        return {
            "status": "ok",
            "entity": entity,
            "event_count": len(events),
            "vault_only": vault_only,
            "sources": dict(source_breakdown),
            "hourly_distribution": {str(h): hourly_activity.get(h, 0) for h in hours},
            "peak_hours": peak_hours,
            "weekly_pattern": {str(d): weekly_activity.get(d, 0) for d in range(7)},
            "stats": {
                "mean_activity_per_hour": round(mean_activity, 2),
                "std_activity_per_hour": round(std_activity, 2),
                "total_events": len(events),
            },
        }

    def analyze_movement(self, entity, vault_only=False):
        """
        Seyahat deseni — konum geçmişi ve rotalar.
        Returns: dict with locations, route, vpn_warning
        """
        events = self._get_events(entity, vault_only)
        locations = []
        movements = []

        # Context'teki IP geolocation verilerini topla
        ip_data = self.context_manager.data.get("ips", {})

        # Entity → IP ilişkileri
        relations = self.context_manager.data.get("relations", [])
        entity_ips = set()
        for rel in relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            if dst.get("type") == "ip" and src.get("value") == entity.replace(f"{src.get('type')}:", ""):
                entity_ips.add(dst.get("value"))

        # IP'lerin konumlarını topla
        for ip in entity_ips:
            if ip in ip_data:
                geo = ip_data[ip].get("geo", {})
                lat = geo.get("latitude") or geo.get("lat")
                lon = geo.get("longitude") or geo.get("lon")
                if lat is not None and lon is not None:
                    locations.append({
                        "ip": ip,
                        "lat": float(lat),
                        "lon": float(lon),
                        "label": f"{geo.get('city', '')}, {geo.get('country', '')}".strip(", "),
                        "country": geo.get("country", ""),
                    })

        # located_in / traveled event'lerinden konum geçmişi
        for ev in events:
            if ev.get("action") in ("located_in", "traveled", "geo_updated"):
                loc = ev.get("location") or (ev.get("metadata") or {}).get("location")
                if loc:
                    movements.append({
                        "time": ev.get("timestamp"),
                        "location": loc,
                        "source": ev.get("_source", "session"),
                    })

        # VPN uyarısı — çok hızlı ülke değişimi
        vpn_warning = False
        if self.pol_cfg.get("movement_vpn_warning", True) and len(movements) >= 2:
            # Aynı gün içinde 2+ farklı lokasyon → olası VPN
            days = {}
            for m in movements:
                try:
                    day = m["time"][:10]
                    days.setdefault(day, set()).add(m["location"])
                except Exception:
                    continue
            for day, locs in days.items():
                if len(locs) >= 2:
                    vpn_warning = True
                    break

        return {
            "entity": entity,
            "location_count": len(locations),
            "locations": locations,
            "movement_history": movements[:20],
            "vpn_warning": vpn_warning,
        }

    def analyze_communications(self, entity, vault_only=False):
        """
        İletişim deseni — varlığın bağlantıda olduğu diğer varlıklar.
        """
        relations = self.context_manager.data.get("relations", [])
        entity_value = entity.split(":", 1)[1] if ":" in entity else entity

        connections = []
        for rel in relations:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            if src.get("value") == entity_value:
                connections.append({
                    "direction": "out",
                    "relation": rel.get("relation"),
                    "target": f"{dst.get('type')}:{dst.get('value')}",
                    "confidence": rel.get("confidence", 1.0),
                })
            elif dst.get("value") == entity_value:
                connections.append({
                    "direction": "in",
                    "relation": rel.get("relation"),
                    "target": f"{src.get('type')}:{src.get('value')}",
                    "confidence": rel.get("confidence", 1.0),
                })

        # İletişim türlerine göre grupla
        comm_types = Counter(c["relation"] for c in connections)

        return {
            "entity": entity,
            "connection_count": len(connections),
            "communication_types": dict(comm_types),
            "connections": connections[:20],
        }

    def detect_anomalies(self, entity, vault_only=False):
        """
        Anomali tespiti — hybrid model (kural + istatistik).
        Returns: dict with score, findings, vpn_warning
        """
        findings = []
        score = 0

        # --- Kural bazlı ---
        events = self._get_events(entity, vault_only)
        night_hours = self.pol_cfg.get("night_activity_hours", [0, 1, 2, 3, 4, 5])

        # 1. Gece aktivitesi
        night_events = 0
        total_events = 0
        for ev in events:
            ts = ev.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                total_events += 1
                if dt.hour in night_hours:
                    night_events += 1
            except Exception:
                continue
        if total_events >= self.pol_cfg.get("min_events_for_analysis", 5) and night_events > 0:
            night_ratio = night_events / total_events
            if night_ratio > 0.3:
                score += 40
                findings.append(f"Gece aktivitesi anormal derecede yüksek ({night_events}/{total_events} event'te)")

        # 2. Beklenmeyen ülke/konum değişimi
        movement = self.analyze_movement(entity, vault_only)
        if movement.get("vpn_warning"):
            score += 30
            findings.append("Aynı gün içinde birden fazla farklı lokasyon — olası VPN/kayıt hatası")

        # 3. İletişim anormalliği — çok sayıda candidate ilişki
        comm = self.analyze_communications(entity, vault_only)
        candidate_rels = [c for c in comm.get("connections", [])
                          if any(k in c.get("relation", "") for k in ("candidate", "possible", "conflict"))]
        if len(candidate_rels) >= 3:
            score += 20
            findings.append(f"Çok sayıda doğrulanmamış candidate ilişki ({len(candidate_rels)} adet)")

        # --- İstatistiksel bazlı ---
        activity = self.analyze_activity(entity, vault_only)
        if activity.get("status") == "ok":
            stats = activity.get("stats", {})
            std = stats.get("std_activity_per_hour", 0)
            mean = stats.get("mean_activity_per_hour", 0)
            # Z-skoru: anormal saatlerde yoğunluk
            if std > 0 and mean > 0:
                hourly = activity.get("hourly_distribution", {})
                for h_str, count in hourly.items():
                    try:
                        z = (count - mean) / std
                        if z > self.pol_cfg.get("anomaly_zscore_threshold", 2.0):
                            score += 10
                            findings.append(f"Saat {h_str}:00'da normalin çok üzerinde aktivite (z-score: {z:.2f})")
                            break  # Max 1 istatistiksel bulgu
                    except Exception:
                        continue

        # Skoru sınırla
        score = min(score, 100)
        threshold = self.pol_cfg.get("anomaly_threshold", 70)

        return {
            "entity": entity,
            "score": score,
            "level": "HIGH" if score >= threshold else "MEDIUM" if score >= threshold * 0.5 else "LOW",
            "findings": findings,
            "vpn_warning": movement.get("vpn_warning", False),
            "event_count": len(events),
        }

    def generate_casefile(self, entity, vault_only=False):
        """
        Varlığın tam soruşturma dosyası — tüm analizlerin birleşimi.
        """
        activity = self.analyze_activity(entity, vault_only)
        movement = self.analyze_movement(entity, vault_only)
        comm = self.analyze_communications(entity, vault_only)
        anomalies = self.detect_anomalies(entity, vault_only)

        casefile = {
            "entity": entity,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_source": "vault" if vault_only else "vault + session",
            "activity": activity,
            "movement": movement,
            "communications": comm,
            "anomaly": anomalies,
        }
        return casefile

    def save_casefile(self, entity, filepath=None, vault_only=False):
        """Case file'ı diske yazar."""
        if not filepath:
            filepath = f"vault/casefiles/case_{entity.replace(':', '_')}.json"

        casefile = self.generate_casefile(entity, vault_only)
        dir_name = os.path.dirname(filepath) if filepath else ""
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(casefile, f, indent=4, ensure_ascii=False)
            return True, f"Case file saved to {filepath}", casefile
        except Exception as e:
            return False, f"Failed to save case file: {e}", casefile