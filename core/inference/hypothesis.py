"""Corvus Corax v1.1 - Hypothesis Engine.

Hipotez oluşturma, yaşam döngüsü ve durum geçişleri.

Hipotez Durumları:
  GENERATED  -> yeni oluşturuldu, henüz kanıt uygulanmadı
  ACTIVE     -> kanıtlar uygulandı, hâlâ kesinleşmedi (0.15 < posterior < 0.85)
  CONFIRMED  -> posterior >= 0.85 - yeterince desteklendi
  REFUTED    -> posterior <= 0.15 - kanıtlar tarafından çürütüldü
  SUSPENDED  -> yetersiz kanıt, araştırma budgeti tüketildi
  ARCHIVED   -> çürütüldü ve arşive alındı (silinmez, provenance için)
"""
import uuid
from datetime import datetime, timezone
from .bayesian import HypothesisBelief, get_prior


# Posterior eşikleri (Plan: confidence-gated)
CONFIRM_THRESHOLD = 0.85
REFUTE_THRESHOLD  = 0.15
SUSPEND_THRESHOLD = 0.30   # Uzun süre düşük kalırsa askıya al


class Hypothesis:
    """Tek bir çıkarım hipotezi."""

    def __init__(self, hypothesis_type: str, claim: str,
                 src_entity: str = "", src_type: str = "unknown",
                 dst_entity: str = "", dst_type: str = "unknown",
                 prior: float = None, seed_pattern_type: str = None):
        self.hypothesis_id = f"hyp-{uuid.uuid4().hex[:8]}"
        self.type = hypothesis_type   # OWNERSHIP, INFRASTRUCTURE, IDENTITY, BRIDGE, TEMPORAL, GEOGRAPHIC
        self.claim = claim
        self.src_entity = src_entity
        self.dst_entity = dst_entity
        self.src_type = src_type
        self.dst_type = dst_type
        self.seed_pattern_type = seed_pattern_type

        # Bayesian inanç durumu
        computed_prior = prior if prior is not None else get_prior(src_type, dst_type)
        self.belief = HypothesisBelief(prior=computed_prior, description=claim)

        # Kanıt izleme
        self.supporting_evidence_ids: list = []
        self.contradicting_evidence_ids: list = []

        # Durum
        self.status = "GENERATED"
        self.generated_at = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.generated_at

        # Açıklama ve provenance
        self.explanation: str = ""
        self.required_to_confirm: list = []   # Bu kanıtlar gelse confirmed olur
        self.required_to_refute: list = []    # Bu kanıtlar gelse refuted olur

    @property
    def posterior(self) -> float:
        return self.belief.posterior

    @property
    def prior(self) -> float:
        return self.belief.prior

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "type": self.type,
            "claim": self.claim,
            "src_entity": self.src_entity,
            "dst_entity": self.dst_entity,
            "src_type": self.src_type,
            "dst_type": self.dst_type,
            "status": self.status,
            "prior": self.prior,
            "posterior": self.posterior,
            "belief": self.belief.to_dict(),
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "contradicting_evidence_ids": self.contradicting_evidence_ids,
            "explanation": self.explanation,
            "required_to_confirm": self.required_to_confirm,
            "required_to_refute": self.required_to_refute,
            "seed_pattern_type": self.seed_pattern_type,
            "generated_at": self.generated_at,
            "last_updated": self.last_updated,
        }


