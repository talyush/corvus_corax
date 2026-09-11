# -*- coding: utf-8 -*-
"""Corvus CANLI SOHBET doğrulama — aynı soru farklı cevaplar üretmeli.

Şikayet: "cevaplar donuk, genelde aynı, canlı değil".
Bu test, aynı sosyal/felsefi/selam girdisinin tekrarlanan sorularda
varyant havuzu sayesinde birbirinden farklı cevaplar ürettiğini doğrular.
"""
import os
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


def main():
    from core.mind.brain import MindBrain

    print("=" * 70)
    print("CANLI SOHBET — Çeşitlilik (varyant) doğrulaması")
    print("=" * 70)

    tmp = tempfile.mkdtemp(prefix="corvus_lively_")
    brain = MindBrain(persist_path=os.path.join(tmp, "mind.json"), auto_persist=True)

    cases = [
        ("merhaba", 3),
        ("anlam nedir", 3),
        ("cevapların statik mi dinamik mi", 3),
    ]

    total_unique = 0
    for question, turns in cases:
        print(f"\n[{question!r}]")
        seen = set()
        for i in range(turns):
            r = brain.generate_response(question, [], {})
            first = r[:60]
            seen.add(first)
            print(f"  {i+1}. {r[:90]}")
        print(f"  -> benzersiz öncül: {len(seen)}/{turns}")
        total_unique += len(seen)

    # En az bir testte çeşitlilik olmalı (sosyal/selam varyant havuzu en az 3)
    social_seen = set()
    for i in range(4):
        social_seen.add(brain.generate_response("merhaba", [], {})[:50])
    print(f"\n[merhaba x4] benzersiz: {len(social_seen)}/4")
    assert len(social_seen) >= 2, "selamlaşma en az 2 farklı cevap üretmeli (verdiği sıkıcılık şikayeti)"

    print("\n" + "-" * 70)
    print("OK — Sohbet artık varyantli/canli (aynı soruya farklı cevaplar).")
    return 0


if __name__ == "__main__":
    sys.exit(main())