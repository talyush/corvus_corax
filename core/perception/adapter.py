"""Corvus Perception — SourceAdapter sözleşmesi ve Wrapper.

v1.4 kararı: mevcut modules/*.py topluca refactor edilmez. SourceAdapter,
bir modülü sararak (Wrapper) Perception pipeline'ına bağlar:

    fetch()   -> modülü çalıştırır (execute), ham çıktıyı toplar
    normalize()-> ham çıktıyı kanonik form'a çevirir (kaynak bağımsız)
    declare() -> kendi SourceDeclaration'ını beyan eder

Context'in doğrudan yazımı burada YASAK — yalnızca pipeline, eligibility
gate'ini geçen veriyi ContextManager'a yazar.

YENİ dosya açılmadan önce ilgili modül yüklenir (yeni/paralel sistem yok).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from core.perception.model import SourceDeclaration, PerceptionResult, stamp_provenance


class SourceAdapter(ABC):
    """Bir algı kaynağını (modülü) Perception pipeline'a bağlayan sözleşme.

    Her adaptör, bir SourceDeclaration beyan eder ve perceive() akışını
    (fetch → normalize) sağlar. Pipeline, sonucu provenance + eligibility
    ile taçlandırır ve dünya modeline yazar.
    """

    source: SourceDeclaration

    @abstractmethod
    def fetch(self, target: str, **params) -> Any:
        """Modülü/modülü saran mantığı çalıştırır; HAM çıktıyı döner."""

    @abstractmethod
    def normalize(self, raw: Any, target: str) -> Dict:
        """Ham çıktıyı, ContextManager add_entity/add_relation uyumlu kanonik forma çevirir."""

    # ------------------------------------------------------------------
    def perceive(self, target: str, **params) -> PerceptionResult:
        """fetch + normalize + provenance zımbası -> PerceptionResult.

        Not: Bu metot ContextManager'a YAZMAZ. Yazma/eligibility pipeline'da.
        """
        try:
            raw = self.fetch(target, **params)
        except Exception as e:
            return PerceptionResult(
                ok=False, source=self.source, target=target,
                target_type="unknown", raw=None, normalized={},
                provenance=stamp_provenance(self.source, target, None),
                error=f"fetch failed: {e}",
            )

        normalized = {}
        try:
            normalized = self.normalize(raw, target)
        except Exception as e:
            return PerceptionResult(
                ok=False, source=self.source, target=target,
                target_type="unknown", raw=raw, normalized={},
                provenance=stamp_provenance(self.source, target, raw),
                error=f"normalize failed: {e}",
            )

        return PerceptionResult(
            ok=True,
            source=self.source,
            target=target,
            target_type=self._target_type(normalized, target),
            raw=raw,
            normalized=normalized,
            provenance=stamp_provenance(self.source, target, raw),
        )

    def _target_type(self, normalized: Dict, target: str) -> str:
        return "unknown"
class ModuleSourceAdapter(SourceAdapter):
    """Mevcut bir BaseModule alt sınıfını saran adaptör (Wrapper).

    Modül, izole (NoWriteContext) ile çalıştırılır: modülün kendi içinde
    yaptığı context yazımları GERÇEK context'e dokunmaz. Modülün dönen
    success payload'ı normalize edilir; context yazımı yalnızca pipeline'ın
    eligibility gate'i ile yapılır.

    Böylece mevcut module kaynak kodu DEĞİŞMEDEN pürüzsüz migration
    (v1.4 kararı: toplu refactor yok, wrapper ile izole).
    """

    def __init__(self, module_cls: Type, source: SourceDeclaration,
                 config: Optional[Dict] = None, logger=None, context=None,
                 module_kwargs: Optional[Dict] = None):
        self.module_cls = module_cls
        self.source = source
        self.config = config or {}
        self.logger = logger
        self.context = context
        self.module_kwargs = module_kwargs or {}

    # ------------------------------------------------------------------
    def _make_isolated(self, target: str, user_context):
        """Modülü context izolasyonuyla kurar.

        Modül 'context' olarak gerçek ContextManager yerine _NoWriteContext
        alır; böylece modülün add_entity/add_relation çağrıları dış dünyaya
        sızmaz. None-güvenli modüller None da alabilir; _NoWriteContext
        sessiz geçişli context olarak güvenlidir.
        """
        ctx = user_context if user_context is not None else _NoWriteContext()
        return self.module_cls(
            target=[target],
            config=self.config,
            logger=self.logger,
            context=ctx,
            **self.module_kwargs,
        )

    def execute_isolated(self, target: str, **params) -> Dict:
        """Modülü çalıştırır, success/error payload'ını döner (context yazmaz)."""
        user_context = params.pop("_context_override", self.context)
        module = self._make_isolated(target, user_context)
        return module.execute()

    def fetch(self, target: str, **params) -> Any:
        out = self.execute_isolated(target, **params)
        if not isinstance(out, dict):
            return {"status": "error", "error": "modül beklenen dict döndürmedi"}
        return out

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        """Varsayılan normalize: modül dönen dict'i taşır (adaptörler ezebilir)."""
        out = raw if isinstance(raw, dict) else {}
        return {
            "status": out.get("status"),
            "data": out.get("data", {}),
            "notes": out.get("notes", []),
            "relationships": out.get("relationships", []),
            "module": out.get("module"),
            "target": out.get("target"),
        }

    # ------------------------------------------------------------------
    def _target_type(self, normalized: Dict, target: str) -> str:
        data = normalized.get("data", {}) if isinstance(normalized, dict) else {}
        if data.get("target_type"):
            return data["target_type"]
        if "." in target and " " not in target and target.count(".") <= 3 \
                and not all(p.isdigit() for p in target.split(".")):
            return "domain"
        if target.count(".") == 3 and all(p.isdigit() for p in target.split(".")):
            return "ip"
        if "@" in target:
            return "email"
        return "person"


class _NoWriteContext:
    """Modüllere verilen güvenlik kopyası: HİÇBİRŞEY yazmaz, HER metodu sessizce geçer.

    Modül `self.context.add_entity(...)` çağırırsa gerçek context'e dokunmaz.
    `data` alanı boş dict olarak okunur (context.graph'a ihtiyaç duyan
    preflight/analyst bileşenleri için güvenli).
    """

    data: Dict = {}

    def __getattr__(self, _name: str):
        # Tüm method çağrıları (add_*, query_*, get_*) sessizce geçer; None döner.
        def _sink(*_args, **_kwargs):
            return None
        return _sink
