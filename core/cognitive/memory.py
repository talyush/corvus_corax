"""Corvus Corax v1.1.1 - Multi-Turn Conversational Memory.

Tracks conversation history, active focal targets, entity mentions,
and provides context awareness across consecutive dialogue turns.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class DialogueTurn:
    """Tek bir diyalog turu kaydı."""

    def __init__(self, role: str, content: str, intent: Optional[str] = None,
                 entities: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.role = role  # "user" veya "assistant"
        self.content = content
        self.intent = intent
        self.entities = entities or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "entities": self.entities,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class ConversationMemory:
    """Çok Turlu (Multi-Turn) Konuşma ve Bağlam Hafızası."""

    def __init__(self, max_turns: int = 30):
        self.max_turns = max_turns
        self.turns: List[DialogueTurn] = []
        self.active_target: Optional[str] = None
        self.active_target_type: Optional[str] = None
        self.session_entities: Dict[str, str] = {}  # entity_value -> entity_type

    def add_user_message(self, content: str, intent: Optional[str] = None,
                         entities: Optional[List[str]] = None) -> DialogueTurn:
        turn = DialogueTurn(role="user", content=content, intent=intent, entities=entities)
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)

        # Update active target if entities are present
        if entities:
            self.active_target = entities[0]
        return turn

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> DialogueTurn:
        turn = DialogueTurn(role="assistant", content=content, metadata=metadata)
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)
        return turn

    def update_focal_target(self, target: str, target_type: str = "unknown"):
        self.active_target = target
        self.active_target_type = target_type
        self.session_entities[target] = target_type

    def get_recent_history(self, limit: int = 6) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.turns[-limit:]]

    def resolve_reference(self, user_text: str) -> Optional[str]:
        """
        Kullanıcı 'onun', 'bu hedefin', 'this target', 'it' gibi zamirler kullandığında
        aktif hedefe bağlar.
        """
        pronoun_triggers = [
            "o", "onun", "ona", "onu", "bunun", "buna", "bunu", "bu hedefin", "bu hedefe",
            "bu kişi", "bu kişinin", "bu kişiyi", "bu şahıs", "bu şahsın", "bu şahsı",
            "hedef", "hedefin", "hedefe", "it", "its", "him", "her", "this target", "the target"
        ]
        text_lower = user_text.lower()
        words = text_lower.split()
        for trig in pronoun_triggers:
            if trig in words or f" {trig} " in f" {text_lower} ":
                return self.active_target
        return None

    def clear(self):
        self.turns.clear()
        self.active_target = None
        self.active_target_type = None
        self.session_entities.clear()
