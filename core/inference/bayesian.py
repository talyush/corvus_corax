"""Corvus Corax v1.1 - Bayesian Inference Engine.

Gerçek Bayes formülü:
    P(H|E) = P(E|H) * P(H) / P(E)
    P(E)   = P(E|H)*P(H) + P(E|¬H)*(1-P(H))

Her kanıt geldiğinde prior -> posterior güncellenir ve bu posterior
bir sonraki kanıt için yeni prior olur (sequential Bayesian updating).
"""
import uuid
import math
from datetime import datetime, timezone
from .evidence_weight import EvidenceWeighter


# Entity tip çiftleri için type-informed prior tablosu (Plan: Option B)
PRIOR_TABLE = {
    ("person",   "domain"):  0.40,
    ("person",   "email"):   0.50,
    ("person",   "ip"):      0.25,
    ("person",   "cert"):    0.30,
    ("person",   "org"):     0.45,
    ("domain",   "ip"):      0.65,
    ("domain",   "domain"):  0.20,
    ("domain",   "cert"):    0.72,
    ("domain",   "email"):   0.40,
    ("ip",       "ip"):      0.20,
    ("ip",       "domain"):  0.55,
    ("ip",       "asn"):     0.75,
    ("email",    "domain"):  0.60,
    ("email",    "person"):  0.45,
    ("org",      "domain"):  0.55,
    ("org",      "ip"):      0.40,
    # Bridge tipi için özel - spekülatif, kasıtlı olarak düşük
    ("bridge",   "any"):     0.28,
}
DEFAULT_PRIOR = 0.35


def get_prior(src_type: str, dst_type: str) -> float:
    """Entity tip çiftine göre type-informed prior döner."""
    key = (src_type.lower(), dst_type.lower())
    if key in PRIOR_TABLE:
        return PRIOR_TABLE[key]
    # Ters sıra da dene
    rev_key = (dst_type.lower(), src_type.lower())
    if rev_key in PRIOR_TABLE:
        return PRIOR_TABLE[rev_key] * 0.9  # Ters yön biraz daha belirsiz
    return DEFAULT_PRIOR


class HypothesisBelief:
    """Bayesian Hipotez İnanç Durumu.

    Bir hipotezin prior'dan posterior'a güncelleme geçmişini tutar.
    """

    def __init__(self, prior: float, description: str = ""):
        self.belief_id = f"bel-{uuid.uuid4().hex[:8]}"
        self.description = description
        self.prior = round(float(prior), 6)
        self.posterior = round(float(prior), 6)
        self.likelihood_history: list = []  # [(evidence_id, p_e_h, p_e_not_h, prior_before, posterior_after)]
        self.update_count = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.created_at

    def apply_update(self, evidence_id: str, p_e_h: float, p_e_not_h: float):
        """Tek bir kanıt güncelleme adımını uygular ve posterior'ı günceller."""
        prior_before = self.posterior

        # P(E) = P(E|H)*P(H) + P(E|¬H)*(1-P(H))
        p_e = (p_e_h * prior_before) + (p_e_not_h * (1.0 - prior_before))

        if p_e < 1e-10:
            # Numerik kararlılık - sıfır bölme önlemi
            posterior_after = prior_before
        else:
            # P(H|E) = P(E|H) * P(H) / P(E)
            posterior_after = (p_e_h * prior_before) / p_e

        posterior_after = round(min(0.999, max(0.001, posterior_after)), 6)
        delta = round(posterior_after - prior_before, 6)

        self.likelihood_history.append({
            "evidence_id": evidence_id,
            "p_e_given_h": round(p_e_h, 4),
            "p_e_given_not_h": round(p_e_not_h, 4),
            "prior_before": round(prior_before, 4),
            "posterior_after": round(posterior_after, 4),
            "delta": round(delta, 4),
        })

        self.posterior = posterior_after
        self.update_count += 1
        self.last_updated = datetime.now(timezone.utc).isoformat()
        return posterior_after

    def to_dict(self) -> dict:
        return {
            "belief_id": self.belief_id,
            "prior": self.prior,
            "posterior": self.posterior,
            "update_count": self.update_count,
            "likelihood_history": self.likelihood_history,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }


