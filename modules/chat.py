"""Corvus Corax v1.1.1+ - Cognitive Chat Module.

Interactive natural language conversation and intent-driven intelligence querying.
v1.1.2+: HYBRID RECON — "Talha Bagci kimdir arastir" gibi hedefli sorgularda
         OSINT modulleri gercek veri toplar, LLM bu kaniti + kendi bilgisini
         harmanlayarak cevap verir. "X arastir" da agent'i otomatik tetikler.
"""

from core.module_base import BaseModule
from core.cognitive.dialogue import CognitiveDialogueEngine


class ChatModule(BaseModule):
    """Cognitive Interface & Natural Language Chat Module."""

    name = "chat"

    _global_dialogue_engine = None

    @classmethod
    def get_engine(cls, context):
        if cls._global_dialogue_engine is None:
            cls._global_dialogue_engine = CognitiveDialogueEngine(context_manager=context)
        return cls._global_dialogue_engine

    def execute(self):
        args = self.target or []
        user_message = " ".join(args) if isinstance(args, list) else str(args)

        if not user_message.strip():
            user_message = "merhaba"

        inv = self.begin_investigation(
            "Cognitive Interface session",
            ["INTENT EXTRACTION", "HYBRID RECON", "COGNITIVE SYNTHESIS"]
        )
        engine = self.get_engine(self.context)

        with inv.phase(0):
            self.status_step("Analyzing natural language query and context memory")

        # HYBRID RECON: hedefli arastirma sorusu -> moduller + LLM birlestik
        hybrid = self._maybe_hybrid(user_message)
        if hybrid is not None:
            with inv.phase(1):
                self.status_step(f"Running hybrid recon for '{hybrid['target']}'")
            # v1.3.4: hybrid sonucunu MEMORY'ye isle — takip sorgulari aktif hedefi bilsin
            # ("talha sağırı araştır" -> "genel olarak bak" kopuklugu duzeltmesi)
            try:
                engine.memory.add_user_message(
                    user_message, intent="investigate", entities=[hybrid["target"]]
                )
                engine.memory.update_focal_target(
                    hybrid["target"], hybrid.get("target_type") or "person"
                )
                engine.memory.add_assistant_message(
                    hybrid["response"], metadata={"category": "hybrid_recon"}
                )
            except Exception:
                pass
            data = {
                "user_message": user_message,
                "response": hybrid["response"],
                "provider": hybrid["provenance"].get("provider_name"),
                "active_target": hybrid["target"],
                "hybrid_recon": True,
                "module_findings": hybrid["module_findings"],
                "observations": hybrid["observations"],
                "provenance": hybrid["provenance"],
                "suggested_command": None,
            }
            return self.success(target=user_message, data=data)

        with inv.phase(2):
            self.status_step(f"Engaging {engine.active_provider.provider_name}")
            chat_result = engine.chat(user_message)
            suggested = chat_result.get("suggested_command")

        # v1.1.2+: agent onerisi gelen komut OTOMATIK calistir (guvenli otonom)
        auto_action = None
        if suggested and suggested.startswith("agent "):
            with inv.phase(2):
                self.status_step(f"Auto-invoking {suggested}")
                try:
                    from core.agent.agent import Agent
                    from core.agent.policy import Approval
                    agent = Agent(
                        module_registry=self._load_modules(),
                        config=self.config,
                        logger=self.logger,
                        context=self.context,
                        approval_mode=Approval.ASK,
                        ask_callback=self._ask_approval,
                    )
                    target = suggested.split(" ", 1)[1]
                    auto_action = agent.investigate(target)
                except Exception as e:
                    auto_action = {"error": str(e), "summary": {"total_steps": 0}}

        data = {
            "user_message": user_message,
            "response": chat_result["response"],
            "intent": chat_result["intent"],
            "provider": chat_result["provider"],
            "active_target": chat_result["active_target"],
            "suggested_command": suggested,
            "auto_action": auto_action,
            "provenance": chat_result.get("provenance"),
        }
        return self.success(target=user_message, data=data)

    # ------------------------------------------------------------------
    def _maybe_hybrid(self, user_message: str):
        """Hedefli arastirma sorusu ise Hybrid Recon calistir.

        v1.3.4 — "havali konusuyor ama yapmiyor" duzeltmesi:
          - Turkce fiiller (araştır/arastir/incele/tara/hakkında...) artik ASCII
            karsiligiyla BERABER tetikler; "araştırırmısın" gibi cekimli/bitisik
            yazimlar da yakalanir (eski sadece 'arastir' seti asla eslesmiyordu).
          - Isim yakalama artik buyuk harf gerektirmez: fiilden ONCEKI kelimeler
            aday hedeftir ("talha sağırı araştırırmısın" -> "talha sağır").
          - Turkce ek soyma: "sağırı/sağırın" -> "sağır" (belirtme/iyelik).
          - Takip mesajlari (genel olarak bak/devam/ilk adımdan başla) onceki
            aktif hedefe devam eder — LLM'e dusup tekrar "ne yapayim?" demez.
        """
        lower = user_message.lower()
        # v1.3-1: HUMAN-CENTERED INTELLIGENCE sorguları HYBRID OSINT'e takılmamalı —
        # dialogue.py:163'teki human query setiyle birebir aynı küme (Görev #1 düzeltmesi).
        # "Alexander Vance için insan profili" gibi sorgular hybrid yerine
        # human_intelligence akışına gider (regex AD+SOYAD'ı yakalayıp OSINT'e
        # yönlendirmesin).
        if any(k in lower for k in (
            "insan profili", "yazım stili", "yazim stili", "stilometri", "stylometry",
            "aktivite saatleri", "ritim", "rhythm", "psikoloji", "persona",
            "davranış profili", "davranis profili", "aynı kişi mi", "ayni kisi mi",
            "aynı kişi olabilir mi", "insan analizi", "human profile", "human analysis",
            "human intelligence", "insan istihbarat"
        )):
            return None

        # Aktif hedef (onceki turdan) — takip sorgularinda devam icin
        active_target = None
        try:
            active_target = self.get_engine(self.context).memory.active_target
        except Exception:
            active_target = None

        # Turkce + ASCII tetikleyiciler birlikte (cekimli/bitisik fiil formlari dahil)
        is_targeted = any(k in lower for k in (
            "araştır", "arastir", "incele", "tara", "kimdir", "kim bu", "kim olduğunu",
            "kim oldugunu", "hakkında", "hakkinda", "hakkında bilgi", "hakkinda bilgi",
            "bilgi topla", "bilgi ver", "profili", "bul", "öğren", "ogren", "keşfet",
            "kesfet", "araştırma", "arastirma", "investigate", "search", "recon",
            "osint", "footprint", "whois", "dns", "find", "check", "scan", "lookup",
        ))

        # Takip/onay cumleleri: aktif hedef varsa "bak/devam/başla/tamam" -> oyle calisir
        is_followup = bool(active_target) and any(k in lower for k in (
            "devam", "bak", "başla", "basla", "tamam", "evet", "olur", "yap",
            "sadece", "ilk adım", "ilk adim", "maddeden", "kaynaklara", "adım", "adim",
            "genel", "soru", "sorular", "sen", "umarım", "göster", "goster",
        ))

        if not (is_targeted or is_followup):
            return None

        import re
        target = None

        # 1) Oncelik: Ad+Soyad (buyuk harf formatli, orijinal haliyle)
        mg = re.search(r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)", user_message)
        if mg:
            target = mg.group(1).strip()

        # 2) Buyuk harf yoksa: fiilden ONCEKI kelimeleri aday yap (kucuk harf toleransi)
        if not target:
            verb_m = re.search(
                r"(araştır|arastir|incele|tara|kimdir|kim bu|kim olduğunu|kim oldugunu|"
                r"hakkında|hakkinda|bilgi|profili|bul|öğren|ogren|keşfet|kesfet|"
                r"investigate|search|recon|find|lookup)",
                lower,
            )
            if verb_m:
                pre = lower[: verb_m.start()].strip()
                words = [w for w in re.split(r"[\s,.;:!?()\"'-]+", pre) if w]
                # "x için y araştır" gibi yapilarda sondan onceki isim parcasini tercih et
                if len(words) >= 2:
                    target = " ".join(words[-2:])
                elif words:
                    target = words[-1]
                # Turkce ek soyma: son kelimedeki belirtme/iyelik eki (sagiri -> sagir)
                if target:
                    parts = target.rsplit(" ", 1)
                    head, last = (parts[0], parts[1]) if len(parts) == 2 else ("", parts[0])
                    for suf in ("ları", "leri", "sı", "si", "yı", "yi", "ın", "in",
                                "un", "ün", "ı", "i", "u", "ü"):
                        if len(last) > len(suf) + 2 and last.endswith(suf):
                            last = last[: -len(suf)]
                            break
                    target = (head + " " + last).strip() if head else last

        # 3) Hecele bulunamadi ama aktif hedef varsa devam et (takip sorgusu)
        if not target and active_target:
            target = active_target

        if not target:
            target = active_target or None

        # Filtreler: tek kelime bilgi sorusu LLM'de kalir, Corvus'un kendisi hedef degil
        if not target or len(target) < 2 or target.lower() in ("corvus corax", "the machine"):
            return None
        if " " not in target and not active_target:
            return None

        try:
            from core.cognitive.hybrid import HybridRecon
            hybrid = HybridRecon(
                module_registry=self._load_modules(),
                config=self.config,
                logger=self.logger,
                context=self.context,
            )
            return hybrid.pursue(user_message, target=target)
        except Exception as e:
            return {"target": target, "response": f"Hibrit arastirma sirasinda sorun: {e}",
                    "provenance": {}, "module_findings": "", "observations": []}

    def _load_modules(self):
        from core.loader import load_modules
        return load_modules()

    def _ask_approval(self, question):
        """Interaktif onay: ag cagrisi yapan araclar icin kullaniciya sor."""
        try:
            answer = input(question + " (e/h): ").strip().lower()
            return answer in ("e", "evet", "yes", "y", "1")
        except Exception:
            return False

        data = {
            "user_message": user_message,
            "response": chat_result["response"],
            "intent": chat_result["intent"],
            "provider": chat_result["provider"],
            "active_target": chat_result["active_target"],
            "suggested_command": suggested,
            "auto_action": auto_action,
            "provenance": chat_result.get("provenance"),
        }
        return self.success(target=user_message, data=data)