class HypothesisGenerator:
    """Hipotez Üretici.

    Pattern, ilişki ve context'ten Hypothesis nesneleri üretir.
    """

    # Pattern -> hipotez tipi eşleşmesi
    PATTERN_TO_HYPOTHESIS_TYPE = {
        "OWNERSHIP":                   "OWNERSHIP",
        "MULTI_SOURCE_CORROBORATION":  "OWNERSHIP",
        "INFRASTRUCTURE_CLUSTER":      "INFRASTRUCTURE",
        "IDENTITY_ANCHOR":             "IDENTITY",
        "TEMPORAL_BURST":              "TEMPORAL",
        "GEOGRAPHIC_CONCENTRATION":    "GEOGRAPHIC",
    }

    def generate_from_pattern(self, pattern, entity: str = "") -> list:
        """Tespit edilmiş bir pattern'dan hipotez/ler üretir.

        Args:
            pattern: DetectedPattern nesnesi
            entity: Odak varlık değeri

        Returns:
            list[Hypothesis]
        """
        hypotheses = []
        hyp_type = self.PATTERN_TO_HYPOTHESIS_TYPE.get(pattern.pattern_type, "UNKNOWN")
        entities = pattern.entities

        if pattern.pattern_type == "OWNERSHIP" and len(entities) >= 2:
            src, dst = entities[0], entities[1]
            h = Hypothesis(
                hypothesis_type="OWNERSHIP",
                claim=f"'{src}' controls or owns '{dst}'",
                src_entity=src, src_type="person",
                dst_entity=dst, dst_type="domain",
                seed_pattern_type=pattern.pattern_type,
            )
            h.required_to_confirm = [
                f"Second independent source confirming {src} as registrant of {dst}",
                f"WHOIS or certificate authority record linking {src} to {dst}",
            ]
            h.required_to_refute = [
                f"Different registrant name in WHOIS for {dst}",
                f"Certificate issued to a different organization for {dst}",
            ]
            hypotheses.append(h)

        elif pattern.pattern_type == "MULTI_SOURCE_CORROBORATION" and len(entities) >= 2:
            subject, value = entities[0], entities[1]
            h = Hypothesis(
                hypothesis_type="OWNERSHIP",
                claim=f"'{value}' is reliably associated with '{subject}' (multi-source confirmed)",
                src_entity=subject, src_type="unknown",
                dst_entity=value, dst_type="unknown",
                prior=min(0.90, 0.50 + pattern.strength * 0.40),
                seed_pattern_type=pattern.pattern_type,
            )
            h.required_to_confirm = [
                "Additional independent source corroboration",
                "Physical or organizational record linkage",
            ]
            h.required_to_refute = [
                "Evidence that data sources share a common (unreliable) origin",
                "Contradicting record from authoritative registry",
            ]
            hypotheses.append(h)

        elif pattern.pattern_type == "INFRASTRUCTURE_CLUSTER" and len(entities) >= 2:
            hub = entities[0]
            members = entities[1:]
            h = Hypothesis(
                hypothesis_type="INFRASTRUCTURE",
                claim=(
                    f"'{hub}' is an infrastructure hub shared by: "
                    f"{', '.join(members[:4])}{'...' if len(members) > 4 else ''}"
                ),
                src_entity=hub, src_type="ip",
                dst_entity=str(members[:2]), dst_type="domain",
                seed_pattern_type=pattern.pattern_type,
            )
            h.required_to_confirm = [
                f"BGP/ASN records confirming {hub} serves multiple domains",
                "Certificate SAN covering multiple listed domains",
            ]
            h.required_to_refute = [
                "Domains resolving to different ASNs/providers",
                "No overlapping certificate or hosting records",
            ]
            hypotheses.append(h)

        elif pattern.pattern_type == "IDENTITY_ANCHOR" and len(entities) >= 2:
            anchor = entities[0]
            linked = entities[1:]
            h = Hypothesis(
                hypothesis_type="IDENTITY",
                claim=(
                    f"'{anchor}' is a unified identity controlling: "
                    f"{', '.join(linked[:3])}{'...' if len(linked) > 3 else ''}"
                ),
                src_entity=anchor, src_type="person",
                dst_entity=str(linked[:2]), dst_type="domain",
                seed_pattern_type=pattern.pattern_type,
            )
            h.required_to_confirm = [
                f"Government or organizational ID record linking {anchor} to listed assets",
                "Shared authentication credentials or certificate chains",
            ]
            h.required_to_refute = [
                "Evidence that assets are controlled by distinct legal entities",
                "Registrant records showing different individuals/organizations",
            ]
            hypotheses.append(h)

        elif pattern.pattern_type == "TEMPORAL_BURST":
            burst_entities = list(set(entities))[:4]
            h = Hypothesis(
                hypothesis_type="TEMPORAL",
                claim=(
                    f"Concentrated activity burst detected across: "
                    f"{', '.join(burst_entities)} - may indicate coordinated action"
                ),
                src_entity=entity, src_type="unknown",
                dst_entity=str(burst_entities), dst_type="unknown",
                prior=0.35,
                seed_pattern_type=pattern.pattern_type,
            )
            h.required_to_confirm = [
                "Additional temporal correlation across independent data sources",
                "Shared IP or ASN during the burst window",
            ]
            h.required_to_refute = [
                "Evidence burst explained by routine scan or automated process",
                "No shared infrastructure between entities during burst window",
            ]
            hypotheses.append(h)

        return hypotheses

    def generate_bridge_hypothesis(self, src_entity: str, dst_entity: str,
                                   bridge_type: str = "SHARED_INFRASTRUCTURE",
                                   intermediate_node: str = None) -> "Hypothesis":
        """Dynamic Bridge hipotezi üretir.

        Grafta doğrudan bağlantısı olmayan iki varlık arasındaki
        spekülatif dolaylı bağlantıyı modeller.
        """
        via_clause = f" via '{intermediate_node}'" if intermediate_node else ""
        claim = (
            f"'{src_entity}' and '{dst_entity}' may be indirectly connected"
            f"{via_clause} [{bridge_type.replace('_', ' ').title()} Bridge]"
        )

        # Bridge prior'ları kasıtlı olarak düşük - spekülatif
        bridge_priors = {
            "SHARED_INFRASTRUCTURE": 0.28,
            "TEMPORAL":             0.22,
            "TYPE_BASED":           0.25,
            "GEOGRAPHIC":           0.20,
        }
        prior = bridge_priors.get(bridge_type, 0.25)

        h = Hypothesis(
            hypothesis_type="BRIDGE",
            claim=claim,
            src_entity=src_entity, src_type="unknown",
            dst_entity=dst_entity, dst_type="unknown",
            prior=prior,
            seed_pattern_type=f"BRIDGE:{bridge_type}",
        )

        # Bridge için standart confirm/refute önerileri
        if bridge_type == "SHARED_INFRASTRUCTURE":
            h.required_to_confirm = [
                f"DNS resolution of '{src_entity}' and '{dst_entity}' to same ASN or hosting provider",
                f"Certificate SAN entries covering both '{src_entity}' and '{dst_entity}'",
                f"Shared IP or subnet assignment in BGP routing tables",
            ]
            h.required_to_refute = [
                f"'{src_entity}' and '{dst_entity}' resolve to geographically distinct ASNs",
                "No overlapping certificate, IP, or hosting infrastructure",
            ]
        elif bridge_type == "TEMPORAL":
            h.required_to_confirm = [
                "Domain registration or infrastructure changes occurring within same time window",
                "Shared administrative contact during overlapping activity period",
            ]
            h.required_to_refute = [
                "Activity timelines are non-overlapping",
                "No common registrar, host, or certificate authority during the period",
            ]
        else:
            h.required_to_confirm = [
                "Independent corroboration linking both entities through common attribute",
            ]
            h.required_to_refute = [
                "No shared attribute, infrastructure, or contact records found",
            ]

        return h

    def generate_competing_hypotheses(self, entity: str, relationships: list,
                                      patterns: list) -> list:
        """Birden fazla rakip hipotez üretir.

        Ana hipoteze alternatif açıklamalar da modele dahil edilir.
        Örnek: Ana -> 'A, B domain'ine sahip'
               Rakip -> 'A, bu domain'i başkası adına proxy olarak kullanıyor'
        """
        hypotheses = []

        # Önce pattern'lardan ana hipotezleri üret
        for pattern in patterns:
            hypotheses.extend(self.generate_from_pattern(pattern, entity))

        # Her ana hipotez için rakip alternatif üret
        competing = []
        for h in hypotheses:
            if h.type == "OWNERSHIP":
                alt = Hypothesis(
                    hypothesis_type="OWNERSHIP",
                    claim=(
                        f"'{h.src_entity}' acts as a proxy operator for '{h.dst_entity}' "
                        f"on behalf of an unknown third party"
                    ),
                    src_entity=h.src_entity, src_type=h.src_type,
                    dst_entity=h.dst_entity, dst_type=h.dst_type,
                    prior=get_prior(h.src_type, h.dst_type) * 0.5,  # Alt hipotez daha düşük prior
                    seed_pattern_type="COMPETING:" + (h.seed_pattern_type or ""),
                )
                alt.required_to_confirm = [
                    f"Third-party beneficial owner record for '{h.dst_entity}'",
                    f"Registrant address or contact not matching any known '{h.src_entity}' record",
                ]
                alt.required_to_refute = [
                    f"Direct personal/organizational record linking '{h.src_entity}' as beneficial owner",
                ]
                competing.append(alt)

        return hypotheses + competing


