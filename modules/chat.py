"""Corvus Corax v1.1.1+ - Cognitive Chat Module.

Interactive natural language conversation and intent-driven intelligence querying.
v1.1.2+: "X araştır" gibi doğal cümleler OTOMATİK olarak Agent Layer'i tetikler.
"""

from core.module_base import BaseModule
from core.cognitive.dialogue import CognitiveDialogueEngine


class ChatModule(BaseModule):
    """v1.1.1 - Cognitive Interface & Natural Language Chat Module."""

    name = "chat"

    # Persistent dialogue engine across CLI executions in session
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
            ["INTENT EXTRACTION", "COGNITIVE SYNTHESIS", "AUTO-ACTION (agent)"]
        )

        engine = self.get_engine(self.context)

        with inv.phase(0):
            self.status_step("Analyzing natural language query and context memory")

        with inv.phase(1):
            self.status_step(f"Engaging {engine.active_provider.provider_name}")
            chat_result = engine.chat(user_message)
            suggested = chat_result.get("suggested_command")

        # v1.1.2+: agent önerisi gelen komut OTOMATİK çalıştır (güvenli otonom)
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
        }

        return self.success(target=user_message, data=data)

    def _load_modules(self):
        from core.loader import load_modules
        return load_modules()

    def _ask_approval(self, question):
        """İnteraktif onay: ağ çağrısı yapan araçlar için kullanıcıya sor."""
        try:
            answer = input(question + " (e/h): ").strip().lower()
            return answer in ("e", "evet", "yes", "y", "1")
        except Exception:
            return False