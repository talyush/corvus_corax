"""Corvus Agent Layer — Tool Registry.

Modül adlarını; hedef tipi (ip/domain/person/email/phone/wallet/org),
aracın ne yaptığı ve güvenlik kapsamıyla birlikte tanımlar.
Her aracın çalıştırılabilmesi için modülün registry'ye dahil olması gerekir.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable


@dataclass
class ToolSpec:
    """Bir aracın statik tanımı."""

    name: str
    target_types: List[str]          # ip, domain, person, email, phone, wallet, org
    description: str = ""
    calls_network: bool = False      # dış ağ çağrısı yapıyor mu (onay gerekir)
    max_depth: int = 1               # reflection'da kaç seviye derinleşir
    requires_target: bool = True
    aliases: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.name


class ToolRegistry:
    """Tüm kullanılabilir araçların envanteri."""

    BUILTIN: Dict[str, ToolSpec] = {
        # ---- Domain hedefleri ----
        "whois": ToolSpec("whois", ["domain"], "Domain kayıt sahibi ve tarih bilgisi.", calls_network=True),
        "dns": ToolSpec("dns", ["domain"], "DNS kayıtları (A, MX, NS, TXT...).", calls_network=True),
        "subdomain": ToolSpec("subdomain", ["domain"], "Alt alan adı keşfi.", calls_network=True),
        "tech": ToolSpec("tech", ["domain"], "Web teknolojisi tespiti (CMS, framework, CDN).", calls_network=True),
        "headers": ToolSpec("headers", ["domain"], "HTTP başlıkları ve güvenlik açıkları.", calls_network=True),
        "metadata": ToolSpec("metadata", ["domain"], "robots.txt, sitemap, security.txt tespiti.", calls_network=True),
        "crawl": ToolSpec("crawl", ["domain"], "Web sayfası taraması / içerik toplama.", calls_network=True, max_depth=2),
        "footprint": ToolSpec("footprint", ["domain"], "Dijital ayak izi — geniş tarama.", calls_network=True, max_depth=2),
        "cert": ToolSpec("cert", ["domain"], "TLS sertifika şeffaflık logları (CT).", calls_network=True),
        "wayback": ToolSpec("wayback", ["domain"], "Arşivlenmiş web geçmişi.", calls_network=True),
        "email": ToolSpec("email", ["domain"], "E-posta altyapısı tespiti.", calls_network=True),

        # ---- IP hedefleri ----
        "geoip": ToolSpec("geoip", ["ip"], "IP konum ve coğrafi bilgi.", calls_network=True),
        "asn": ToolSpec("asn", ["ip", "domain"], "ASN / ağ sahipliği analizi.", calls_network=True),
        "scan": ToolSpec("scan", ["ip", "domain"], "Port taraması — dikkatli.", calls_network=True, max_depth=2),
        "netscan": ToolSpec("netscan", ["ip"], "Ağ segment taraması.", calls_network=True, max_depth=2),

        # ---- Person / Organization ----
        "social": ToolSpec("social", ["person", "username"], "Sosyal medya profili keşfi.", calls_network=True),
        "github": ToolSpec("github", ["person", "username"], "GitHub profili ve repo taraması.", calls_network=True),
        "academic": ToolSpec("academic", ["person"], "Akademik yayın / OpenAlex taraması.", calls_network=True),
        "org": ToolSpec("org", ["organization", "person"], "Organizasyon/şirket istihbaratı.", calls_network=True),

        # ---- Email / Phone / Wallet ----
        "breach": ToolSpec("breach", ["email"], "Bilinen veri sızıntıları (meta-data).", calls_network=True),
        "phone": ToolSpec("phone", ["phone"], "Telefon numarası analizi.", calls_network=True),
        "wallet": ToolSpec("wallet", ["wallet"], "Kripto cüzdan istihbaratı.", calls_network=True),

        # ---- Yerel analiz (otomatik — onay gerektirmez) ----
        "resolve": ToolSpec("resolve", ["domain", "ip"], "DNS çözümleme / hostname map.", calls_network=False),
        "evidence": ToolSpec("evidence", ["domain", "ip", "person", "email"], "Kanıt zinciri ve lineage analizi.", calls_network=False),
        "nexus": ToolSpec("nexus", ["domain", "ip", "person", "organization", "email"], "Korelasyon motoru — nexus infer/bridge.", calls_network=False, max_depth=2),
        "pivot": ToolSpec("pivot", ["domain", "ip", "person", "email"], "Ortak altyapı pivot analizi.", calls_network=False, max_depth=2),
        "pol": ToolSpec("pol", ["domain", "ip", "person"], "Pattern of Life — davranış analizi.", calls_network=False),
        "discover": ToolSpec("discover", ["domain", "ip", "person", "email", "organization"], "Otomatik keşif zinciri (Discovery Engine).", calls_network=True, max_depth=2),
        "geoint": ToolSpec("geoint", ["ip", "domain"], "GEOINT haritalama / lokasyon analizi.", calls_network=False),
    }
    def __init__(self, module_registry: Optional[Dict] = None):
        self.specs: Dict[str, ToolSpec] = dict(self.BUILTIN)
        # Hangi modüller gerçekten yüklü? (loader sonucu)
        self.available: List[str] = []
        if module_registry:
            self.sync_with_modules(module_registry)

    def sync_with_modules(self, module_registry: Dict) -> None:
        """Yüklenmiş modülleri kullanılabilir araçlarla eşleştirir."""
        loaded = set(module_registry.keys())
        for tool_name in self.specs:
            if tool_name in loaded:
                self.available.append(tool_name)
        self.available.sort()

    # ------------------------------------------------------------------
    def is_available(self, tool_name: str) -> bool:
        return tool_name in self.available

    def is_network(self, tool_name: str) -> bool:
        spec = self.specs.get(tool_name)
        return bool(spec and spec.calls_network)

    def tools_for_target(self, target_type: str) -> List[str]:
        """Belirli bir hedef tipi için önerilen araç sırasını verir."""
        ordered = []
        # Önce network toplayıcılar, sonra yerel analiz
        for name, spec in self.specs.items():
            if target_type in spec.target_types and spec.calls_network:
                ordered.append(name)
        for name, spec in self.specs.items():
            if target_type in spec.target_types and not spec.calls_network:
                ordered.append(name)
        return ordered

    def get(self, tool_name: str) -> Optional[ToolSpec]:
        return self.specs.get(tool_name)

    def describe(self) -> List[str]:
        out = []
        for name, spec in self.specs.items():
            scope = "NET" if spec.calls_network else "LOCAL"
            out.append(f"  {name:<12} [{scope:>5}] hedefler: {','.join(spec.target_types)} — {spec.description}")
        return out