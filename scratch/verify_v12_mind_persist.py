# -*- coding: utf-8 -*-
"""Corvus Mind v1.2 Faz B — Kalıcı hafıza doğrulama.

1. Bir oturum: 'benim adım ahmet', 'anlam nedir', 'merhaba' konuş
2. Yeni oturum (yeni instance): 'ben kimim' sor — önceki oturumun
   hafızasından gerçek cevap gelsin; 'merhaba' -> kullanıcı adını bilsin.
"""
import os
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.mind.brain import MindBrain


def main():
    print("=" * 70)
    print("CORVUS MIND v1.2 (Faz B) — Kalıcı Hafıza Doğrulama")
    print("=" * 70)

    path = os.path.join(tempfile.gettempdir(), "corvus_mind_test.json")
    if os.path.exists(path):
        os.remove(path)

    ctx = {"entities": {}, "relations": []}

    # ---- Oturum 1: konuş ve kaydet ----
    print("\n[OTURUM 1]")
    brain1 = MindBrain(persist_path=path)
    print("  U: benim adım ahmet")
    print("  C:", brain1.generate_response("benim adım ahmet", [], ctx)[:90])
    brain1.generate_response("anlam nedir", [], ctx)
    brain1.generate_response("example.com araştır", [], ctx)
    brain1.save()
    assert os.path.exists(path), "kayıt dosyası oluşmadı"

    print("[1] disk'e yazıldı:", path)
    print("    tur sayısı:", brain1.memory.turn_no)

    # ---- Oturum 2: yeni instance ile yükle ----
    print("\n[OTURUM 2] (yeni instance)")
    brain2 = MindBrain(persist_path=path)
    print("  yüklenen tur:", brain2.memory.turn_no, "| aktif konular:", brain2.memory.all_user_topics())

    r = brain2.generate_response("ben kimim", [], ctx)
    print("  U: ben kimim")
    print("  C:", r)
    assert "ahmet" in r or "profiline" in r.lower(), f"hafıza uzandı ama isim yansımadı: {r[:80]}"

    r2 = brain2.generate_response("merhaba", [], ctx)
    print("  U: merhaba")
    print("  C:", r2)
    assert "ahmet" in r2.lower(), f"selam isimle olmalı: {r2[:80]}"

    # ---- Temizlik ----
    os.remove(path)
    print("\n" + "-" * 70)
    print("OK — Kalıcı hafıza çalışıyor (oturumlar arası).")
    return 0


if __name__ == "__main__":
    sys.exit(main())