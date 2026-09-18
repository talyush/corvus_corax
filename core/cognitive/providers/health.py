"""Corvus Corax v1.1.2+ - Health Manager.

Provider sagligini izler ve yonetir:
    healthy -> degraded -> offline -> recovering

Kurallar:
  - Basarili yanit  : saglik iyilesir (RECOVERING -> HEALTHY)
  - Timeout/hata    : degrades; ust uste hatada offline
  - Offline'dan sonra: recovering (yeniden denenir), basariyla HEALTHY

Strateji: "performanstan kazan, sureden odun ver" prensibine uygun —
saglikli adaylar onceliklendirilir, sagliksizlar atlanir (bloklamaz).
"""

from __future__ import annotations
import time
from typing import Dict
from .interface import ProviderHealth


class HealthManager:
    """Provider saglik durumlarini izler ve gunceller."""

    # Durum gecis kurallari (aritmetik)
    DEGRADE_THRESHOLD = 2      # ust uste bu kadar hata -> degraded
    OFFLINE_THRESHOLD = 4      # ust uste bu kadar hata -> offline
    RECOVER_AFTER = 30.0       # offline'dan sonra kac saniye bekleyip yeniden dene (s)

    def __init__(self):
        self._state: Dict[str, ProviderHealth] = {}
        self._fail_count: Dict[str, int] = {}
        self._last_fail: Dict[str, float] = {}
        self._cooldown_until: Dict[str, float] = {}

    # ------------------------------------------------------------------
    def status(self, provider_id: str) -> ProviderHealth:
        """Anlik saglik durumu."""
        return self._state.get(provider_id, ProviderHealth.HEALTHY)

    def is_recoverable(self, provider_id: str) -> bool:
        """Bir provider'in yeniden denenmeye deger olup olmadigi."""
        st = self.status(provider_id)
        if st == ProviderHealth.HEALTHY:
            return True
        if st == ProviderHealth.RECOVERING:
            return True
        # offline: cooldown gectiyse yeniden dene (recovering'e gecir)
        now = time.time()
        cooldown = self._cooldown_until.get(provider_id, 0)
        if now >= cooldown:
            self._state[provider_id] = ProviderHealth.RECOVERING
            return True
        return False

    # ------------------------------------------------------------------
    def record_success(self, provider_id: str) -> None:
        """Basarili yanit -> saglik tamamen duzelir."""
        self._state[provider_id] = ProviderHealth.HEALTHY
        self._fail_count[provider_id] = 0
        self._cooldown_until.pop(provider_id, None)

    def record_failure(self, provider_id: str) -> ProviderHealth:
        """Hata -> degrades/offline; yeni durumu dondurur."""
        fails = self._fail_count.get(provider_id, 0) + 1
        self._fail_count[provider_id] = fails
        self._last_fail[provider_id] = time.time()

        if fails >= self.OFFLINE_THRESHOLD:
            self._state[provider_id] = ProviderHealth.OFFLINE
            # offline cooldown: RECOVER_AFTER sn sonra yeniden denenir
            self._cooldown_until[provider_id] = time.time() + self.RECOVER_AFTER
        elif fails >= self.DEGRADE_THRESHOLD:
            self._state[provider_id] = ProviderHealth.DEGRADED
        else:
            # single hata: henuz degraded etme (gurultu say)
            self._state.setdefault(provider_id, ProviderHealth.HEALTHY)
        return self.status(provider_id)

    def snapshot(self) -> Dict[str, Dict]:
        """CLI/doctor icin tum provider saglik ozeti."""
        out = {}
        for pid, st in self._state.items():
            out[pid] = {
                "health": st.value,
                "consecutive_failures": self._fail_count.get(pid, 0),
            }
        return out