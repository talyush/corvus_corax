"""Corvus Corax v1.1 - Counterfactual & Alternative Explanation Engine.

"Bunu değiştirecek ne tür kanıt lazım?"
"Başka ne düşünebilirsin?"

CounterfactualEngine:
  what_would_confirm(hypothesis)   -> Bu hipotezi doğrulayacak kanıt türleri
  what_would_refute(hypothesis)    -> Bu hipotezi çürütecek kanıt türleri
  generate_alternative_explanations(hypotheses) -> Onaylanan hipoteze alternatif açıklama
"""
from .bayesian import BayesianUpdater, HypothesisBelief, get_prior


class CounterfactualEngine:
    """Karşıolgusal ve Alternatif Açıklama Motoru."""

    def what_would_confirm(self, hypothesis) -> dict:
        """Bu hipotezi doğrulamak için hangi kanıtlar gerekir?

        Mevcut posterior'dan yola çıkarak CONFIRM_THRESHOLD'a (0.85) ulaşmak
        için ne tür kanıtların kaç tane gelmesi gerektiğini hesaplar.

        Returns:
            dict with required_evidence_types, estimated_count, current_gap, prescribed_actions
        """
        posterior = hypothesis.posterior
        gap = 0.85 - posterior

        # Önceden tanımlanmış kanıt gereksinimleri (hipotez üretiminde atandı)
        predefined = hypothesis.required_to_confirm or []

        # Kaç tane A1 kanıt gelse yeterli olurdu? (simülasyon)
        needed_strong, needed_moderate = self._simulate_needed_updates(
            prior=posterior, target=0.85
        )

        prescribed_actions = self._prescribe_actions(hypothesis)

        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "direction": "CONFIRM",
            "current_posterior": round(posterior, 4),
            "target_posterior": 0.85,
            "gap": round(gap, 4),
            "predefined_requirements": predefined,
            "estimated_strong_evidence_needed": needed_strong,    # A1/A2 kanıtlar
            "estimated_moderate_evidence_needed": needed_moderate, # B2/C3 kanıtlar
            "prescribed_actions": prescribed_actions,
            "note": (
                f"Hypothesis is currently at posterior={posterior:.2f}. "
                f"~{needed_strong} high-reliability (A1) evidence items would confirm it, "
                f"or ~{needed_moderate} moderate-reliability (B2) items."
            ),
        }

    def what_would_refute(self, hypothesis) -> dict:
        """Bu hipotezi çürütmek için hangi kanıtlar gerekir?

        Returns:
            dict with required_evidence_types, estimated_count, current_gap, prescribed_actions
        """
        posterior = hypothesis.posterior
        gap = posterior - 0.15

        predefined = hypothesis.required_to_refute or []
        needed_strong, needed_moderate = self._simulate_needed_updates(
            prior=posterior, target=0.15, direction="refute"
        )

        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "direction": "REFUTE",
            "current_posterior": round(posterior, 4),
            "target_posterior": 0.15,
            "gap": round(gap, 4),
            "predefined_requirements": predefined,
            "estimated_strong_counter_evidence_needed": needed_strong,
            "estimated_moderate_counter_evidence_needed": needed_moderate,
            "note": (
                f"Hypothesis is currently at posterior={posterior:.2f}. "
                f"~{needed_strong} strongly contradicting (A1) evidence items would refute it, "
                f"or ~{needed_moderate} moderate (B2) contradicting items."
            ),
        }

    def generate_alternative_explanations(self, confirmed_hypotheses: list,
                                          all_hypotheses: list) -> list:
        """Onaylanmış hipotezlere alternatif açıklamalar üretir.

        "Corvus bunu düşünüyor, ama başka ne düşünebilir?"

        Args:
            confirmed_hypotheses: Status=CONFIRMED hipotezler
            all_hypotheses: Tüm hipotezler (ACTIVE olanlar zaten alternatif adayı)

        Returns:
            list[dict] - alternatif açıklamalar
        """
        alternatives = []

        # ACTIVE hipotezler doğal alternatiflerdir
        active = [h for h in all_hypotheses if h.status == "ACTIVE"]
        competing_types = {
            "OWNERSHIP":      "Proxy/Fronting",
            "INFRASTRUCTURE": "Coincidental Hosting",
            "IDENTITY":       "Name/Alias Collision",
            "TEMPORAL":       "Routine Scan Activity",
            "BRIDGE":         "Unrelated Infrastructure Sharing",
        }

        for confirmed in confirmed_hypotheses:
            # Aynı varlıkları içeren ACTIVE hipotezler
            rival_actives = [
                h for h in active
                if (h.src_entity == confirmed.src_entity or
                    h.dst_entity == confirmed.dst_entity)
                and h.hypothesis_id != confirmed.hypothesis_id
            ]

            if rival_actives:
                for rival in rival_actives[:2]:
                    alternatives.append({
                        "confirmed_hypothesis_id": confirmed.hypothesis_id,
                        "confirmed_claim": confirmed.claim,
                        "alternative_hypothesis_id": rival.hypothesis_id,
                        "alternative_claim": rival.claim,
                        "alternative_posterior": round(rival.posterior, 4),
                        "interpretation": (
                            f"While '{confirmed.claim[:50]}...' appears confirmed, "
                            f"an alternative explanation remains active: '{rival.claim[:50]}...'"
                            f" (posterior={rival.posterior:.2f})"
                        ),
                    })
            else:
                # Standart alternatif açıklama üret
                alt_type = competing_types.get(confirmed.type, "Unknown Alternative")
                alternatives.append({
                    "confirmed_hypothesis_id": confirmed.hypothesis_id,
                    "confirmed_claim": confirmed.claim,
                    "alternative_hypothesis_id": None,
                    "alternative_claim": (
                        f"Alternative ({alt_type}): "
                        f"The observed pattern may be explained by {alt_type.lower()} "
                        f"rather than direct ownership/control by '{confirmed.src_entity}'"
                    ),
                    "alternative_posterior": round(
                        max(0.05, 1.0 - confirmed.posterior - 0.05), 4
                    ),
                    "interpretation": (
                        f"Confirmed claim: '{confirmed.claim[:50]}...'. "
                        f"Alternative: {alt_type} scenario cannot be ruled out without "
                        f"additional identity-linking evidence."
                    ),
                })

        return alternatives

    @staticmethod
    def _simulate_needed_updates(prior: float, target: float,
                                 direction: str = "confirm") -> tuple:
        """Hedef posterior'a ulaşmak için kaç kanıt gerektiğini simüle eder.

        Returns:
            (needed_strong: int, needed_moderate: int)
            - A1 (güçlü) ve B2 (orta) kanıt adedi tahminleri
        """
        # P(E|H), P(E|¬H) değerleri - A1 ve B2 için
        A1 = (0.95, 0.05)
        B2 = (0.82, 0.18)

        def simulate(p_e_h, p_e_not_h, current, goal, direction):
            count = 0
            post = current
            max_iter = 20
            while count < max_iter:
                p_e = p_e_h * post + p_e_not_h * (1.0 - post)
                if direction == "confirm":
                    post = (p_e_h * post) / p_e if p_e > 0 else post
                    if post >= goal:
                        break
                else:
                    # Refute: çelişkili kanıt -> P(E|H) ve P(E|¬H) tersine çevrilmiş
                    p_e = p_e_not_h * post + p_e_h * (1.0 - post)
                    post = (p_e_not_h * post) / p_e if p_e > 0 else post
                    if post <= goal:
                        break
                count += 1
            return count + 1

        strong = simulate(A1[0], A1[1], prior, target, direction)
        moderate = simulate(B2[0], B2[1], prior, target, direction)
        return (strong, moderate)

    @staticmethod
    def _prescribe_actions(hypothesis) -> list:
        """Hipotez tipine göre önerilen recon aksiyonlarını döner."""
        type_actions = {
            "OWNERSHIP": [
                "Run 'whois' module to retrieve registrant records",
                "Run 'cert' module to check certificate SAN and organization fields",
                "Run 'dns' module to confirm A/CNAME resolution chain",
            ],
            "INFRASTRUCTURE": [
                "Run 'asn' module to retrieve BGP/ASN routing table entry",
                "Run 'cert' module to find SAN-grouped domains on same certificate",
                "Run 'netscan' on related IP ranges",
            ],
            "IDENTITY": [
                "Run 'social' or 'identity' module to cross-reference person attributes",
                "Run 'email' module to validate email-to-domain linkage",
                "Search for shared registration contacts across known domains",
            ],
            "TEMPORAL": [
                "Retrieve historical WHOIS or DNS data for temporal comparison",
                "Run 'cert' module to check certificate issuance timestamps",
            ],
            "BRIDGE": [
                "Run 'dns' module on both entities to check common resolution",
                "Run 'cert' module to find shared SAN certificates",
                "Run 'asn' module to check BGP path overlap",
            ],
        }
        return type_actions.get(hypothesis.type, [
            "Run available recon modules to gather additional evidence",
        ])
