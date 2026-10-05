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
    """Bir aracın statik tanımı.

    v1.4 yeni alanlar:
      input_schema : JSON Schema — kwargs doğrulaması (yeni araçlarda ZORUNLU;
                     migration süresince mevcut araçlar `{}` toleransı kullanır).
      output_kind  : "data" | "evidence" | "report_fragment" — Investigation
                     Engine tool capability değerlendirmesinde kullanır.
      capabilities : capability/interface listesi (örn. "perception::source").
    """

    name: str
    target_types: List[str]          # ip, domain, person, email, phone, wallet, org
    description: str = ""
    calls_network: bool = False      # dış ağ çağrısı yapıyor mu (onay gerekir)
    max_depth: int = 1               # reflection'da kaç seviye derinleşir
    requires_target: bool = True
    aliases: List[str] = field(default_factory=list)
    # v1.4 (Phase 3) — ToolSpec migration
    input_schema: Optional[Dict] = None             # JSON Schema
    output_kind: str = "data"                       # "data" | "evidence" | "report_fragment"
    capabilities: List[str] = field(default_factory=list)
    gathers_evidence: bool = True                   # False ise çıktısı kanıt sayılmaz

    @property
    def id(self) -> str:
        return self.name

    @property
    def effective_output_kind(self) -> str:
        """Engine'in kullanacağı output_kind.

        Her araç explicit `output_kind` beyan etmelidir (Phase 3). Yine de
        gevşek uyumluluk için: verilen değer "" veya "auto" ise calls_network'ten
        türetir. Beyan edilmiş ("data"/"evidence"/"report_fragment") değere
        SAYGI GÖSTERİLİR (crawl/scan -> "data" ezilmez).
        """
        if self.output_kind in ("data", "evidence", "report_fragment"):
            return self.output_kind
        if self.calls_network and self.gathers_evidence:
            return "evidence"
        if not self.gathers_evidence:
            return "report_fragment"
        return "data"


