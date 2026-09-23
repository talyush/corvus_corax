"""Corvus Corax v1.3 - Similarity Engine.

Multi-dimensional profile and fingerprint comparison:
Crucial Principle: Similarity Score != Same Identity Claim
Calculates observed similarity while maintaining strict distinction from identity attribution.
"""
from typing import Dict, Any, List, Optional


class SimilarityEngine:
    """Çok Boyutlu Benzerlik ve Ayak İzi Karşılaştırma Motoru."""

    def compare_profiles(self, profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        İki insan/varlık profilini çoklu boyutlarda karşılaştırır:
        - Stilometri / Dilsel benzerlik (ağırlık: %30)
        - Zamanlama / Aktivite ritmi örtüşmesi (ağırlık: %25)
        - Altyapı ve E-posta tercihleri (ağırlık: %20)
        - Sosyal handle ve isimlendirme yakınlığı (ağırlık: %15)
        - Anlamsal konu örtüşmesi (ağırlık: %10)
        """
        dimension_scores = {}
        corroborating_factors = []
        conflicting_factors = []

        # 1. Stilometrik Benzerlik
        sty_a = profile_a.get("stylometry", {})
        sty_b = profile_b.get("stylometry", {})
        if sty_a and sty_b:
            from .stylometry import StylometryEngine
            sty_engine = StylometryEngine()
            sty_sim = sty_engine.compute_stylometric_similarity(sty_a, sty_b)
            dimension_scores["stylometric_similarity"] = sty_sim
            if sty_sim > 0.70:
                corroborating_factors.append(f"Yüksek dilsel stil ve sözcük çeşitliliği benzerliği (%{int(sty_sim*100)})")
            elif sty_sim < 0.40:
                conflicting_factors.append(f"Belirgin biçimde farklı cümle yapısı ve sözcük dağarcığı (%{int(sty_sim*100)})")
        else:
            dimension_scores["stylometric_similarity"] = 0.50

        # 2. Zamanlama / Aktivite Ritmi
        timing_a = profile_a.get("timing", {})
        timing_b = profile_b.get("timing", {})
        if timing_a and timing_b:
            peaks_a = set(timing_a.get("peak_hours_utc", []))
            peaks_b = set(timing_b.get("peak_hours_utc", []))
            overlap_peaks = len(peaks_a.intersection(peaks_b)) / max(1, len(peaks_a.union(peaks_b)))
            dimension_scores["timing_overlap"] = round(overlap_peaks, 2)
            if overlap_peaks >= 0.5:
                corroborating_factors.append(f"Örtüşen aktif saat pencereleri (UTC)")
            else:
                conflicting_factors.append(f"Farklı aktivite saatleri ve ritim pencereleri")
        else:
            dimension_scores["timing_overlap"] = 0.50

        # 3. Altyapı ve Teknik Tercihler
        infra_a = profile_a.get("infrastructure", {})
        infra_b = profile_b.get("infrastructure", {})
        if infra_a and infra_b:
            arch_a = infra_a.get("email_provider_archetype")
            arch_b = infra_b.get("email_provider_archetype")
            infra_match = 1.0 if arch_a == arch_b else 0.3
            dimension_scores["infrastructure_similarity"] = infra_match
            if infra_match == 1.0:
                corroborating_factors.append(f"Benzer e-posta ve altyapı sertleştirme modeli: '{arch_a}'")
        else:
            dimension_scores["infrastructure_similarity"] = 0.50

        # 4. Genel Ağırlıklı Benzerlik Skoru Hesabı
        overall_similarity = (
            dimension_scores.get("stylometric_similarity", 0.5) * 0.35 +
            dimension_scores.get("timing_overlap", 0.5) * 0.30 +
            dimension_scores.get("infrastructure_similarity", 0.5) * 0.35
        )
        overall_similarity = round(overall_similarity, 3)

        # 5. ETIK AYRIM: Benzerlik != Aynı Kişi İddiası
        if overall_similarity >= 0.80:
            assessment = "Yüksek Örüntü Benzerliği (Benzer alışkanlıklara ve yazım stiline sahip bağımsız profiller veya aynı operatör hipotezi)."
        elif overall_similarity >= 0.50:
            assessment = "Orta Düzey Kısmi Örtüşme (Belirli alanlarda benzerlik, ancak ayrışan karakteristikler mevcut)."
        else:
            assessment = "Düşük Benzerlik (Farklı dilsel ve davranışsal profillere işaret ediyor)."

        return {
            "overall_similarity_score": overall_similarity,
            "overall_similarity_percentage": f"%{int(overall_similarity * 100)}",
            "dimension_scores": dimension_scores,
            "corroborating_factors": corroborating_factors,
            "conflicting_factors": conflicting_factors,
            "epistemic_assessment": assessment,
            "identity_claim_disclaimer": "ÖNEMLİ: Benzerlik skoru (%{}), aynı kişi olduğunu KANITLAMAZ. Benzer demografik, profesyonel veya teknik geçmişe sahip farklı bireyler de yüksek benzerlik gösterebilir.".format(int(overall_similarity * 100)),
        }
