"""Corvus Corax v1.3 - Textual Psychology Profiling.

Ethical, non-dogmatic psychological and cognitive signal analysis:
Pattern: Observed Linguistic Signals -> Possible Interpretation -> Alternative Explanations -> Confidence

Rules:
- NEVER assign rigid or clinical psychological labels to a human subject.
- Always provide counter-explanations (e.g. situational stress, professional jargon, intentional brevity).
- Quantify observational confidence transparently.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class PsychologicalObservation:
    """Tek bir dilsel ve bilişsel gözlem kaydı."""
    observed_signal: str
    signal_strength: float  # [0.0 - 1.0]
    possible_interpretation: str
    alternative_explanations: List[str]
    confidence: float  # [0.0 - 1.0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observed_signal": self.observed_signal,
            "signal_strength": round(self.signal_strength, 2),
            "possible_interpretation": self.possible_interpretation,
            "alternative_explanations": self.alternative_explanations,
            "confidence": round(self.confidence, 2),
        }


class TextualPsychologyProfiler:
    """Etik ve Hipotez Odaklı Metinsel Psikoloji ve Bilişsel Profiler."""

    def profile_text(self, text: str, stylometry_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raw_text = text.strip()
        lower = raw_text.lower()
        words = re.findall(r'\b\w+\b', lower)
        total_words = max(1, len(words))

        observations: List[PsychologicalObservation] = []

        # 1. Bilişsel Titizlik & Detay Odaklılık Sinyali (Analytical Rigor)
        analytical_markers = [
            "çünkü", "cunku", "dolayısıyla", "dolayisiyla", "ancak", "örneğin", "ornegin",
            "nedenle", "kapsamında", "kapsaminda", "because", "therefore", "however",
            "specifically", "evidence", "hypothesis", "verify", "data", "analysis"
        ]
        analytical_hits = sum(1 for w in words if w in analytical_markers)
        analytical_density = analytical_hits / total_words

        if analytical_density > 0.04:
            observations.append(PsychologicalObservation(
                observed_signal=f"Yüksek nedensellik ve yapılandırılmış mantık bağlaçları kullanımı (%{round(analytical_density*100, 1)})",
                signal_strength=min(1.0, analytical_density * 15),
                possible_interpretation="Sistematik, analitik ve kanıt temelli düşünme eğilimi.",
                alternative_explanations=[
                    "Teknik veya akademik bir raporlama bağlamında bulunma gerekliliği",
                    "Savunmacı veya hesap verebilir olma zorunluluğu altında yazılmış metin"
                ],
                confidence=0.75
            ))

        # 2. İletişimsel Aciliyet ve Baskı Sinyali (Urgency & Compression)
        short_sentences = bool(stylometry_data and stylometry_data.get("sentence_length", {}).get("mean", 10) < 5)
        has_caps = bool(re.search(r'\b[A-ZÇĞİÖŞÜ]{4,}\b', raw_text))
        urgency_words = ["acil", "hemen", "çabuk", "cabuk", "şimdi", "simdi", "urgent", "asap", "now", "immediately", "quick"]
        urgency_hits = sum(1 for w in words if w in urgency_words)

        if urgency_hits >= 2 or (short_sentences and has_caps):
            observations.append(PsychologicalObservation(
                observed_signal="Kısa cümle blokları, aciliyet belirteçleri veya vurgulu büyük harf kullanımı",
                signal_strength=0.70,
                possible_interpretation="Zaman baskısı, yüksek operasyonel stres veya hızlı karar alma ortamı.",
                alternative_explanations=[
                    "Mobil cihaz üzerinden hızlıca iletilen rutin operasyonel mesajlaşma",
                    "Doğal olarak kısa ve doğrudan iletişim tercih eden bir mizaç"
                ],
                confidence=0.65
            ))

        # 3. İletişimsel Açıklık vs Ketumluk Sinyali (Openness vs Guardedness)
        first_person_singular = ["ben", "benim", "bana", "beni", "kendim", "i", "my", "me", "myself"]
        first_person_hits = sum(1 for w in words if w in first_person_singular)
        first_person_ratio = first_person_hits / total_words

        if first_person_ratio < 0.005 and total_words > 40:
            observations.append(PsychologicalObservation(
                observed_signal="Birinci tekil şahıs ('ben') kullanımının neredeyse tamamen yokluğu",
                signal_strength=0.65,
                possible_interpretation="Kişisel mesafeyi koruma, kurumsal/objektif kimliğin arkasında kalma tercihi.",
                alternative_explanations=[
                    "Kurumsal yazışma protokollerine katı bağlılık",
                    "Gizlilik bilinci (OpSec) gereği kişisel kimlikten kaçınma"
                ],
                confidence=0.70
            ))
        elif first_person_ratio > 0.08:
            observations.append(PsychologicalObservation(
                observed_signal="Yüksek birinci tekil şahıs ('ben') zamiri sıklığı",
                signal_strength=0.70,
                possible_interpretation="Doğrudan kişisel sorumluluk alma, benmerkezci veya içsel odaklı anlatım.",
                alternative_explanations=[
                    "Bireysel deneyim aktarımı veya günce formatında yazım",
                    "Konuşma dilinin doğallığı"
                ],
                confidence=0.60
            ))

        # 4. Şüphecilik ve Doğrulama İhtiyacı (Vigilance & Skepticism)
        doubt_markers = ["acaba", "belki", "kesin mi", "doğru mu", "emin", "şüpheli", "really", "maybe", "verify", "doubt", "sure"]
        doubt_hits = sum(1 for w in words if w in doubt_markers)

        if doubt_hits >= 2:
            observations.append(PsychologicalObservation(
                observed_signal="Doğruluk ve kesinlik sorgulayan kuşkucu belirteçler",
                signal_strength=0.60,
                possible_interpretation="Yüksek bilişsel teyit ihtiyacı, analitik şüphecilik.",
                alternative_explanations=[
                    "Geçmişte yaşanan yanıltıcı bir bilgiye karşı temkinli tepki",
                    "Sokratik sorgulama yöntemi izleme"
                ],
                confidence=0.70
            ))

        # Varsayılan temel profil
        summary_tone = "Analitik ve Dengeli" if analytical_density > 0.02 else "Operasyonel / Doğrudan"

        return {
            "observations_count": len(observations),
            "observations": [o.to_dict() for o in observations],
            "cognitive_style_summary": summary_tone,
            "ethical_safeguard": "Analiz kesin tanı ve etiket içermez; yalnızca gözlemlenen dilsel hipotezleri ve alternatiflerini sunar.",
        }
