"""Corvus Corax v1.1.2+ - Provider Registry.

Tum kullanilabilir saglayicilarin envanteri.
"Many models" tarafi: Ollama, OpenAI (GPT), Cloud (Claude/Gemini), Embedded Core.

Registry, saglayicilari kaydeder, birincil/ikincil ayrimi + oncelik sirasi verir.
Saglayicilar istege bagli (key/varliga gore) kaydedilir — olmayan atlanir.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from .interface import AbstractCognitiveProvider, Capability
from .local_engine import EmbeddedCognitiveEngine
from .api_providers import OllamaProvider, OpenAIProvider


class ProviderRegistry:
    """Kullanilabilir zihin sesleri kayit defteri."""

    def __init__(self, include_cloud_claude: bool = True):
        self.providers: Dict[str, AbstractCognitiveProvider] = {}

        # Corvus Mind her zaman orada (offline/sembolik — asla yok sayilmaz)
        self.register(EmbeddedCognitiveEngine())

        # Ollama (yerel) — varsa
        try:
            self.register(OllamaProvider())
        except Exception:
            pass

        # OpenAI — api key varsa
        try:
            self.register(OpenAIProvider())
        except Exception:
            pass

        # Cloud / Claude — api key varsa
        if include_cloud_claude:
            try:
                from .api_providers import AnthropicProvider
                self.register(AnthropicProvider())
            except Exception:
                pass

    # ------------------------------------------------------------------
    def register(self, provider: AbstractCognitiveProvider) -> None:
        self.providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> Optional[AbstractCognitiveProvider]:
        return self.providers.get(provider_id)

    def all(self) -> List[AbstractCognitiveProvider]:
        return list(self.providers.values())

    def available(self) -> List[AbstractCognitiveProvider]:
        """O an kullanilabilir saglayicilar (embedded her zaman var)."""
        return [p for p in self.providers.values() if self.is_usable(p)]

    def is_usable(self, provider: AbstractCognitiveProvider) -> bool:
        """Saglayiciyi kullanabilir mi (embedded her zaman TRUE)."""
        if provider.provider_id == "embedded_core":
            return True
        try:
            return bool(provider.is_available())
        except Exception:
            return False

    def by_priority(self, with_cap: Optional[Capability] = None) -> List[AbstractCognitiveProvider]:
        """Kullanilabilirleri oncelik sirasina gore doner (dusuk once)."""
        pool = [p for p in self.providers.values() if self.is_usable(p)]
        if with_cap:
            pool = [p for p in pool if p.has_capability(with_cap)]
        return sorted(pool, key=lambda p: p.priority)

    def metadata(self) -> List[Dict]:
        """CLI/doctor/dogal dil icin tum saglayici bilgisi."""
        return [p.metadata() for p in self.all()]