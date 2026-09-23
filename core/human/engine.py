"""Corvus Corax v1.3 - Human Intelligence Engine (Master Orchestrator).

"From Infrastructure Intelligence -> Human-Centered Intelligence."
Unifies all 11 pillars:
1. Persona Analysis
2. Behavior Profiling
3. Digital Footprint Correlation
4. Similarity vs Identity Distinction
5. Social Fingerprint
6. Infrastructure Fingerprint
7. Stylometry Engine
8. Textual Psychology Profiling
9. Digital Timing & Activity Rhythm
10. Semantic Network & Temporal Drift
11. Advanced Anomaly & Threat Detection
"""
from typing import Dict, Any, List, Optional

from .stylometry import StylometryEngine
from .psychology import TextualPsychologyProfiler
from .persona import PersonaAnalyzer
from .behavior import BehaviorProfiler
from .timing import ActivityRhythmEngine
from .semantic import SemanticInterestNetwork
from .social_fp import SocialFingerprintEngine
from .infra_fp import InfraFingerprintEngine
from .similarity import SimilarityEngine
from .footprint import FootprintCorrelator
from .anomaly import HumanAnomalyEngine


class HumanIntelligenceEngine:
    """Corvus Corax v1.3 İnsan Merkezli İstihbarat Ana Motoru."""

    def __init__(self, context_manager=None):
        self.context = context_manager
        self.stylometry = StylometryEngine()
        self.psychology = TextualPsychologyProfiler()
        self.persona = PersonaAnalyzer()
        self.behavior = BehaviorProfiler()
        self.timing = ActivityRhythmEngine()
        self.semantic = SemanticInterestNetwork()
        self.social_fp = SocialFingerprintEngine()
        self.infra_fp = InfraFingerprintEngine()
        self.similarity = SimilarityEngine()
        self.footprint = FootprintCorrelator()
        self.anomaly = HumanAnomalyEngine()

    def generate_human_profile(self, target: str, texts: Optional[List[str]] = None,
                               timestamps: Optional[List[str]] = None,
                               platforms_data: Optional[List[Dict[str, Any]]] = None,
                               domains_data: Optional[List[Dict[str, Any]]] = None,
                               ips_data: Optional[List[Dict[str, Any]]] = None,
                               emails: Optional[List[str]] = None,
                               baseline_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Bir insan/operatör hedefi için tam kapsamlı v1.3 insan istihbarat profili üretir."""
        texts = texts or []
        timestamps = timestamps or []
        emails = emails or []
        domains_data = domains_data or []
        ips_data = ips_data or []

        # 1. Stilometrik Analiz
        combined_text = " ".join(texts)
        stylometry_res = self.stylometry.analyze(combined_text)

        # 2. Metinsel Psikoloji ve Bilişsel Sinyaller
        psychology_res = self.psychology.profile_text(combined_text, stylometry_data=stylometry_res)

        # 3. Persona ve İletişim Tercihleri
        persona_res = self.persona.analyze_persona(texts)

        # 4. Zamanlama ve Gün İçi Ritim
        timing_res = self.timing.analyze_timestamps(timestamps)

        # 5. Sosyal Parmak İzi
        social_res = self.social_fp.build_fingerprint(target, platforms_data=platforms_data)

        # 6. Altyapı ve Teknik Tercihler
        infra_res = self.infra_fp.profile_infrastructure_habits(domains_data, ips_data, emails)

        # 7. Anlamsal İlgi Alanları
        topics_res = self.semantic.extract_topics(texts)
        dominant_topics = [t[0] for t in topics_res.most_common(3)]

        # 8. Ayak İzi Korelasyonu
        footprint_res = self.footprint.correlate_footprint(
            target=target,
            social_data=social_res,
            infra_data=infra_res,
            timing_data=timing_res,
            stylometry_data=stylometry_res
        )

        current_profile = {
            "target": target,
            "stylometry": stylometry_res,
            "psychology": psychology_res,
            "persona": persona_res,
            "timing": timing_res,
            "social": social_res,
            "infrastructure": infra_res,
            "dominant_topics": dominant_topics,
            "footprint": footprint_res,
        }

        # 9. Anomali Değerlendirmesi
        anomaly_res = self.anomaly.detect_anomalies(
            target=target,
            current_profile=current_profile,
            baseline_profile=baseline_profile
        )
        current_profile["anomaly_assessment"] = anomaly_res

        return current_profile

    def format_human_report(self, profile: Dict[str, Any], lang: str = "tr") -> str:
        """Kullanıcıya veya LLM ses katmanına sunulacak yapılandırılmış insan istihbarat raporu."""
        target = profile.get("target", "Target")
        sty = profile.get("stylometry", {})
        psy = profile.get("psychology", {})
        per = profile.get("persona", {})
        tim = profile.get("timing", {})
        soc = profile.get("social", {})
        inf = profile.get("infrastructure", {})
        anom = profile.get("anomaly_assessment", {})

        if lang == "tr":
            lines = [
                f"============================================================",
                f"  CORVUS HUMAN INTELLIGENCE REPORT (v1.3) — '{target}'",
                f"  Vizyon: From Infrastructure -> Human-Centered Intelligence",
                f"============================================================",
                f"  [1. PERSONA & ILETISIM PROFILI]",
                f"    * Teknik Dil Seviyesi  : {per.get('technical_depth')}",
                f"    * Iletisim Tonu        : {per.get('communication_tone')}",
                f"    * Etkilesim Tarzi      : {per.get('interaction_style')}",
                f"",
                f"  [2. DILSEL & STILOMETRIK PARMAK IZI]",
                f"    * Ort. Cumle Uzunlugu : {sty.get('sentence_length', {}).get('mean', 0)} kelime",
                f"    * Sozcuk Cesitliligi  : TTR {sty.get('vocabulary_diversity', {}).get('ttr', 0)} ({sty.get('vocabulary_diversity', {}).get('diversity_level')})",
                f"    * Noktalama Frekansi  : 100 kelimede {sty.get('punctuation_profile', {}).get('frequency_per_100_words', 0)} isaret",
                f"",
                f"  [3. METINSEL PSIKOLOJI VE BILISSEL GOZLEMLER]",
                f"    * Bilisel Tarz Ozeti  : {psy.get('cognitive_style_summary')}",
            ]
            for o in psy.get("observations", [])[:2]:
                lines.append(f"    + Gozlem: {o.get('observed_signal')}")
                lines.append(f"      -> Olası Yorum: {o.get('possible_interpretation')}")
                lines.append(f"      -> Alternatifler: {', '.join(o.get('alternative_explanations', []))}")
            
            lines.extend([
                f"",
                f"  [4. DIJITAL ZAMANLAMA & AKTIVITE RITMI (Pattern of Life)]",
                f"    * En Yogun Saatler (UTC) : {tim.get('peak_hours_utc')}",
                f"    * Muhtemel Timezone      : {tim.get('probable_timezone_estimate')}",
                f"    * Dinlenme Penceresi     : {tim.get('probable_quiet_window_utc')} UTC",
                f"    * Calisma Rutini         : {tim.get('routine_preference')}",
                f"",
                f"  [5. ALTYAPI & OPERATOR TERCIHLERI]",
                f"    * E-Posta Modeli         : {inf.get('email_provider_archetype')}",
                f"    * Sertlestirme Duzeyi    : {inf.get('security_hardening_level')}",
                f"",
                f"  [6. ANOMALI VE SAPMA DEGERLENDIRMESI]",
                f"    * Anomali Skoru          : {anom.get('anomaly_score', 0)} ({anom.get('anomaly_level')})",
                f"    * Etik Not               : {anom.get('threat_assessment_note')}",
                f"============================================================",
            ])
            return "\n".join(lines)
        else:
            lines = [
                f"============================================================",
                f"  CORVUS HUMAN INTELLIGENCE REPORT (v1.3) — '{target}'",
                f"  Vision: From Infrastructure -> Human-Centered Intelligence",
                f"============================================================",
                f"  [1. PERSONA & COMMUNICATION PROFILE]",
                f"    * Technical Depth      : {per.get('technical_depth')}",
                f"    * Communication Tone   : {per.get('communication_tone')}",
                f"    * Interaction Style    : {per.get('interaction_style')}",
                f"",
                f"  [2. LINGUISTIC & STYLOMETRIC FINGERPRINT]",
                f"    * Mean Sentence Length : {sty.get('sentence_length', {}).get('mean', 0)} words",
                f"    * Vocab Diversity (TTR): {sty.get('vocabulary_diversity', {}).get('ttr', 0)} ({sty.get('vocabulary_diversity', {}).get('diversity_level')})",
                f"    * Punctuation Rate     : {sty.get('punctuation_profile', {}).get('frequency_per_100_words', 0)} per 100 words",
                f"",
                f"  [3. TEXTUAL PSYCHOLOGY & COGNITIVE SIGNALS]",
                f"    * Style Summary        : {psy.get('cognitive_style_summary')}",
                f"",
                f"  [4. DIGITAL TIMING & ACTIVITY RHYTHM]",
                f"    * Peak Hours (UTC)     : {tim.get('peak_hours_utc')}",
                f"    * Probable Timezone    : {tim.get('probable_timezone_estimate')}",
                f"    * Quiet Rest Window    : {tim.get('probable_quiet_window_utc')} UTC",
                f"",
                f"  [5. ANOMALY EVALUATION]",
                f"    * Anomaly Score        : {anom.get('anomaly_score', 0)} ({anom.get('anomaly_level')})",
                f"    * Epistemic Note       : {anom.get('threat_assessment_note')}",
                f"============================================================",
            ]
            return "\n".join(lines)
