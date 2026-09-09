"""Corvus Self-Learning — Feedback Loop.

Kullanıcı geri bildirimi ("şunu yapsaydın", "bu işe yaramadı") ve iç gözlem
(self-feedback) kanallarını Experience Store'a bağlar.

Doğal dil geri bildirimini yakalar ve YAPISAL öğrenmeye çevirir:
  1. Kullanıcı "valuesiz sonuç, x kullan" derse -> deneyim üzerine uygula
  2. Bu, sonraki tool selection / calibration güncellemesi için kayıt oluşturur
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional

from .experience import ExperienceStore, Experience


class FeedbackLoop:
    """Kullanıcı ve iç geri bildirimden öğrenme kanalı."""

    def __init__(self, store: ExperienceStore):
        self.store = store
        # "şunu yapsaydın / şunu kullansaydın / beni tatmin etmedi" kalıpları
        self._suggestion_re = re.compile(
            r"(?:yapsaydın|yapmalıydın|yapsan|kullansaydın|kullanmalıydın|kullansan|"
            r"deneseydin|şunu kullan|use\s+\w+|try\s+\w+)",
            re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Kullanıcı geri bildirimi
    # ------------------------------------------------------------------
    def ingest_user_feedback(self, text: str, target_tool: str = "", target_type: str = "unknown",
                             target: str = "") -> Optional[Experience]:
        """
        'whis's falan işe yaramadı; dns kullansaydın' gibi doğal dil bildirimi alır.
        Son deneyime kullanıcı notu ve memnuniyet ekler; öneriyi öğrenme kaynağı yapar.
        """
        text_l = text.lower()
        satisfaction = None
        if any(w in text_l for w in ("tatmin etmedi", "işe yaramadı", "berbat", "kötü", "olmamış",
                                     "didn't work", "failed", "useless", "bad")):
            satisfaction = 1
        elif any(w in text_l for w in ("süper", "harika", "mükemmel", "iyi iş", "teşekkür",
                                       "great", "awesome", "good", "thanks", "nice")):
            satisfaction = 5
        elif "böyle olabilir" in text_l or "şöyle yap" in text_l:
            satisfaction = 3

        # Önerilen aracı ("... kullansaydın X") çıkar
        suggested_tool = self._extract_suggested_tool(text)

        # Hedef deneyim: en son kullanıcı şikayet ettiği aracın kaydı
        if not target_tool:
            # İstatistiklere göre en çok hata yapanlardan birini seç
            failed = [e for e in reversed(self.store.experiences) if e.status == "error"]
            if failed:
                target_tool = failed[0].tool
            else:
                return None

        exp = self.store.most_recent(target_tool, limit=1)
        if exp:
            record = exp[0]
            record.user_satisfaction = satisfaction
            record.user_note = text[:200]
            if suggested_tool:
                record.alternatives = [suggested_tool] + record.alternatives
        else:
            # Yeni (geçmişe ait) kayıt
            record = self.store.record(
                tool=target_tool, target_type=target_type, target=target,
                status="error", error_type="user_feedback",
                summary=f"kullanıcı geri bildirimi: {text[:120]}",
                alternatives=[suggested_tool] if suggested_tool else [],
            )
            record.user_satisfaction = satisfaction
            record.user_note = text[:200]

        try:
            self.store.save()
        except Exception:
            pass
        return record

    def _extract_suggested_tool(self, text: str) -> Optional[str]:
        """'dns kullansaydın' gibi bir ifadeden aracı çıkarır."""
        known = [
            "whois", "dns", "tech", "cert", "metadata", "footprint", "crawl", "wayback",
            "geoip", "asn", "scan", "netscan", "social", "github", "academic", "org",
            "breach", "phone", "wallet", "resolve", "evidence", "nexus", "pivot", "pol",
            "discover", "geoint", "subdomain", "headers", "email",
        ]
        for tool in known:
            if tool in text.lower():
                return tool
        return None

    # ------------------------------------------------------------------
    # İç geri bildirim (self-feedback) — doğrudan kayıt
    # ------------------------------------------------------------------
    def self_feedback(self, tool: str, satisfaction: int, note: str = "",
                      target_type: str = "unknown", target: str = "") -> Experience:
        """Corvus kendi değerlendirmesini deneyime işler (başarısını ölçer)."""
        record = self.store.record(
            tool=tool, target_type=target_type, target=target,
            status="success" if satisfaction >= 3 else "error",
            error_type="self_feedback" if satisfaction < 3 else "",
            summary=note[:150],
        )
        record.user_satisfaction = satisfaction
        record.user_note = note[:200]
        try:
            self.store.save()
        except Exception:
            pass
        return record