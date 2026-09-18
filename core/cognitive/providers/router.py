"""Corvus Corax v1.1.2+ - Provider Router.

"Many models, one mind interface" — aklin sesini secen katman.

Router:
  1. Goreve gore provider secimi (capability matching: deep/fast/code...)
  2. Fallback zinciri: primary -> secondary -> ... -> embedded_core (asla atlanmaz)
  3. Saglik odakli: HealthManager'a dayanir (degraded/offline atlanir)
  4. PROVENANCE: her yanitin hangi provider/model ile uretildigini kaydeder
     - request_id, provider, model, fallback_chain, fallback_reason

Felsefe: provider degisir, Corvus'un zihni degismez. Router yalnizca SESTIR.
"""

from __future__ import annotations
import uuid
import time
from typing import Dict, List, Optional

from .interface import AbstractCognitiveProvider, Capability
from .health import HealthManager
from .registry import ProviderRegistry


class ProviderResult:
    """Bir yanitin uretim kaydi (provenance)."""

    def __init__(self, text: str, provider: Optional[AbstractCognitiveProvider] = None,
                 request_id: str = "", fallback_chain: Optional[List[str]] = None,
                 fallback_reason: str = ""):
        self.text = text
        self.provider = provider
        self.request_id = request_id or str(uuid.uuid4())[:8]
        self.fallback_chain = fallback_chain or []
        self.fallback_reason = fallback_reason

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "provider": self.provider.provider_id if self.provider else None,
            "provider_name": self.provider.provider_name if self.provider else None,
            "model": self.provider.model if self.provider else None,
            "fallback_chain": self.fallback_chain,
            "fallback_reason": self.fallback_reason,
        }


class ProviderRouter:
    """Zihin sesi yonlendiricisi — fallback + saglik + provenance."""

    def __init__(self, registry: Optional[ProviderRegistry] = None,
                 health: Optional[HealthManager] = None):
        self.registry = registry or ProviderRegistry()
        self.health = health or HealthManager()
# ------------------------------------------------------------------
    # Ana giris: prompt + gorev -> yanit + provenance
    # ------------------------------------------------------------------
    def route(self, user_prompt: str, conversation_history: List[Dict],
              context_data: Optional[Dict] = None, system_prompt: Optional[str] = None,
              with_cap: Optional[Capability] = None,
              preferred: Optional[str] = None) -> ProviderResult:
        """Provider/fallback zincirinden yanit uretir."""
        chain = []
        reasons = []
        last_error = ""

        # 1. Aday sirasi: preferred (verildiyse) -> capability -> priority
        candidates = self._candidates(preferred=preferred, with_cap=with_cap)

        for provider in candidates:
            chain.append(provider.provider_id)

            # Saglik kontrolu: cooldown'daysa atla
            if not self.health.is_recoverable(provider.provider_id):
                reasons.append(f"{provider.provider_id}:offline_cooldown")
                continue

            try:
                text = provider.generate_response(
                    user_prompt=user_prompt,
                    conversation_history=conversation_history,
                    context_data=context_data,
                    system_prompt=system_prompt,
                )

                # Basarisizlik gosterimi (hata metni) -> fallback
                if text.startswith("[") and ("Error" in text or "missing" in text.lower()):
                    reasons.append(f"{provider.provider_id}:error_resp")
                    self.health.record_failure(provider.provider_id)
                    last_error = text[:120]
                    continue

                # Basari kriteri: bos olmamasi + minimal uzunluk
                if len(text.strip()) < 2:
                    reasons.append(f"{provider.provider_id}:empty_resp")
                    self.health.record_failure(provider.provider_id)
                    continue

                self.health.record_success(provider.provider_id)
                return ProviderResult(
                    text=text.strip(),
                    provider=provider,
                    fallback_chain=chain,
                    fallback_reason=";".join(reasons),
                )
            except Exception as e:
                reasons.append(f"{provider.provider_id}:{type(e).__name__}")
                self.health.record_failure(provider.provider_id)
                last_error = str(e)[:120]

        # 2. Hicbiri calismadiysa EMBEDDED_CORE (asla atlanmaz) — garantili ses
        embedded = self.registry.get("embedded_core")
        if embedded is not None:
            chain.append(embedded.provider_id)
            try:
                text = embedded.generate_response(
                    user_prompt=user_prompt,
                    conversation_history=conversation_history,
                    context_data=context_data,
                    system_prompt=system_prompt,
                )
                reasons.append("final_fallback:embedded_core")
                return ProviderResult(
                    text=text.strip(),
                    provider=embedded,
                    fallback_chain=chain,
                    fallback_reason=";".join(reasons),
                )
            except Exception as e:
                reasons.append(f"embedded:{type(e).__name__}")
                last_error = str(e)[:120]

        # 3. Cok nadir: Corvus Mind bile calismadi
        return ProviderResult(
            text="Beni baglarken bir sorun olustu. Kisa bir sure sonra tekrar deneyebilir misin?",
            fallback_chain=chain,
            fallback_reason=";".join(reasons),
        )

    # ------------------------------------------------------------------
    # Aday secimi
    # ------------------------------------------------------------------
    def _candidates(self, preferred: Optional[str],
                    with_cap: Optional[Capability]) -> List[AbstractCognitiveProvider]:
        """Primary -> secondary -> ... -> embedded_core ozel sirasi."""
        providers = []

        pref_provider = self.registry.get(preferred) if preferred else None
        if pref_provider and self.registry.is_usable(pref_provider):
            providers.append(pref_provider)

        for p in self.registry.by_priority(with_cap=with_cap):
            if p.provider_id not in [x.provider_id for x in providers]:
                providers.append(p)

        embedded = self.registry.get("embedded_core")
        if embedded and embedded.provider_id not in [x.provider_id for x in providers]:
            providers.append(embedded)

        return providers