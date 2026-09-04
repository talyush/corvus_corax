"""Corvus Corax v1.1.1 - Abstract Cognitive Provider Interface.

Defines the contract for LLM backends (Ollama, OpenAI, Gemini, Anthropic, Embedded).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AbstractCognitiveProvider(ABC):
    """Bilişsel Model Sağlayıcı Soyut Arayüzü."""

    @abstractmethod
    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        """
        Kullanıcı girdisi, konuşma geçmişi ve bağlam grafiği verilerinden
        doğal dilde dinamik yanıt üretir.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Sağlayıcının aktif/kullanılabilir olup olmadığını döner."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Sağlayıcı adı (örn: 'Embedded Semantic Engine', 'Ollama (DeepSeek-R1)', 'OpenAI GPT-4o')."""
        pass
