"""Corvus Agent Layer — Safety Policy (Güvenlik Politikası).

Sandbox karar katmanı: hangi aracın kullanıcı onayına ihtiyaç duyduğunu belirler.

  ToolScope.LOCAL  -> otomatik (yerel analiz, context, nexus)
  ToolScope.NETWORK-> onay gerekir (dış ağ çağrısı, aktif tarama)
  ToolScope.DENIED -> hiç çalıştırılmaz (kısıtlı/şüpheli araç)

Ayrıca; iterasyon limiti, otonomluk seviyesi ve onay geri çağrısı (callback)
ile kullanıcıya planın her adımını sorma akışı burada yönetilir.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class ToolScope(Enum):
    LOCAL = "local"      # otomatik çalışabilir
    NETWORK = "network"  # kullanıcı onayı gerekir
    DENIED = "denied"    # çalıştırılamaz


class Approval(Enum):
    AUTO = "auto"        # onboarding callback yoksa otomatik (test modu)
    ASK = "ask"          # kullanıcıya sor
    DENY = "deny"


@dataclass
class PolicyDecision:
    tool: str
    scope: ToolScope
    requires_approval: bool = False
    reason: str = ""
    approved: bool = False


class SafetyPolicy:
    """Güvenlik karar katmanı."""

    MAX_ITERATIONS = 4          # bir görevde maksimum aksiyon döngüsü
    MAX_NETWORK_TOOLS_PER_TASK = 6
    MAX_LOCAL_TOOLS_PER_TASK = 3

    # Kısıtlı araçlar (istisna)
    DENIED_TOOLS = {"netscan", "scan"}   # aktif tarama = yüksek risk -> interaction'sız DENIED

    def __init__(self, approval_mode: Approval = Approval.ASK,
                 ask_callback: Optional[Callable[[str], bool]] = None):
        """approval_mode: ASK (varsayılan, kullanıcıya sorur), AUTO (çalıştırır — testler için).

        ask_callback(text) -> bool; None ise ASK modunda da otomatik reddedilir.
        """
        self.approval_mode = approval_mode
        self.ask_callback = ask_callback

    # ------------------------------------------------------------------
    def scope_for(self, tool_name: str, registry) -> ToolScope:
        if tool_name in self.DENIED_TOOLS:
            return ToolScope.DENIED
        if registry.is_network(tool_name):
            return ToolScope.NETWORK
        return ToolScope.LOCAL

    def decide(self, tool_name: str, registry) -> PolicyDecision:
        scope = self.scope_for(tool_name, registry)
        requires_approval = scope == ToolScope.NETWORK
        reason = "dış ağ çağrısı" if scope == ToolScope.NETWORK else (
            "kısıtlı araç" if scope == ToolScope.DENIED else "yerel analiz"
        )
        approved = scope == ToolScope.LOCAL

        if scope == ToolScope.NETWORK:
            if self.approval_mode == Approval.AUTO:
                approved = True
            elif self.approval_mode == Approval.ASK and self.ask_callback is not None:
                approved = self.ask_callback(
                    f"[Agent] '{tool_name}' aracı dış ağ çağrısı yapacak. Onaylıyor musun? (e/h): "
                )
            else:
                approved = False

        return PolicyDecision(
            tool=tool_name,
            scope=scope,
            requires_approval=requires_approval,
            reason=reason,
            approved=approved,
        )