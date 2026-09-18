"""Corvus Corax v1.1.1+ - Abstract Cognitive Provider Interface.

"Many models, one mind interface" - provider sozlesmesi.

Her LLM/kognitif saglayici bu sozlesmeyi karsilamalidir:
  - chat:       generate_response (temel)
  - stream:     opsiyonel akis uretimi
  - health:     health_status() -> healthy/degraded/offline/recovering
  - capabilities: hangi gorevlere uygun (general/deep/creative/code/fast/offline)
  - metadata:   provider_id, model, provider_name

Kritik: saglayici yalnizca SESTIR - Corvus'un zihni (alignment, memory,
persona, planning) asla bir saglayiciya devredilmez.
"ai degisebilir, corvus degisemez."
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional


class ProviderHealth(Enum):
    """Provider'in anlik saglik durumu (HealthManager tarafindan yonetilir)."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"       # yavas/kararsiz ama calisabilir
    OFFLINE = "offline"
    RECOVERING = "recovering"   # arizadan cikista tekrar denenir


class Capability(Enum):
    """Provider'in hangi gorevleri destekledigini belirtir."""

    GENERAL = "general"        # her sey
    DEEP = "deep"              # felsefi / uzun akil yurutme
    CODE = "code"              # kod / teknik
    CREATIVE = "creative"      # yaratici yazi
    FAST = "fast"              # hizlandirilmis / kisa yanit
    OFFLINE = "offline"        # internet gerektirmez
    LOCAL = "local"            # yerel makinede calisir
    CLOUD = "cloud"            # bulut API
    STREAM = "stream"          # streaming destekler


class AbstractCognitiveProvider(ABC):
    """Bilissel Model Saglayici Soyut Arayuzu."""

    # ------------------------------------------------------------------
    # Metadata - saglayiciyi tanimlar
    # ------------------------------------------------------------------
    provider_id: str = "base"
    model: str = "base"
    capabilities: List[Capability] = [Capability.GENERAL]
    priority: int = 100            # router fallback sirasi (dusuk = once)

    @abstractmethod
    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        """Girdi, gecmis ve baglam grafiginden dogal dil yanit uretir."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Saglayicinin kullanilabilir olup olmadigini dondurur."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Saglayici adi (orn: 'Embedded Cognitive Engine', 'Ollama (...).')."""
        pass

    # ------------------------------------------------------------------
    # Health & Capabilities - router / CLI / dogal dil icin
    # ------------------------------------------------------------------
    def health_status(self) -> ProviderHealth:
        try:
            return ProviderHealth.HEALTHY if self.is_available() else ProviderHealth.OFFLINE
        except Exception:
            return ProviderHealth.OFFLINE

    def has_capability(self, cap: Capability) -> bool:
        return cap in self.capabilities

    def metadata(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "model": self.model,
            "health": self.health_status().value,
            "available": self.is_available(),
            "capabilities": [c.value for c in self.capabilities],
            "priority": self.priority,
        }