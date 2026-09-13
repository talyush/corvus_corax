"""Corvus Mind — Oturum Tabanlı Ders (LessonSession).

Mimar (architect) birden çok turda ders verebilir:
  1. Mimar: "sana Sokrates'ten bahsedeceğim"   -> ders oturumu başlar
  2. Mimar: "Sokrates şöyle düşünürdü..."       -> not birikir
  3. Mimar: "arayüzünde X kullan"               -> agent önerisi birikir
  4. Corvus: "özetle" isteyince özet çıkarır    -> mimar onaylar
  5. Onaylanınca KnowledgeStore'a işlenir (source=architect)

Ders sözleşmesi:
  - Kaynak her zaman 'architect' — normal kullanıcıdan ayrı.
  - Ders, eylem önerileri içerebilir -> KnowledgeStore.agent_hints'a yazılır,
    böylece Agent Layer (planner) bunları plana koyabilir.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LessonSession:
    """Tek bir çok turlu ders oturumu."""

    topic: str = ""
    notes: List[str] = field(default_factory=list)
    action_hints: List[str] = field(default_factory=list)  # "domain'de cert dene" gibi
    started_at: str = ""
    status: str = "active"   # active | summarizing | approved | discarded

    def add_note(self, note: str) -> None:
        if note and note not in self.notes:
            self.notes.append(note.strip())

    def add_action_hint(self, hint: str) -> None:
        if hint and hint not in self.action_hints:
            self.action_hints.append(hint.strip())

    def summarize(self) -> str:
        head = f"DERS ÖZETİ — {self.topic}"
        body = "\n".join(f"  - {n}" for n in self.notes)
        if self.action_hints:
            body += "\nEYLEM ÖNERİLERİ (agent planını etkileyecek):"
            body += "\n".join(f"  * {h}" for h in self.action_hints)
        return f"{head}\n{body}"

    def mark_approved(self) -> None:
        self.status = "approved"

    def mark_discarded(self) -> None:
        self.status = "discarded"

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "notes": list(self.notes),
            "action_hints": list(self.action_hints),
            "started_at": self.started_at,
            "status": self.status,
        }


class LessonManager:
    """Ders oturumlarının hayat döngüsünü yönetir (oturum başına tek aktif ders)."""

    # "ders bitti/özetle/onayla/kaydet" gibi komutlar
    START_TRIGGERS = (
        "bahsedecegim", "bahsedicem", "anlatacagim", "anlaticam",
        "öğreteceğim", "öğreticem", "ders", "not al", "ogret",
    )
    SUMMARIZE_TRIGGERS = (
        "özetle", "ozetle", "ders bitti", "özet çıkar", "summary", "end lesson",
        "özeti al", "kaydet", "kaydet ve özetle",
    )
    APPROVE_TRIGGERS = (
        "onayla", "onaylıyorum", "evet onayla", "approved", "onay",
        "yayınla", "işaretle",
    )
    DISCARD_TRIGGERS = (
        "boş ver", "vazgeç", "sil", "discard", "iptal", "at gitsin",
    )

    def __init__(self):
        self.active: Optional[LessonSession] = None
        self.completed: List[LessonSession] = []

    # ------------------------------------------------------------------
    def is_active(self) -> bool:
        """Ders aktif/özet-bekliyor durumda mı? (onay akışı da dahil)"""
        return self.active is not None and self.active.status in ("active", "summarizing")

    def begin(self, topic: str = "ders") -> LessonSession:
        """Yeni ders oturumu başlatır (varsa eskiyi tamamlar)."""
        from datetime import datetime, timezone
        session = LessonSession(
            topic=topic.strip().lower()[:40] or "ders",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.active = session
        return session

    def consume_note(self, text: str) -> bool:
        """Aktif ders varsa not/eylem önerisi olarak işler. True döner."""
        if not self.is_active():
            return False
        # Eylem önerisi yakala: "X'te/kullanımında Y kullan/dene" kalıpları
        import re
        hint = None
        m = re.search(
            r"(?:hedef(?:ler)?(?:inde|de)?|durum(?:lar)?(?:da|unda)?|'de|kullanırken)\s*"
            r"([a-zA-Z0-9_.-]+)\s+(?:da|de|leri|lerde|larında)\s*(?:kullan|dene|tercih et|bak)\s*"
            r"([a-zA-Z0-9_-]+)",
            text, re.IGNORECASE,
        )
        # Daha geniş: "... kullan", "... dene" gibi kısa komutlar
        m2 = re.search(r"(\w+)\s+(?:kullan|dene|kullanmalısın|denemelisin)\b", text, re.IGNORECASE)
        if m:
            hint = f"{m.group(1).lower()[:24]}->{m.group(2).lower()[:24]}"
        elif m2:
            hint = f"*->{m2.group(1).lower()[:24]}"

        if hint:
            self.active.add_action_hint(hint)
            return True

        # Genel not
        self.active.add_note(text)
        return True

    def request_summary(self) -> str:
        """Aktif dersi özetler; durumu 'summarizing' yapar."""
        if self.active is None:
            return "Aktif ders yok."
        self.active.status = "summarizing"
        return self.active.summarize()

    def approve(self) -> Dict:
        """Dersi onaylar: completed'a taşır, active temizler. False->None."""
        if self.active is None:
            return {}
        self.active.mark_approved()
        result = self.active.to_dict()
        self.completed.append(self.active)
        self.active = None
        return result

    def discard(self) -> None:
        """Dersi iptal eder."""
        if self.active is not None:
            self.active.mark_discarded()
            self.completed.append(self.active)
            self.active = None