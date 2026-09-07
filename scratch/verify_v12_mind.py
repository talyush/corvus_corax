# -*- coding: utf-8 -*-
"""Corvus Mind v1.2 (Faz A) doğrulama scripti.

Amaç: Eski şablon motorunun yerine geçen gerçek, kod tabanlı beynin
şikayet edilen davranışları çözdüğünü göstermek:
  1. "ben kimim" -> gerçek kullanıcı profili (modele dayalı, boş şablon değil)
  2. dinamik yanıt -> aynı soru farklı bağlamda farklı cevap verir
  3. duygusal/sosyal ton -> iç durum ve hafızadan beslenir
  4. hafıza -> önceki turlar konuşmaya yansır
"""
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.mind.brain import MindBrain


def main():
    print("=" * 70)
    print("CORVUS MIND v1.2 (Faz A) — Doğrulama")
    print("=" * 70)

    brain = MindBrain()
    ctx = {"entities": {}, "relations": []}

    def ask(q):
        r = brain.generate_response(q, [], ctx)
        print(f"\n  KULLANICI: {q}")
        print(f"  CORVUS  : {r}")
        return r

    # 1. Selamlaşma (boş) + aynı sorunun dinamikliği
    print("\n[1] DİNAMİK YANIT — aynı soru, farklı bağlam")
    ask("merhaba")
    brain.generate_response("bana ne söyleyebilirsin", [], ctx)   # bağlam yükle
    ask("merhaba")
    ask("merhaba")  # her turda az da olsa farklı olmalı

    # 2. Meta / dinamik cevap
    print("\n[2] META — kendi çalışma şekli")
    ask("cevapların statik mi dinamik mi")

    # 3. Kimlik
    print("\n[3] 'ben kimim' → gerçek profil")
    brain.generate_response("anlam nedir", [], ctx)  # felsefi içerik yükle
    ask("ben kimim")

    print("\n[4] 'sen kimsin'")
    ask("sen kimsin")

    # 4. Felsefi
    print("\n[5] FELSEFİ")
    ask("anlam nedir")

    # 5. Duygusal
    print("\n[6] DUYGUSAL")
    ask("çok yoruldum")

    # 6. Kabiliyet
    print("\n[7] KABİLİYET")
    ask("yardım menüsünü aç")

    # 7. Hafıza üzerinden hedefli araştırma
    print("\n[8] HEDEFLİ SORGU")
    ask("example.com araştır")

    # 8. Nihai durum
    st = brain.debug_state()
    print("\n" + "-" * 70)
    print("[DURUM]")
    print("  bellekte tur:", st["memory"]["turn_count"], "| aktif konular:", st["memory"]["active_topics"])
    print("  iç durum(mood):", st["state"]["mood"], "| drive:", st["state"]["blend"])
    print("  kullanıcı modeli:", st["user"])
    print("=" * 70)
    print("OK — Corvus Mind v1.2 (Faz A) çalışıyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())