class HypothesisLifecycle:
    """Hipotez Yaşam Döngüsü Yöneticisi.

    Posterior'a göre durum geçişlerini yönetir ve hipotez depolarını sorgular.
    """

    def __init__(self):
        self._hypotheses: dict = {}   # hypothesis_id -> Hypothesis

    def register(self, hypothesis: "Hypothesis"):
        """Bir hipotezi yaşam döngüsü yönetimine kaydeder."""
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis

    def advance(self, hypothesis: "Hypothesis") -> str:
        """Posterior'a göre hipotez durumunu günceller.

        Args:
            hypothesis: Güncellenecek Hypothesis

        Returns:
            str - yeni durum
        """
        post = hypothesis.posterior
        prev_status = hypothesis.status

        if post >= CONFIRM_THRESHOLD:
            hypothesis.status = "CONFIRMED"
        elif post <= REFUTE_THRESHOLD:
            hypothesis.status = "REFUTED"
        elif hypothesis.status == "GENERATED":
            hypothesis.status = "ACTIVE"
        # ACTIVE kalır eğer ortada ise

        hypothesis.last_updated = datetime.now(timezone.utc).isoformat()

        # Explanation oluştur
        hypothesis.explanation = self._build_explanation(hypothesis)

        return hypothesis.status

    def advance_all(self) -> dict:
        """Tüm kayıtlı hipotezlerin durumunu günceller."""
        results = {}
        for hid, h in self._hypotheses.items():
            results[hid] = self.advance(h)
        return results

    def archive_refuted(self):
        """REFUTED hipotezleri ARCHIVED durumuna al. Silinmez - provenance için saklanır."""
        for h in self._hypotheses.values():
            if h.status == "REFUTED":
                h.status = "ARCHIVED"

    def get_by_status(self, status: str) -> list:
        return [h for h in self._hypotheses.values() if h.status == status]

    def get_active(self) -> list:
        return self.get_by_status("ACTIVE")

    def get_confirmed(self) -> list:
        return self.get_by_status("CONFIRMED")

    def get_refuted(self) -> list:
        return [h for h in self._hypotheses.values()
                if h.status in ("REFUTED", "ARCHIVED")]

    def get_all(self) -> list:
        return list(self._hypotheses.values())

    def get(self, hypothesis_id: str) -> "Hypothesis":
        return self._hypotheses.get(hypothesis_id)

    @staticmethod
    def _build_explanation(hypothesis: "Hypothesis") -> str:
        """İnsan-okunabilir provenance açıklaması üretir."""
        from .bayesian import BayesianUpdater
        trail = BayesianUpdater.build_trail_string(hypothesis.belief)
        n_supporting = len(hypothesis.supporting_evidence_ids)
        n_contradicting = len(hypothesis.contradicting_evidence_ids)

        lines = [
            f"Claim: {hypothesis.claim}",
            f"Bayesian Trail: {trail}",
            f"Supporting evidence: {n_supporting} record(s)",
        ]
        if n_contradicting:
            lines.append(f"Contradicting evidence: {n_contradicting} record(s)")
        if hypothesis.status == "CONFIRMED":
            lines.append("Assessment: Posterior exceeded confirmation threshold (>=0.85).")
        elif hypothesis.status == "REFUTED":
            lines.append("Assessment: Posterior fell below refutation threshold (<=0.15).")
        elif hypothesis.status == "ACTIVE":
            lines.append("Assessment: Hypothesis remains active - additional evidence needed.")

        return " | ".join(lines)