class BayesianUpdater:
    """Bayesian Güncelleme Motoru.

    Kanıt listesini alır, sırayla posterior günceller, güncelleme geçmişini tutar.
    """

    def __init__(self):
        self.weighter = EvidenceWeighter()

    def compute_likelihood(self, evidence) -> tuple:
        """Kanıt için P(E|H) ve P(E|¬H) çifti hesaplar.

        Admiralty kodu temel değerini EvidenceWeighter'dan alır,
        sonra ağırlık faktörüyle modüle eder.

        Returns:
            (p_e_given_h: float, p_e_given_not_h: float)
        """
        p_e_h, p_e_not_h = self.weighter.compute_likelihood(evidence)
        weight = self.weighter.compute_weight(evidence)

        # Ağırlık 1.0'ın üzerindeyse likelihood H lehine biraz güçlenir
        if weight > 1.0:
            boost = min(0.05, (weight - 1.0) * 0.05)
            p_e_h = min(0.99, p_e_h + boost)
            p_e_not_h = max(0.01, p_e_not_h - boost)
        elif weight < 0.5:
            # Zayıf kanıt -> likelihood ortaya çeker (daha az bilgi verici)
            midpoint = 0.50
            factor = weight * 2  # 0.0-1.0 arası
            p_e_h = p_e_h * factor + midpoint * (1 - factor)
            p_e_not_h = p_e_not_h * factor + midpoint * (1 - factor)

        return (round(p_e_h, 4), round(p_e_not_h, 4))

    def update(self, belief: HypothesisBelief, evidence) -> float:
        """Tek bir kanıtla hipotez inancını günceller.

        Args:
            belief: Güncellenecek HypothesisBelief
            evidence: Evidence nesnesi

        Returns:
            float - yeni posterior değeri
        """
        ev_id = getattr(evidence, "id", str(uuid.uuid4().hex[:8]))
        p_e_h, p_e_not_h = self.compute_likelihood(evidence)
        return belief.apply_update(ev_id, p_e_h, p_e_not_h)

    def batch_update(self, belief: HypothesisBelief, evidence_list: list) -> float:
        """Kanıt listesini sırayla uygulayarak posterior'ı günceller.

        Her kanıt bir öncekinin posterior'unu yeni prior olarak alır
        (sequential Bayesian updating).

        Args:
            belief: Güncellenecek HypothesisBelief
            evidence_list: Evidence nesneleri listesi (kronolojik sıra önerilir)

        Returns:
            float - final posterior
        """
        # Kanıtları timestamp'e göre sırala (en eski önce)
        sorted_evs = sorted(
            evidence_list,
            key=lambda e: getattr(e, "timestamp", "") or ""
        )
        for ev in sorted_evs:
            self.update(belief, ev)
        return belief.posterior

    def negative_update(self, belief: HypothesisBelief, expected_evidence_type: str,
                        absence_strength: float = 0.4) -> float:
        """Beklenen ama YOK olan kanıt için negatif Bayesian güncelleme.

        Bir modül çalıştı ama beklenen kanıt türü görülmedi.
        Bu yokluk da bir sinyal: P(E|H) düşük -> posterior düşer.

        Args:
            belief: Güncellenecek HypothesisBelief
            expected_evidence_type: Beklenen ama bulunamayan kanıt türü
            absence_strength: Yokluğun güçlülüğü [0.1-0.7], default 0.4 (orta)

        Returns:
            float - yeni posterior
        """
        # Yokluk kanıtı için: P(E|H) = absence_strength (H doğru olsa bu kanıt olurdu)
        # P(E|¬H) = 1.0 - absence_strength (H yanlışsa yokluk beklenir zaten)
        p_e_h = round(absence_strength, 4)
        p_e_not_h = round(1.0 - absence_strength, 4)

        ev_id = f"absent:{expected_evidence_type}"
        return belief.apply_update(ev_id, p_e_h, p_e_not_h)

    @staticmethod
    def build_trail_string(belief: HypothesisBelief) -> str:
        """İnsan-okunabilir Bayesian güncelleme izi (trail) üretir.

        Örnek: 'Prior 0.40 -> [ev-001] +0.23 -> 0.63 -> [ev-002] +0.15 -> 0.78'
        """
        if not belief.likelihood_history:
            return f"Prior {belief.prior:.2f} (no updates applied)"

        parts = [f"Prior {belief.prior:.2f}"]
        for step in belief.likelihood_history:
            ev_id = step["evidence_id"]
            delta = step["delta"]
            post = step["posterior_after"]
            sign = "+" if delta >= 0 else ""
            parts.append(f"[{ev_id}] {sign}{delta:.3f} -> {post:.2f}")

        return " -> ".join(parts)
