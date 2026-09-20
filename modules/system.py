"""Corvus Corax v1.1.2+ — System Module (CLI / Doctor).

Zihin sesleri (provider'lar) hakkında şeffaf bilgi:
  system            -> genel durum (provider sayısı, aktif ses, sağlık)
  system providers  -> tüm sağlayıcıların metadata'sı
  system provider <id> -> tek sağlayıcı detayı
  system doctor     -> sağlık kontrolü (diagnostic)
  system history    -> son yanıtların provenance'ı

Aynı bilgi doğal dille de sorulabilir:
  "hangi modelle konuşuyorum? / ai sağlığı nasıl?" -> chat bu modüle yönlenir.
"""

from core.module_base import BaseModule


class SystemModule(BaseModule):
    """Zihin sesleri (provider) ve sistem sağlığı görünümü."""

    name = "system"

    def execute(self):
        args = self.target or []
        args = list(args) if isinstance(args, (list, tuple)) else str(args).split()
        sub = args[0].lower() if args else "status"

        from core.cognitive.providers.registry import ProviderRegistry

        registry = ProviderRegistry()

        inv = self.begin_investigation(
            "System & Provider Status",
            ["PROVIDER REGISTRY", "HEALTH", "DOCTOR"],
        )

        if sub == "providers":
            with inv.phase(0):
                self.status_step("Enumerating provider registry")
            return self.success(target="providers", data={
                "providers": registry.metadata(),
            })

        if sub == "provider" and len(args) >= 2:
            with inv.phase(0):
                self.status_step(f"Inspecting provider {args[1]}")
            p = registry.get(args[1])
            if p is None:
                return self.success(target=args[1], data={
                    "error": f"provider '{args[1]}' bulunamadı",
                    "known": [x.provider_id for x in registry.all()],
                })
            return self.success(target=args[1], data={"provider": p.metadata()})

        if sub == "doctor":
            with inv.phase(2):
                self.status_step("Running health diagnostics")
            # Sağlık durumlarını topla
            result = {"providers": registry.metadata()}
            # son yanıt provenance (memory yoksa boş)
            return self.success(target="doctor", data=result)

        if sub == "history":
            with inv.phase(1):
                self.status_step("Reading last responses provenance")
            # Dialogue engine global kullanımı — modül içinden doğrudan erişilmez:
            return self.success(target="history", data={
                "note": "Sohbet geçmişi oturum içinde tutulur; her yanıtın provenance'ı "
                        "chat çıktısında görünür.",
            })

        # default: status
        with inv.phase(1):
            self.status_step("Aggregating provider status")
        providers = registry.metadata()
        active = next((p for p in providers if p["available"]), None)
        return self.success(target="system", data={
            "provider_count": len(providers),
            "active_voice": active["provider_name"] if active else None,
            "providers": providers,
            "mind_engine": "Corvus Mind (symbolic core — never changes)",
        })