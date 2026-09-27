"""Corvus Perception — Pipeline (v1.4).

Sözleşme akışı:
    SourceAdapter.perceive (fetch+normalize+provenance)
        -> EvidenceExtractor (mevcut evidence engine)
        -> EvidenceValidator (VALIDATED | SYNTAX_ERROR | UNVERIFIABLE | EXPIRED)
        -> ELIGIBILITY GATE (yalnızca VALIDATED yazılabilir)
        -> ContextManager (kontrollü write path)

Bu pipeline, modüllerin kendi içinde yaptığı context yazımını izole eder;
dünya modeline yazım tek noktadan (pipeline) ve eligibility kurallarına
göre yapılır.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.perception.adapter import SourceAdapter
from core.perception.model import PerceptionResult, EligibilityState, stamp_provenance
from core.evidence.model import Evidence, Observation


class PerceptionPipeline:
    """Algı boru hattı — kayıtlı adaptörler üzerinden algı yürütür, yalnızca
    eligibility gate'i geçen veriyi ContextManager'a yazar."""

    def __init__(self, context=None, logger=None, register_defaults: bool = True):
        self.context = context
        self.logger = logger
        self.adapters: Dict[str, SourceAdapter] = {}
        self.gaps: List[str] = []
        if register_defaults:
            self._register_builtin_adapters()

    # ------------------------------------------------------------------
    # Kayıt
    # ------------------------------------------------------------------
    def register(self, adapter: SourceAdapter) -> None:
        self.adapters[adapter.source.source_id] = adapter

    def _register_builtin_adapters(self) -> None:
        """whois ve social bilinen adaptörleri yükle (v1.4 başlangıç seti).

        Not: adaptörler modüllere (modules/*) bağımlıdır; bağımlılık yoksa
        pipeline geri kalanıyla çalışmaya devam eder.
        """
        try:
            from core.perception.adapters.whois import WhoisAdapter
            from core.perception.adapters.social import SocialAdapter
            self.register(WhoisAdapter(config={}, logger=self.logger, context=self.context))
            self.register(SocialAdapter(config={}, logger=self.logger, context=self.context))
        except Exception as e:  # pragma: no cover — bağımlılık yoksa sessiz
            if self.logger:
                self.logger.warning(f"Perception builtin adapters not available: {e}")

    # ------------------------------------------------------------------
    # Ana algı çağrısı
    # ------------------------------------------------------------------
    def perceive(self, source_id: str, target: str, **params) -> PerceptionResult:
        """Bir kaynağı hedef üzerinde algılar.

        Adımlar: perceive -> evidence -> validation -> eligibility -> write.
        Modül izole çalıştırıldığı için context yazımı YALNIZCA burada yapılır.
        """
        adapter = self.adapters.get(source_id)
        if adapter is None:
            return self._fail(source_id, target, f"kaynak kayıtlı değil: {source_id}")

        result = adapter.perceive(target, **params)
        if not result.ok:
            return result

        # --- 1. Evidence üretimi (mevcut engine) ---
        observation, evidence_list = self._build_evidence(result)

        # --- 2. Validasyon + eligibility ---
        written: List[Dict] = []
        rejected: List[Dict] = []
        for ent in result.normalized.get("entities", []):
            decision = self._gate_entity(ent, result)
            if decision.eligible:
                self._write_entity(ent, result)
                written.append({"type": "entity", "value": ent.get("value"),
                                "gate": decision.gate, "reason": decision.reason})
            else:
                rejected.append({"type": "entity", "value": ent.get("value"),
                                 "gate": decision.gate, "reason": decision.reason})

        for rel in result.normalized.get("relations", []):
            decision = self._gate_relation(rel, result)
            if decision.eligible:
                self._write_relation(rel, result)
                written.append({"type": "relation",
                                "value": f"{rel.get('src', {}).get('value')}->{rel.get('dst', {}).get('value')}",
                                "gate": decision.gate, "reason": decision.reason})
            else:
                rejected.append({"type": "relation",
                                 "value": f"{rel.get('src', {}).get('value')}->{rel.get('dst', {}).get('value')}",
                                 "gate": decision.gate, "reason": decision.reason})

        result.evidence = evidence_list
        result.observation = observation
        result.eligibility = {
            "written": len(written),
            "rejected": len(rejected),
            "gaps": list(self.gaps),
        }
        result.written = written
        result.rejected = rejected
        return result

# ------------------------------------------------------------------
    # Evidence üretimi (mevcut Evidence modeli kullanılır)
    # ------------------------------------------------------------------
    def _build_evidence(self, result: PerceptionResult):
        """Observation + Evidence listesi üretir.

        v1.4 kuralı: YENİ Evidence modeli YOK — core/evidence/model üzerine
        kurulur. EvidenceExtractor bu skelede standart 'relationships'
        üzerinden çalışır; bizden geldiği gibi normalized formu kullanırız.
        """
        target = result.target
        module = result.source.source_id
        obs = Observation(target=target, source_module=module, payload=result.normalized)

        evidence: List[Evidence] = []

        # Entities -> Evidence
        for ent in result.normalized.get("entities", []):
            ent_type = ent.get("type", "entity")
            value = str(ent.get("value", ""))
            evidence.append(Evidence(
                evidence_type=ent_type,
                observed_value=value,
                target=target,
                source_module=module,
                admiralty_code="B2",
                confidence=float(ent.get("confidence", 0.8)),
                raw_observation_id=obs.obs_id,
            ))

        # Relations -> Evidence (mevcut extractor formatıyla aynı formül)
        for rel in result.normalized.get("relations", []):
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            evidence.append(Evidence(
                evidence_type=rel.get("relation", "relates_to"),
                observed_value=f"{src.get('value', '?')} ==[{rel.get('relation', 'relates_to')}]==> {dst.get('value', '?')}",
                target=target,
                source_module=module,
                admiralty_code="B2",
                confidence=float(rel.get("confidence", 0.8)),
                raw_observation_id=obs.obs_id,
            ))

        return obs, evidence
# ------------------------------------------------------------------
    # ELIGIBILITY GATE (kontrat 3.6)
    # ------------------------------------------------------------------
    def _gate_entity(self, entity: Dict, result: PerceptionResult) -> EligibilityState:
        """Bir varlık dünya modeline yazılabilir mi?

        Kural: Evidence'in VAR olması tek başına yetmez — status/provenance/
        validation üçlüsü geçmeden yazılamaz (UNVERIFIABLE ve seed reddedilir).
        """
        ent_type = entity.get("type", "entity")
        value = str(entity.get("value", ""))
        if not value:
            return EligibilityState(False, "validation", "boş değer")

        # Seed koruması — kullanıcı girdisi doğrulanmış dünya gerçeği değildir
        prov = entity.get("provenance") or result.provenance or {}
        if prov.get("source") == "user_input" or prov.get("status") == "seed":
            return EligibilityState(False, "seed",
                                    "kullanıcı seed'i doğrulanmış dünya gerçeği olarak yazılamaz")

        status = self._validate_value(ent_type, value, entity)
        if status == "VALIDATED":
            return EligibilityState(True, "validation", "format doğrulandı")
        if status in ("SYNTAX_ERROR", "UNVERIFIABLE", "EXPIRED", "MALFORMED"):
            return EligibilityState(False, "validation",
                                    f"kanıt {status} — dünya modeline yazılamaz")
        return EligibilityState(False, "validation", f"doğrulanamayan kanıt statüsü: {status}")

    def _gate_relation(self, relation: Dict, result: PerceptionResult) -> EligibilityState:
        """İlişki yazılabilir mi? (evidence + confidence)"""
        src = relation.get("src", {})
        dst = relation.get("dst", {})
        if not src.get("value") or not dst.get("value"):
            return EligibilityState(False, "validation", "ilişki uçlarından biri boş")
        if float(relation.get("confidence", 0.8)) < 0.5:
            return EligibilityState(False, "evidence", "aday ilişki — confidence < 0.5")
        return EligibilityState(True, "evidence", "kanıta dayalı ilişki")

    def _validate_value(self, ent_type: str, value: str, _entity: Dict) -> str:
        """Mevcut EvidenceValidator desenleriyle sözdizim doğrulaması.

        v1.4 kuralı: mevcut validator mantığı kullanılır, yeni/paralel
        doğrulama hattı kurulmaz.
        """
        import re
        if ent_type in ("domain", "subdomain", "whois_server"):
            if re.match(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", value):
                return "VALIDATED"
        if ent_type == "ip":
            if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", value):
                return "VALIDATED"
        if ent_type == "email":
            if "@" in value and re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                return "VALIDATED"
        if ent_type in ("social_profile", "person", "organization", "username", "url"):
            if value and not value.endswith(("None", "null")):
                return "VALIDATED"
        return "UNVERIFIABLE"
# ------------------------------------------------------------------
    # Kontrollü write path (ContextManager'a yalnızca buradan yazılır)
    # ------------------------------------------------------------------
    def _write_entity(self, entity: Dict, result: PerceptionResult) -> None:
        if self.context is None:
            return
        prov = dict(entity.get("provenance") or {})
        prov["source"] = result.provenance.get("source", result.source.source_id)
        prov["source_url"] = result.provenance.get("source_url")
        prov["fetched_at"] = result.provenance.get("fetched_at")
        prov["method"] = result.provenance.get("method")
        prov["auth"] = result.provenance.get("auth")
        prov["raw_hash"] = result.provenance.get("raw_hash")
        prov.setdefault("status", "verified")
        self.context.add_entity(
            entity.get("type", "entity"),
            entity.get("value", ""),
            properties=entity.get("properties", {}),
            provenance=prov,
        )

    def _write_relation(self, relation: Dict, result: PerceptionResult) -> None:
        if self.context is None:
            return
        self.context.add_relation(
            relation.get("src", {}).get("type", "entity"),
            relation.get("src", {}).get("value", ""),
            relation.get("relation", "relates_to"),
            relation.get("dst", {}).get("type", "entity"),
            relation.get("dst", {}).get("value", ""),
            evidence=result.provenance.get("source"),
            confidence=float(relation.get("confidence", 0.8)),
        )

    # ------------------------------------------------------------------
    def _fail(self, source_id: str, target: str, reason: str) -> PerceptionResult:
        from core.perception.model import SourceDeclaration
        pseudo = SourceDeclaration(source_id=source_id, kind="unknown", auth_level="public")
        return PerceptionResult(
            ok=False, source=pseudo, target=target, target_type="unknown",
            raw=None, normalized={},
            provenance=stamp_provenance(pseudo, target, None),
            error=reason,
        )
        return result