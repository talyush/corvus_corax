"""Verification test for Corvus Corax v1.3 Stylometry Engine."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.human.stylometry import StylometryEngine


def test_stylometry():
    print("=== TEST 1: Stylometry Engine & Linguistic Feature Extraction ===")
    engine = StylometryEngine()

    text_sample_a = (
        "Sistem mimarisi üzerinde gerçekleştirdiğimiz derin analiz sonucunda, altyapının "
        "DNS ve TLS yapılandırmalarında belirli tutarsızlıklar gözlemlenmiştir. "
        "Çünkü her dijital imza geride analitik bir iz bırakır; dolayısıyla doğrulama zorunludur."
    )

    text_sample_b = (
        "DNS ve TLS loglarında tutarsızlık tespit edildi. "
        "Sistem izleri dikkatle analiz edildi ve doğrulandı."
    )

    # 1. Analyze Sample A
    res_a = engine.analyze(text_sample_a)
    print(f"[+] Sample A Total Words: {res_a['total_words']}, Sentences: {res_a['total_sentences']}")
    print(f"[+] Vocabulary Diversity (TTR): {res_a['vocabulary_diversity']['ttr']} ({res_a['vocabulary_diversity']['diversity_level']})")
    print(f"[+] Mean Sentence Length: {res_a['sentence_length']['mean']} words")
    print(f"[+] Detected Language: {res_a['detected_language']}")
    assert res_a["total_words"] > 0
    assert res_a["detected_language"] == "tr"
    assert res_a["vocabulary_diversity"]["ttr"] > 0.60

    # 2. Analyze Sample B
    res_b = engine.analyze(text_sample_b)
    print(f"\n[+] Sample B Total Words: {res_b['total_words']}, Sentences: {res_b['total_sentences']}")

    # 3. Stylometric Similarity
    sim_score = engine.compute_stylometric_similarity(res_a, res_b)
    print(f"\n[+] Stylometric Similarity Score: {sim_score} (%{int(sim_score*100)})")
    assert 0.0 <= sim_score <= 1.0

    print("\n[+] STYLOMETRY ENGINE TEST PASSED CLEANLY!")
    return 0


if __name__ == "__main__":
    sys.exit(test_stylometry())
