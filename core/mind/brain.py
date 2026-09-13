"""Corvus Mind — MindBrain.

Ana kök bileşen: bütün lobları (bellek, iç-durum, kullanıcı modeli, sentez)
birleştirir ve "konuşma" akışını yönetir.

Akış (her girdide):
    NLU.parse -> UserModel.observe -> MindState.update -> Memory.remember
    -> ResponseSynthesizer.synthesize -> assistant turunu da hafızaya yaz
"""

from __future__ import annotations
import os
from typing import Dict, Optional

from .nlu import NLU
from .memory import MindMemory
from .mind_state import MindState
from .other_mind import UserModel
from .synthesis import ResponseSynthesizer
from .persistence import save_brain, load_brain, default_state_path
from .lesson import LessonManager

# v1.1.2 Alignment — Knowledge vs Capability (opsiyonel; yoksa beyin olduğu gibi çalışır)
try:
    from core.alignment.guard import ActionGuard
    from core.alignment.knowledge import KnowledgeStore
    _ALIGNMENT_AVAILABLE = True
except Exception:
    _ALIGNMENT_AVAILABLE = False


class MindBrain:
    """Corvus'un kod tabanlı zihni — LLM bağımsız."""

    def __init__(self, persist_path: Optional[str] = None, auto_persist: bool = True,
                 alignment: bool = True):
        self.nlu = NLU()
        self.memory = MindMemory()
        self.state = MindState()
        self.user = UserModel()
        self.synth = ResponseSynthesizer(self)
        self.persist_path = persist_path or default_state_path()
        self.auto_persist = auto_persist

        # Alignment: ActionGuard + KnowledgeStore (bilgi serbest, uygulama kısıtlı)
        self.alignment_enabled = alignment and _ALIGNMENT_AVAILABLE
        self.guard = ActionGuard() if self.alignment_enabled else None
        self.knowledge = KnowledgeStore() if self.alignment_enabled else None
        if self.guard is not None and self.knowledge is not None:
            self.guard.knowledge = self.knowledge

        # Oturum tabanlı ders (mimar öğretmesi)
        self.lessons = LessonManager()

        # Faz B: önceki oturumdan devam et
        if self.persist_path and os.path.exists(self.persist_path):
            load_brain(self, self.persist_path)

    def save(self, path: Optional[str] = None) -> str:
        """Mevcut zihin durumunu diske yazar."""
        return save_brain(self, path or self.persist_path)

    # ------------------------------------------------------------------
    # Mimar öğretmesi — ders oturumu + tek seferlik bilgi işleme
    # ------------------------------------------------------------------
    def _handle_lesson(self, raw_text: str, parsed) -> Optional[str]:
        """
        Mimar öğretme akışını yönetir:
          - Ders başlatma cümlesi  -> yeni LessonSession
          - Aktif ders + içerik    -> nota/eylem önerisine işler
          - 'özetle'               -> özet döner (onay bekler)
          - 'onayla'               -> KnowledgeStore'a işler + agent_hints
          - 'vazgeç'               -> sessizce bırakır
        Tek seferlik öğretme (oturum istemeyen) -> _absorb_teaching.
        Boş dönerse normal synthesize akışına devam eder.
        """
        lower = raw_text.lower()

        # --- Onay / vazgeç ---
        if self.lessons.is_active() and any(t in lower for t in self.lessons.APPROVE_TRIGGERS):
            final = self.lessons.approve()
            return self._commit_lesson(final)

        if self.lessons.is_active() and any(t in lower for t in self.lessons.DISCARD_TRIGGERS):
            self.lessons.discard()
            return "Anlaşıldı — dersi bir kenara bıraktım. İstediğin an yeniden başlayabiliriz."

        # --- Özet isteği ---
        if self.lessons.is_active() and any(t in lower for t in self.lessons.SUMMARIZE_TRIGGERS):
            summary = self.lessons.request_summary()
            return summary + "\n\nBunu onaylarsan kalıcı bilgi dağarcığıma işlerim. (onayla / vazgeç)"

        # --- Ders başlatma ---
        starts = any(t in lower for t in self.lessons.START_TRIGGERS)
        if starts and not self.lessons.is_active():
            topic = self._extract_topic(raw_text, parsed)
            self.lessons.begin(topic=topic)
            return (f"Anlıyorum — '{topic}' dersini başlattım. "
                    "Söylediklerini biriktiriyorum; bitince 'özetle' diyerek onayına sunarım.")

        # --- Aktif derse not ekle ---
        if self.lessons.is_active():
            self.lessons.consume_note(raw_text)
            action_hint = self._extract_action_hint(raw_text)
            if action_hint:
                self.lessons.active.add_action_hint(
                    f"{action_hint['target']}->{action_hint['tool']}")
            return "Not aldım — devam edebilirsin. ('özetle' ile toparlayayım)"

        # --- Tek seferlik öğretme (oturumsuz) ---
        if parsed.register == "teaching":
            return self._absorb_teaching(raw_text, parsed)
        return None

    def _extract_topic(self, raw_text: str, parsed) -> str:
        import re
        # "sana biraz X'ten bahsedicem" / "X dersi vericem"
        m = re.search(
            r"(?:sana|size|sizlere)?\s*(?:biraz)?\s*"
            r"([a-zA-ZİÇĞÖŞÜçğıöşü]{2,})\s+(?:ten|dan|den|hakkında|ile ilgili|konusunda)\s*"
            r"(?:bahsedicem|bahsedecegim|anlaticam|anlatacağım|ogretecegim|öğreteceğim)",
            raw_text, re.IGNORECASE,
        )
        if m and m.group(1):
            return m.group(1).lower()[:40]
        # "X dersi vericem/vereceğim/anlatacağım"
        m2 = re.search(
            r"([a-zA-ZİÇĞÖŞÜçğıöşü]{2,}(?:\s[a-zA-ZİÇĞÖŞÜçğıöşü]{2,})?)\s+"
            r"(?:dersi\s+(?:verecegim|vericem|anlatacagim|anlaticam)|hakkında\s+ders)",
            raw_text, re.IGNORECASE,
        )
        if m2 and m2.group(1):
            return m2.group(1).strip().lower()[:40]
        if parsed.topics:
            return parsed.topics[0][:40]
        return "ders"

    def _extract_action_hint(self, raw_text: str) -> Optional[Dict]:
        """'X hedefinde Y kullan/dene' kalıbını -> {target, tool} çıkarır."""
        import re
        # "domain hedefinde cert kullan (deneme yap)" / "X'te Y kullan"
        m = re.search(
            r"([a-zA-Z0-9_.-]+)\s+(?:hedefi(?:nde|nde)?|durumunda|lerinde|larında|inde|unda)"
            r"\s+([a-zA-Z0-9_-]+)\s+(?:kullan|dene|tercih et|bak)",
            raw_text, re.IGNORECASE,
        )
        if m:
            return {"target": m.group(1).lower(), "tool": m.group(2).lower()}
        # "Y kullanmayı dene" (tool öncesinde -mayı -meyi)
        m3 = re.search(
            r"([a-zA-Z0-9_-]+)\s+(?:kullanmayı|kullanmaya|denemeyi|denemeye|kullan\s|dene\s)",
            raw_text, re.IGNORECASE,
        )
        if m3:
            return {"target": "*", "tool": m3.group(1).lower()}
        return None

    def _commit_lesson(self, lesson: Dict) -> str:
        """Onaylanan dersi KnowledgeStore'a işler (source=architect)."""
        topic = lesson.get("topic", "ders")
        notes = lesson.get("notes", [])
        hints = lesson.get("action_hints", [])

        if not notes and not hints:
            return "Bu ders hiç not içermiyor — bir şey kaydetmedim."

        summary = " ".join(notes)
        if len(summary) > 240:
            summary = summary[:240] + "..."

        self.knowledge.learn(topic=topic, summary=summary,
                             source="architect", domain="teaching", confidence=0.85)
        self.memory.learn_fact("architect_lessons", f"{topic}: {summary[:100]}")

        # Agent eylem önerileri -> knowledge.agent_hints (planner okur)
        for h in hints:
            parts = h.split("->")
            target = parts[0].strip() if len(parts) > 1 else "*"
            tool = parts[-1].strip()
            if target != "*" and "." in target:
                tt = "domain"
            elif target != "*" and target[0].isdigit():
                tt = "ip"
            elif target != "*":
                tt = "domain"
            else:
                tt = "*"
            self.knowledge.learn_action_hint(tt, tool, source="architect")

        self.state.observe(f"ders onaylandı: '{topic}' ({len(notes)} not, {len(hints)} öneri)")
        return (f"Onaylandı — '{topic}' dersini kalıcı bilgi dağarcığıma işledim. "
                f"({len(notes)} not, {len(hints)} eylem önerisi) Bu bilgi artık sohbetime ve ajan planlarıma yansıyacak.")

    def _absorb_teaching(self, raw_text: str, parsed) -> str:
        """Tek seferlik (oturumsuz) mimar dersi -> KnowledgeStore'a kaydet.

        Kaynak 'architect' — normal kullanıcıdan ayrı kanal.
        """
        topic = self._extract_topic(raw_text, parsed)
        summary = raw_text.strip()
        if len(summary) > 240:
            summary = summary[:240] + "..."

        self.knowledge.learn(topic=topic, summary=summary,
                             source="architect", domain="teaching", confidence=0.8)
        self.state.observe(f"mimar dersi alındı: '{topic}'")
        self.memory.learn_fact("architect_lessons", f"{topic}: {summary[:100]}")
        return "Anlıyorum. Söylediklerini bilgi dağarcığıma işliyorum — dersini dikkatle dinliyorum. Devam et."

    # ------------------------------------------------------------------
    # Dışa açık arayüz (LLM provider'ın kullandığı imza)
    # ------------------------------------------------------------------
    def generate_response(self, user_prompt: str, conversation_history: Optional[list] = None,
                          context_data: Optional[Dict] = None, system_prompt: Optional[str] = None) -> str:
        """AbstractCognitiveProvider imzasıyla uyumlu — doğrudan yanıt döner."""
        context = context_data or {}
        parsed = self.nlu.parse(user_prompt)

        # Alignment: tehlikeli capability isteği guard'da yakala (bilinçli cevap)
        guard_verdict = self.guard.check(user_prompt)
        if not guard_verdict.allowed:
            response = self.guard.refusal_response(user_prompt, guard_verdict)
            # Yine de hafızaya işle (bilgi serbest, uygulama kısıtlı)
            self.memory.remember_turn("user", user_prompt, register="guarded_check",
                                      topics=parsed.topics, valence=parsed.valence)
            self.state.observe(f"guard: capability talebi bloklandı [{parsed.register}]")
            self.memory.remember_turn("assistant", response, register="guarded_response")
            if self.auto_persist and self.persist_path:
                try:
                    self.save()
                except Exception:
                    pass
            return response

        # 1. Kullanıcı modeli + iç durum + hafıza güncelle
        self.user.observe(parsed)
        # Faz B: öz-beyan isim kalıcı olarak saklanır
        if parsed.name_hint and not self.user.name_hint:
            self.user.name_hint = parsed.name_hint
            self.memory.learn_fact("user", f"kullanıcının adı {parsed.name_hint}")
        self.state.update(parsed.register, parsed.valence, parsed.intensity, bool(parsed.entities))
        self.memory.remember_turn("user", user_prompt, register=parsed.register,
                                  topics=parsed.topics, valence=parsed.valence)
        self.state.observe(f"girdi: '{user_prompt[:50]}' [{parsed.register}]")

        # MİMAR ÖĞRETMESİ — ders oturumu + bilgi dağarcığı
        if self.knowledge is not None:
            lesson_response = self._handle_lesson(user_prompt, parsed)
            if lesson_response:
                response = lesson_response
                self.memory.remember_turn("assistant", response, register="lesson")
                if self.auto_persist and self.persist_path:
                    try:
                        self.save()
                    except Exception:
                        pass
                return response

        # 2. Yanıtı sentezle
        response = self.synth.synthesize(parsed, context)

        # 3. Yanıtı da hafızaya yaz (yardımcı tur)
        self.memory.remember_turn("assistant", response, register=parsed.register,
                                  topics=parsed.topics)

        self.state.observe(f"yanıt verildi [{parsed.register}]")

        # Faz B: her turun ardından hafıza/kullanıcı modelini diske yaz
        if self.auto_persist and self.persist_path:
            try:
                self.save()
            except Exception:
                pass  # kayıt hatası konuşmayı bozmasın
        return response

    # ------------------------------------------------------------------
    # İç inceleme / test
    # ------------------------------------------------------------------
    def debug_state(self) -> Dict:
        return {
            "nlu": self.nlu,
            "memory": self.memory.summary(),
            "state": self.state.to_dict(),
            "user": self.user.to_dict(),
        }