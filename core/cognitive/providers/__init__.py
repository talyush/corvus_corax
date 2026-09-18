"""Corvus Corax Cognitive Providers Package.

"Many models, one mind interface" — zihin sesi katmani.
Saglayicilar degisebilir, Corvus'un zihni degismez.
"""
from .interface import AbstractCognitiveProvider, ProviderHealth, Capability
from .local_engine import EmbeddedCognitiveEngine
from .api_providers import OllamaProvider, OpenAIProvider, AnthropicProvider
from .health import HealthManager
from .registry import ProviderRegistry
from .router import ProviderRouter, ProviderResult

__all__ = [
    "AbstractCognitiveProvider",
    "ProviderHealth",
    "Capability",
    "EmbeddedCognitiveEngine",
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "HealthManager",
    "ProviderRegistry",
    "ProviderRouter",
    "ProviderResult",
]
