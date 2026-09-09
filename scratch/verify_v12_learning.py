# -*- coding: utf-8 -*-
"""Corvus Self-Learning Layer (v1.1.2) doğrulama.

Senaryolar (kullanıcının vizyonundan):
  1. "social gizli hesap hatası" -> FailureLearning alternatif önerir + kaydeder
  2. Kullanıcı geri bildirimi "dns yerine cert kullansaydın" -> deneyime işlenir
  3. Calibration + ExperienceBasedSelection arac sırasını değiştirir
  4. Audit Log her değişikliği kaydeder (mimar raporu)
"""
import os
import sys
import tempfile

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)


def main():
    tmp = tempfile.mkdtemp(prefix="corvus_learning_")
    exp_path = os.path.join(tmp, "experience.json")
    audit_path = os.path.join(tmp, "audit.jsonl")

    from core.learning.experience import ExperienceStore
    from core.learning.feedback import FeedbackLoop
    from core.learning.calibration import CalibrationEngine
    from core.learning.selection import ExperienceBasedSelection
    from core.learning.patterns import PatternLearning
    from core.learning.self_learn import FailureLearner
    from core.learning.audit import AuditLog

    print("=" * 70)
    print("v1.1.2 — SELF-LEARNING LAYER DOĞRULAMA")
    print("=" * 70)

    store = ExperienceStore(path=exp_path)
    feedback = FeedbackLoop(store)
    cal = CalibrationEngine(store)
    patterns = PatternLearning(store)
    learner = FailureLearner(store, patterns)
    audit = AuditLog(path=audit_path)
    selection = ExperienceBasedSelection(store, cal)

    # ---- 1. Failure Learning: sosyal araç gizli hesaba çarptı ----
    print("\n[1] BAŞARISIZLIKTAN ÖĞRENME (privacy_wall)")
    for i in range(2):  # 2 kez tekrarlansın ki desen olgunlaşsın
        res = learner.learn_from_failure(
            tool="social", target_type="person",
            error_type="privacy_wall",
            summary=f"Instagram hesabı gizli — {i+1}. deneme",
            context_keywords=["instagram", "private"],
        )
        audit.log_experience("social", "error", "person", "privacy_wall", res["alternatives_suggested"])
    print("  önerilen alternatifler:", res["alternatives_suggested"])
    mature = patterns.mature_patterns()
    print("  olgunlaşmış desenler:", [(p.tool, p.error_type, p.count) for p in mature])
    assert res["alternatives_suggested"], "alternatif önerisi boş olmamalı"
    assert len(mature) >= 1, "desen öğrenilmeli"

    # ---- 2. Kullanıcı geri bildirimi ----
    print("\n[2] KULLANICI GERİ BİLDİRİMİ")
    learned = feedback.ingest_user_feedback(
        "bu sonuç beni tatmin etmedi, dns yerine cert kullansaydın",
        target_tool="dns", target_type="domain", target="example.com",
    )
    audit.log_feedback("dns", 1, "dns yerine cert kullansaydın", "cert")
    print("  geri bildirim kaydı:", learned.user_note if learned else "YOK")
    assert learned, "geri bildirim deneyime işlenmeli"

    # ---- 3. Bazı başarılar da ekle (kalibrasyon için) ----
    print("\n[3] BAŞARILARDAN ÖĞRENME + KALİBRASYON")
    cert_ok = learner.learn_from_success("cert", "domain", new_entities=5, summary="sertifika CT logu başarılı")
    audit.log_calibration("cert", 1.0, cal.calibrate("cert"))
    cert_ok = learner.learn_from_success("cert", "domain", new_entities=8, summary="başka sertifika")
    audit.log_calibration("cert", 1.0, cal.calibrate("cert"))
    cert_ok = learner.learn_from_success("cert", "domain", new_entities=6, summary="üçüncü sertifika başarısı")
    audit.log_calibration("cert", 1.0, cal.calibrate("cert"))
    dns_ok = learner.learn_from_success("dns", "domain", new_entities=2, summary="DNS kaydı")
    print("  cert ağırlık:", cal.weight("cert"), "| cert çağrı:", store.stats("cert")["calls"])
    assert cal.weight("cert") > 1.0, "başarılı araç ağırlığı artmalı"
    assert store.stats("dns")["calls"] >= 1, "dns deneyimi kaydedilmeli"

    # ---- 4. Deneyim tabanlı araç seçimi ----
    print("\n[4] DENEYİM TABANLI ARAÇ SEÇİMİ")
    planner_order = ["dns", "cert", "whois", "tech"]  # planner'ın varsayılan sırası
    reordered = selection.reorder(planner_order, "domain")
    print("  planner sırası:  ", planner_order)
    print("  öğrenilmiş sıra:", reordered)
    audit.log_selection("domain", planner_order, reordered)
    # cert başarılı ve ağırlığı yüksek -> dns'ten öne geçmeli
    assert reordered.index("cert") < reordered.index("dns"), "cert, dns'ten öne geçmeli"

    # ---- 5. Audit ----
    print("\n[5] AUDIT RAPORU")
    recent = audit.recent(limit=10)
    print("  son audit kaydı sayısı:", len(recent))
    by_type = audit.summary()["by_type"]
    print("  türlere göre:", by_type)
    assert len(recent) >= 5, "audit en az 5 kayıt içermeli"
    for r in recent[:3]:
        print("   -", r.get("type"), "|", r.get("tool", ""), "|", r.get("change", r.get("status", "")))

    print("\n" + "-" * 70)
    print("OK — v1.1.2 Self-Learning katmanı çalışıyor.")
    print("    Deneyim dosyası:", exp_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())