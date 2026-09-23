"""Verification test for Corvus Corax v1.3 Similarity vs Identity Engine."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.human.similarity import SimilarityEngine


def test_similarity():
    print("=== TEST 3: Similarity Engine (Similarity != Identity) ===")
    engine = SimilarityEngine()

    profile_a = {
        "stylometry": {
            "total_words": 150,
            "sentence_length": {"mean": 12.5},
            "word_length": {"mean": 5.4},
            "vocabulary_diversity": {"ttr": 0.65},
            "function_word_distribution": {"ve": 3.5, "için": 2.1, "bu": 1.8},
        },
        "timing": {
            "peak_hours_utc": [9, 14, 16],
            "probable_timezone_estimate": "UTC+3",
        },
        "infrastructure": {
            "email_provider_archetype": "Gizlilik ve Güvenlik Odaklı (Privacy-Centric)",
            "distinct_asns_used": ["AS13335"],
        }
    }

    profile_b = {
        "stylometry": {
            "total_words": 130,
            "sentence_length": {"mean": 11.8},
            "word_length": {"mean": 5.2},
            "vocabulary_diversity": {"ttr": 0.62},
            "function_word_distribution": {"ve": 3.2, "için": 2.0, "bu": 1.6},
        },
        "timing": {
            "peak_hours_utc": [9, 14, 17],
            "probable_timezone_estimate": "UTC+3",
        },
        "infrastructure": {
            "email_provider_archetype": "Gizlilik ve Güvenlik Odaklı (Privacy-Centric)",
            "distinct_asns_used": ["AS13335"],
        }
    }

    comparison = engine.compare_profiles(profile_a, profile_b)
    print(f"[+] Overall Similarity: {comparison['overall_similarity_percentage']}")
    print(f"[+] Assessment: {comparison['epistemic_assessment']}")
    print(f"[+] Disclaimer: {comparison['identity_claim_disclaimer']}")

    assert comparison["overall_similarity_score"] > 0.75
    assert "KANITLAMAZ" in comparison["identity_claim_disclaimer"]

    print("\n[+] SIMILARITY ENGINE TEST PASSED CLEANLY!")
    return 0


if __name__ == "__main__":
    sys.exit(test_similarity())
