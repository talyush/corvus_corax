"""Corvus Corax v1.3 - Advanced Human & Technical Anomaly Engine.

Fuses technical infrastructure anomalies with human behavioral/linguistic anomalies.
Crucial Principle: Anomaly Score != Threat Probability
Identifies deviations from baseline while providing benign counter-explanations.
"""
from typing import Dict, Any, List, Optional


class HumanAnomalyEngine:
    """Teknik ve İnsani Çok Boyutlu Anomali Tespit Motoru."""

    def detect_anomalies(self, target: str, current_profile: Dict[str, Any],
                         baseline_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not baseline_profile:
            return {
                "target": target,
                "anomaly_score": 0.0,
                "anomaly_level": "Temel Seviye (Baseline Oluşturuluyor)",
                "detected_deviations": [],
                "benign_explanations": ["İlk gözlem yapıldığı için karşılaştırmalı bir sapma tespit edilemedi."],
                "threat_assessment_note": "Anomali skoru doğrudan bir tehdit veya saldırı anlamına gelmez.",
            }

        deviations = []
        benign_explanations = []
        raw_anomaly_points = 0.0

        # 1. Stilometrik Sapma (Yazım stili aniden değişti mi?)
        sty_curr = current_profile.get("stylometry", {})
        sty_base = baseline_profile.get("stylometry", {})
        if sty_curr and sty_base:
            from .stylometry import StylometryEngine
            sim = StylometryEngine().compute_stylometric_similarity(sty_curr, sty_base)
            if sim < 0.45:
                raw_anomaly_points += 0.35
                deviations.append(f"Belirgin dilsel stil sapması (Benzerlik: %{int(sim*100)})")
                benign_explanations.append("Farklı bir ortamda (mobil/klavye), aciliyet altında yazılmış veya başka bir çalışan tarafından iletilmiş olabilir.")

        # 2. Zamanlama Sapması (Aktivite saatleri tamamen değişti mi?)
        time_curr = current_profile.get("timing", {})
        time_base = baseline_profile.get("timing", {})
        if time_curr and time_base:
            tz_c = time_curr.get("probable_timezone_estimate")
            tz_b = time_base.get("probable_timezone_estimate")
            if tz_c != tz_b and tz_c != "Bilinmiyor" and tz_b != "Bilinmiyor":
                raw_anomaly_points += 0.30
                deviations.append(f"Aktivite zaman penceresi / Timezone kayması ({tz_b} -> {tz_c})")
                benign_explanations.append("Fiziksel seyahat, nöbet değişimi, VPN kullanımı veya mesai saati dışı çalışma.")

        # 3. Altyapı ve ASN Değişimi
        infra_curr = current_profile.get("infrastructure", {})
        infra_base = baseline_profile.get("infrastructure", {})
        if infra_curr and infra_base:
            asn_c = set(infra_curr.get("distinct_asns_used", []))
            asn_b = set(infra_base.get("distinct_asns_used", []))
            if asn_c and asn_b and not asn_c.intersection(asn_b):
                raw_anomaly_points += 0.35
                deviations.append(f"Altyapı operatörü/ASN tamamen farklı bir ağa kaydı")
                benign_explanations.append("ISP değişikliği, yeni hosting sağlayıcısına geçiş veya kurumsal ağdan bağlanma.")

        anomaly_score = min(1.0, round(raw_anomaly_points, 2))

        if anomaly_score >= 0.70:
            level = "Yüksek Sapma (Çok Boyutlu Değişim)"
        elif anomaly_score >= 0.35:
            level = "Orta Düzey Sapma (Tekil Boyutta Değişim)"
        else:
            level = "Düşük / Rutin Seviye"

        return {
            "target": target,
            "anomaly_score": anomaly_score,
            "anomaly_level": level,
            "detected_deviations": deviations,
            "benign_explanations": benign_explanations or ["Önemli bir sapma gözlemlenmedi."],
            "threat_assessment_note": "KRİTİK İLKE: Anomali skoru tek başına tehdit veya kötü niyet göstergesi DEĞİLDİR. Doğal operasyonel değişiklikler de anomali üretebilir.",
        }
