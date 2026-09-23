"""Corvus Corax v1.3 - Behavior Profiling Engine.

Synthesizes behavioral patterns across time, data streams, and interaction frequencies.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class BehaviorProfiler:
    """Davranışsal Örüntü ve Alışkanlık Profileri."""

    def build_profile(self, events: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not events:
            return {
                "total_events": 0,
                "behavioral_summary": "Yetersiz olay kaydı — profil oluşturulamadı.",
                "interaction_consistency": "Bilinmiyor",
                "habit_indicators": [],
            }

        total = len(events)
        sources = set(e.get("source_module", "unknown") for e in events)
        action_types = set(e.get("event", e.get("action", "unknown")) for e in events)

        # Tutarlılık değerlendirmesi
        consistency = "Yüksek (Düzenli Etkileşim)" if total >= 5 else "Gelişmekte Olan (Seyrek Gözlem)"

        habit_indicators = []
        if len(sources) >= 3:
            habit_indicators.append("Çoklu platform ve modül üzerinde aktif ayak izi")
        if total > 10:
            habit_indicators.append("Sık ve sürekli dijital veri akışı")

        return {
            "total_events": total,
            "distinct_sources": list(sources),
            "distinct_action_types": list(action_types),
            "interaction_consistency": consistency,
            "habit_indicators": habit_indicators,
            "behavioral_summary": f"{total} gözlem üzerinden {len(sources)} farklı kaynakta tutarlı iz.",
        }