class ToolRegistry:
    """Tüm kullanılabilir araçların envanteri."""

    BUILTIN: Dict[str, ToolSpec] = {
        # ---- Domain hedefleri ----
        "whois": ToolSpec("whois", ["domain"], "Domain kayıt sahibi ve tarih bilgisi.", calls_network=True,
                          capabilities=["perception::source"], output_kind="evidence"),
        "dns": ToolSpec("dns", ["domain"], "DNS kayıtları (A, MX, NS, TXT...).", calls_network=True,
                        capabilities=["perception::source"], output_kind="evidence"),
        "subdomain": ToolSpec("subdomain", ["domain"], "Alt alan adı keşfi.", calls_network=True,
                              capabilities=["perception::source"], output_kind="evidence"),
        "tech": ToolSpec("tech", ["domain"], "Web teknolojisi tespiti (CMS, framework, CDN).", calls_network=True,
                         capabilities=["perception::source"], output_kind="evidence"),
        "headers": ToolSpec("headers", ["domain"], "HTTP başlıkları ve güvenlik açıkları.", calls_network=True,
                            capabilities=["perception::source"], output_kind="evidence"),
        "metadata": ToolSpec("metadata", ["domain"], "robots.txt, sitemap, security.txt tespiti.", calls_network=True,
                             capabilities=["perception::source"], output_kind="evidence"),
        "crawl": ToolSpec("crawl", ["domain"], "Web sayfası taraması / içerik toplama.", calls_network=True, max_depth=2,
                          output_kind="data"),
        "footprint": ToolSpec("footprint", ["domain"], "Dijital ayak izi — geniş tarama.", calls_network=True, max_depth=2,
                              output_kind="evidence"),
        "cert": ToolSpec("cert", ["domain"], "TLS sertifika şeffaflık logları (CT).", calls_network=True,
                         capabilities=["perception::source"], output_kind="evidence"),
        "wayback": ToolSpec("wayback", ["domain"], "Arşivlenmiş web geçmişi.", calls_network=True,
                            capabilities=["perception::source"], output_kind="evidence"),
        "email": ToolSpec("email", ["domain"], "E-posta altyapısı tespiti.", calls_network=True,
                          capabilities=["perception::source"], output_kind="evidence"),

        # ---- IP hedefleri ----
        "geoip": ToolSpec("geoip", ["ip"], "IP konum ve coğrafi bilgi.", calls_network=True,
                          capabilities=["perception::source"], output_kind="evidence"),
        "asn": ToolSpec("asn", ["ip", "domain"], "ASN / ağ sahipliği analizi.", calls_network=True,
                        capabilities=["perception::source"], output_kind="evidence"),
        "scan": ToolSpec("scan", ["ip", "domain"], "Port taraması — dikkatli.", calls_network=True, max_depth=2,
                         output_kind="data"),
        "netscan": ToolSpec("netscan", ["ip"], "Ağ segment taraması.", calls_network=True, max_depth=2,
                            output_kind="data"),

        # ---- Person / Organization ----
        "social": ToolSpec("social", ["person", "username"], "Sosyal medya profili keşfi.", calls_network=True,
                           capabilities=["perception::source"], output_kind="evidence"),
        "github": ToolSpec("github", ["person", "username"], "GitHub profili ve repo taraması.", calls_network=True,
                           capabilities=["perception::source"], output_kind="evidence"),
        "academic": ToolSpec("academic", ["person"], "Akademik yayın / OpenAlex taraması.", calls_network=True,
                             capabilities=["perception::source"], output_kind="evidence"),
        "org": ToolSpec("org", ["organization", "person"], "Organizasyon/şirket istihbaratı.", calls_network=True,
                        capabilities=["perception::source"], output_kind="evidence"),

        # ---- Email / Phone / Wallet ----
        "breach": ToolSpec("breach", ["email"], "Bilinen veri sızıntıları (meta-data).", calls_network=True,
                           capabilities=["perception::source"], output_kind="evidence"),
        "phone": ToolSpec("phone", ["phone"], "Telefon numarası analizi.", calls_network=True,
                          capabilities=["perception::source"], output_kind="evidence"),
        "wallet": ToolSpec("wallet", ["wallet"], "Kripto cüzdan istihbaratı.", calls_network=True,
                           capabilities=["perception::source"], output_kind="evidence"),

        # ---- Yerel analiz (otomatik — onay gerektirmez) ----
        "resolve": ToolSpec("resolve", ["domain", "ip"], "DNS çözümleme / hostname map.", calls_network=False,
                            output_kind="data"),
        "evidence": ToolSpec("evidence", ["domain", "ip", "person", "email"], "Kanıt zinciri ve lineage analizi.", calls_network=False,
                             output_kind="report_fragment", gathers_evidence=False),
        "nexus": ToolSpec("nexus", ["domain", "ip", "person", "organization", "email"], "Korelasyon motoru — nexus infer/bridge.", calls_network=False, max_depth=2,
                          output_kind="report_fragment", gathers_evidence=False),
        "pivot": ToolSpec("pivot", ["domain", "ip", "person", "email"], "Ortak altyapı pivot analizi.", calls_network=False, max_depth=2,
                          output_kind="report_fragment", gathers_evidence=False),
        "pol": ToolSpec("pol", ["domain", "ip", "person"], "Pattern of Life — davranış analizi.", calls_network=False,
                        output_kind="report_fragment", gathers_evidence=False),
        "discover": ToolSpec("discover", ["domain", "ip", "person", "email", "organization"], "Otomatik keşif zinciri (Discovery Engine).", calls_network=True, max_depth=2,
                             output_kind="report_fragment", gathers_evidence=False),
        "geoint": ToolSpec("geoint", ["ip", "domain"], "GEOINT haritalama / lokasyon analizi.", calls_network=False,
                           output_kind="report_fragment", gathers_evidence=False),
    }
    def __init__(self, module_registry: Optional[Dict] = None):
        self.specs: Dict[str, ToolSpec] = dict(self.BUILTIN)
        # v1.4 (Phase 3) — migration: mevcut 24 aracın input_schema'sı boşsa
        # `{}` tolerant geçiş değeri alır (yeni araçlar şemasız kayıt EDİLEMEZ;
        # register() bunu zorlar). Gerçek şeması verilenler dokunulmaz.
        for _spec in self.specs.values():
            if _spec.input_schema is None:
                _spec.input_schema = {}
        # Hangi modüller gerçekten yüklü? (loader sonucu)
        self.available: List[str] = []
        if module_registry:
            self.sync_with_modules(module_registry)

    # ------------------------------------------------------------------
    # v1.4 (Phase 3) — registry genişlemiş kayıt: yeni araçlar şemasız giremez
    # ------------------------------------------------------------------
    def register(self, spec: ToolSpec) -> None:
        """Yeni araç kaydı.

        v1.4 kuralı: input_schema ZORUNLU'dur — şemasız kayıt reddedilir.
        Migration istisnası: mevcut BUILTIN araçları `input_schema={}` toleransı
        ile üretilir (yukarıdaki BUILTIN tanımı), yeni eklenenler bu doğrulamadan
        geçer.
        """
        if not isinstance(spec, ToolSpec):
            raise TypeError("ToolRegistry.register sadece ToolSpec kabul eder")
        if spec.input_schema is None:
            raise ValueError(
                f"Tool '{spec.name}' input_schema olmadan kayıt edilemez (v1.4 zorunluluğu). "
                "Boş bırakılamaz; gereksizse '{}' kullanın (açık tolerant schema).")
        if spec.name in self.specs:
            raise ValueError(f"Tool '{spec.name}' zaten kayıtlı (override yasak)")
        self.specs[spec.name] = spec

    def validate_input(self, tool_name: str, kwargs: Dict) -> Optional[str]:
        """JSON Schema ile kwargs doğrulaması yapar. Hata mesajı veya None.

        Schema yoksa ({} toleransı) doğrulama geçer — migration esintisi sürerken
        kırılsın istenmez.
        """
        spec = self.specs.get(tool_name)
        if spec is None or not spec.input_schema:
            return None  # tolerans: şema yoksa kwargs geçer
        schema = spec.input_schema
        required = schema.get("required", [])
        for field in required:
            if field not in kwargs:
                return f"'{tool_name}' eksik zorunlu parametre: {field}"
        properties = schema.get("properties", {})
        for field, value in kwargs.items():
            ftype = properties.get(field, {}).get("type")
            if ftype == "string" and not isinstance(value, str):
                return f"'{tool_name}' parametresi '{field}' string olmalı"
            if ftype == "integer" and not isinstance(value, int):
                return f"'{tool_name}' parametresi '{field}' integer olmalı"
        return None

    def has_capability(self, tool_name: str, capability: str) -> bool:
        spec = self.specs.get(tool_name)
        return bool(spec and capability in spec.capabilities)

    def output_kind_for(self, tool_name: str) -> str:
        spec = self.specs.get(tool_name)
        return spec.effective_output_kind if spec else "data"

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