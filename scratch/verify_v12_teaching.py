# -*- coding: utf-8 -*-
"""Corvus v1.1.2+ — Mimar Öğretmesi + Knowledge Recall + Chat Oto-Agent doğrulama.

Senaryolar:
  1. Mimar "sana Sokrates'ten bahsedeceğim..." dersi verir -> KnowledgeStore'a kaydedilir
  2. Kaynak 'architect' olarak işaretlenir (normal kullanıcıdan ayrı)
  3. "sokrates kimdir" sorgusu -> öğretilen bilgiyi konuşmaya katar (recall)
  4. "example.com araştır" -> chat, agent'ı OTOMATİK tetikler
"""
import os
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


def main():
    from core.mind.brain import MindBrain
    from core.context import ContextManager
    from modules.chat import ChatModule

    print("=" * 70)
    print("v1.1.2+ — MİMAR ÖĞRETMESİ & KNOWLEDGE RECALL & OTO-AGENT")
    print("=" * 70)

    tmp = tempfile.mkdtemp(prefix="corvus_teach_")
    brain = MindBrain(persist_path=os.path.join(tmp, "mind.json"), auto_persist=True)

    # 1. Mimar dersi
    print("\n[1] MİMAR DERSİ")
    r = brain.generate_response(
        "naber bugün sana biraz sokrates ten bahsedicem, "
        "behavioral profiling yaparken insanları daha iyi anla",
        [], {},
    )
    print("  cevap:", r[:70])
    assert "anlıyorum" in r.lower() or "işliyorum" in r.lower(), f"kabul cevabı bekleniyor: {r[:60]}"

    # 2. Bilgi dağarcığı + kaynak ayrımı
    print("\n[2] BİLGİ DAĞARCIĞI + MİMAR AYRIMI")
    entry = brain.knowledge.get("sokrates")
    print("  topicalar:", list(brain.knowledge.facts.keys()))
    print("  sokrates kaynak:", entry["source"] if entry else "YOK")
    assert entry and entry["source"] == "architect", "sokrates bilgisi architect olarak kaydedilmeli"

    # 3. Knowledge recall (öğretilen bilgi konuşmaya katılır)
    print("\n[3] KNOWLEDGE RECALL")
    r2 = brain.generate_response("sokrates kimdir", [], {})
    print("  cevap:", r2[:150])
    assert "öğretildi" in r2 or "taught" in r2.lower(), "recall bilgiyi konuşmaya katmalı"

    # 4. Chat oto-agent
    print("\n[4] CHAT OTO-AGENT (example.com araştır)")
    ctx = ContextManager()
    mod = ChatModule(target=["example.com", "araştır"], config={}, context=ctx)
    mod._ask_approval = lambda q: True  # test için otomatik onay
    res = mod.execute()
    d = res["data"]
    print("  suggested:", d.get("suggested_command"))
    print("  auto_action yürütüldü:", (d.get("auto_action") or {}).get("executed"))
    assert d.get("suggested_command") == "agent example.com", "doğal dil -> agent komutu"
    assert d.get("auto_action") and d["auto_action"].get("executed"), "agent otomatik çalışmalı"

    print("\n" + "-" * 70)
    print("OK — Mimar öğretmesi, knowledge recall ve chat oto-agent çalışıyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())