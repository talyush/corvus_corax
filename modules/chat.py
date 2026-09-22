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

        Tetikleyiciler: 'kimdir/arastir/incele' + bir ISIM/HEDEF (>=2 kelime).
        "socrates kimdir" gibi tek-isim bilgi sorusu LLM'de kalir (modul yok),
        ama "Ahmet Yilmaz kimdir arastir" gibi hedef iceren sorgularda
        moduller gercel kanit toplar, LLM harmanlar.
        """
        lower = user_message.lower()
        is_targeted = any(k in lower for k in ("kimdir", "arastir", "incele",
                                               "hakkinda arastir", "profili", "hakkinda bilgi",
                                               "bul", "kim bu"))
        if not is_targeted:
            return None

        import re
        # "Talha Bağcı" gibi Ad+Soyad'ı yakala (kimdir/araştır öncesi)
        mg = re.search(r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+)", user_message)
        if not mg:
            mg = re.search(r"(\w+\.\w+)", lower)  # domain/ip hedefleri
        if not mg or not mg.group(1):
            return None

        target = mg.group(1).strip()
        # Cümle içinde "kimdir/araştır" gibi kelimeler hedefe sızmasın
        for word in ("kimdir", "kim", "araştır", "arastir", "incele", "bul", "hakkında",
                     "profili", "ve", "arasında"):
            target = target.replace(" " + word, "").replace(word + " ", "")
        target = target.strip()
        if len(target) < 2 or target.lower() in ("corvus corax", "the machine"):
            return None
        # Tek kelimelik bilgi sorusu -> LLM'de kalsin
        if " " not in target:
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