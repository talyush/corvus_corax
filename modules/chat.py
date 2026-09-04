"""Corvus Corax v1.1.1 - Cognitive Chat Module.

Interactive natural language conversation and intent-driven intelligence querying.
"""
from core.module_base import BaseModule
from core.cognitive.dialogue import CognitiveDialogueEngine


class ChatModule(BaseModule):
    """
    v1.1.1 - Cognitive Interface & Natural Language Chat Module.
    """
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
            f"Cognitive Interface session",
            ["INTENT EXTRACTION", "COGNITIVE SYNTHESIS"]
        )

        engine = self.get_engine(self.context)

        with inv.phase(0):
            self.status_step("Analyzing natural language query and context memory")

        with inv.phase(1):
            self.status_step(f"Engaging {engine.active_provider.provider_name}")
            chat_result = engine.chat(user_message)

        data = {
            "user_message": user_message,
            "response": chat_result["response"],
            "intent": chat_result["intent"],
            "provider": chat_result["provider"],
            "active_target": chat_result["active_target"],
            "suggested_command": chat_result["suggested_command"],
        }

        return self.success(target=user_message, data=data)
