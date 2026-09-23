"""Corvus Corax v1.3 - Semantic Interest Network & Temporal Drift.

Tracks an entity's semantic topics of interest and measures temporal interest drift over time.
"""
from typing import Dict, Any, List, Optional
from collections import Counter


class SemanticInterestNetwork:
    """Anlamsal İlgi Alanları ve Zaman İçinde İlgi Kayması (Drift) Motoru."""

    TOPIC_TAXONOMY = {
        "cybersecurity": ["exploit", "recon", "whois", "dns", "tls", "vuln", "security", "threat", "payload", "cve", "patch"],
        "software_dev": ["python", "javascript", "code", "git", "github", "docker", "api", "database", "backend", "frontend"],
        "infrastructure": ["server", "linux", "cloud", "aws", "nginx", "routing", "ip", "asn", "subnet", "domain"],
        "cryptography": ["cipher", "rsa", "hash", "sha256", "wallet", "btc", "eth", "crypto", "encryption", "keys"],
        "philosophy_ai": ["intelligence", "meaning", "consciousness", "mind", "reasoning", "ethics", "logic", "socrates", "model"],
        "general_osint": ["social", "profile", "investigation", "footprint", "identity", "phone", "email", "academic"]
    }

    def extract_topics(self, texts: List[str]) -> Counter:
        """Metinlerden konu dağılımını çıkarır."""
        combined = " ".join(texts).lower()
        topic_counts = Counter()
        for topic, keywords in self.TOPIC_TAXONOMY.items():
            hits = sum(combined.count(kw) for kw in keywords)
            if hits > 0:
                topic_counts[topic] = hits
        return topic_counts

    def analyze_interest_drift(self, past_texts: List[str], current_texts: List[str]) -> Dict[str, Any]:
        """Geçmiş dönem ile şimdiki dönem arasındaki ilgi alanı değişimini (drift) analiz eder."""
        past_topics = self.extract_topics(past_texts)
        current_topics = self.extract_topics(current_texts)

        all_topics = set(past_topics.keys()).union(set(current_topics.keys()))
        if not all_topics:
            return {
                "dominant_topics": [],
                "drift_detected": False,
                "topic_transitions": [],
                "summary": "Yetersiz anlamsal veri.",
            }

        total_past = max(1, sum(past_topics.values()))
        total_curr = max(1, sum(current_topics.values()))

        transitions = []
        drift_magnitude = 0.0

        for t in all_topics:
            ratio_past = past_topics.get(t, 0) / total_past
            ratio_curr = current_topics.get(t, 0) / total_curr
            delta = ratio_curr - ratio_past
            drift_magnitude += abs(delta)

            if abs(delta) > 0.15:
                direction = "Yükselen İlgi" if delta > 0 else "Azalan İlgi"
                transitions.append({
                    "topic": t,
                    "past_share": round(ratio_past * 100, 1),
                    "current_share": round(ratio_curr * 100, 1),
                    "trend": direction,
                })

        dominant_current = [t[0] for t in current_topics.most_common(3)]
        drift_detected = drift_magnitude > 0.40

        return {
            "dominant_topics": dominant_current,
            "drift_detected": drift_detected,
            "drift_magnitude_score": round(drift_magnitude, 2),
            "topic_transitions": transitions,
            "summary": "Belirgin anlamsal ilgi alanı kayması tespit edildi." if drift_detected else "İlgi alanları zaman içinde tutarlı.",
        }
