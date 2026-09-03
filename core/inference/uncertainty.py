"""Corvus Corax v1.1 - Uncertainty Engine.

Hipotez belirsizliğini Shannon entropy ile ölçer ve
Corvus'un nerede emin olmadığını raporlar.

Shannon Entropy: H = -p*log2(p) - (1-p)*log2(1-p)
  H = 0.0 -> kesin (posterior 0 veya 1)
  H = 1.0 -> maksimum belirsizlik (posterior = 0.5)

Belirsizlik Seviyeleri:
  LOW      -> posterior > 0.85 veya < 0.15
  MEDIUM   -> 0.70-0.85 veya 0.15-0.30
  HIGH     -> 0.50-0.70 veya 0.30-0.50
  CRITICAL -> posterior ~0.5 (coin flip)
"""
import math


def compute_entropy(posterior: float) -> float:
    """Shannon entropy hesapla.

    Args:
        posterior: Hipotez posterior değeri [0.0 - 1.0]

    Returns:
        float - entropy [0.0 - 1.0]
    """
    p = max(1e-10, min(1.0 - 1e-10, float(posterior)))
    q = 1.0 - p
    return round(-(p * math.log2(p)) - (q * math.log2(q)), 4)


def assess_uncertainty_level(posterior: float) -> str:
    """Posterior'a göre belirsizlik seviyesi döner."""
    p = float(posterior)
    if p >= 0.85 or p <= 0.15:
        return "LOW"
    elif p >= 0.70 or p <= 0.30:
        return "MEDIUM"
    elif p >= 0.50 or p <= 0.50:
        # 0.40-0.60 aralığı CRITICAL
        if 0.40 <= p <= 0.60:
            return "CRITICAL"
        return "HIGH"
    return "HIGH"


class UncertaintyEngine:
    """Belirsizlik Analiz ve Raporlama Motoru."""

    def generate_uncertainty_report(self, hypotheses: list) -> list:
        """Hipotez listesi için belirsizlik raporu üretir.

        Args:
            hypotheses: Hypothesis nesneleri listesi

        Returns:
            list[dict] - her hipotez için belirsizlik kaydı
        """
        report = []
        for h in hypotheses:
            posterior = h.posterior
            entropy = compute_entropy(posterior)
            level = assess_uncertainty_level(posterior)
            uncertainty_note = self._uncertainty_narrative(h, level, entropy)

            report.append({
                "hypothesis_id": h.hypothesis_id,
                "claim": h.claim,
                "posterior": round(posterior, 4),
                "entropy": entropy,
                "uncertainty_level": level,
                "uncertainty_note": uncertainty_note,
                "update_count": h.belief.update_count,
                "status": h.status,
            })

        # En belirsizden en keshine sırala
        report.sort(key=lambda x: x["entropy"], reverse=True)
        return report

    def find_critical_uncertainties(self, hypotheses: list) -> list:
        """CRITICAL veya HIGH belirsizliğe sahip hipotezleri döner."""
        return [
            h for h in hypotheses
            if assess_uncertainty_level(h.posterior) in ("CRITICAL", "HIGH")
            and h.status not in ("ARCHIVED",)
        ]

    def generate_knowledge_gaps(self, hypotheses: list, entity: str,
                                modules_run: list = None) -> list:
        """'WHAT CORVUS DOES NOT KNOW' listesi üretir.

        Args:
            hypotheses: Tüm hipotezler
            entity: Hedef varlık
            modules_run: Çalıştırılan modüllerin listesi

        Returns:
            list[str] - bilgi boşluğu açıklamaları
        """
        gaps = []
        modules_run = set(modules_run or [])

        # Kritik belirsizlik olan hipotezleri raporla
        for h in hypotheses:
            level = assess_uncertainty_level(h.posterior)
            if level == "CRITICAL":
                gaps.append(
                    f"Hypothesis '{h.claim[:60]}...' is at maximum uncertainty "
                    f"(posterior={h.posterior:.2f}) - coin-flip level, cannot determine truth"
                )
            elif level == "HIGH" and h.status == "ACTIVE":
                gaps.append(
                    f"Hypothesis '{h.claim[:60]}...' remains unresolved "
                    f"(posterior={h.posterior:.2f}, {h.belief.update_count} evidence applied)"
                )

        # Çalıştırılmamış modüller -> potansiyel eksik kanıt
        all_useful_modules = {"dns", "whois", "cert", "social", "subdomain", "geoip", "asn"}
        missing_modules = all_useful_modules - modules_run
        if missing_modules:
            gaps.append(
                f"The following recon modules have not been run: "
                f"{', '.join(sorted(missing_modules))} - potential evidence sources unexplored"
            )

        # Hiç hipotez oluşturulmadıysa
        if not hypotheses:
            gaps.append(
                f"No hypotheses could be generated for '{entity}' - "
                f"insufficient evidence baseline. Run initial recon modules first."
            )

        # Çürütülmüş hipotezleri de raporla (ne olmadığını bilmek de değerli)
        refuted = [h for h in hypotheses if h.status in ("REFUTED", "ARCHIVED")]
        if refuted:
            gaps.append(
                f"{len(refuted)} hypothesis/hypotheses were REFUTED - "
                f"these explanations are considered unlikely: "
                f"{'; '.join(h.claim[:40] for h in refuted[:2])}"
            )

        return gaps

    @staticmethod
    def _uncertainty_narrative(hypothesis, level: str, entropy: float) -> str:
        """Belirsizlik seviyesi için açıklayıcı metin üretir."""
        p = hypothesis.posterior
        narratives = {
            "LOW": (
                f"Corvus is {'highly confident' if p >= 0.85 else 'strongly doubtful'} "
                f"about this hypothesis (entropy: {entropy:.3f}). "
                f"{'Conclusion is treated as near-definitive.' if p >= 0.85 else 'This hypothesis is near-refuted.'}"
            ),
            "MEDIUM": (
                f"Corvus has moderate confidence (posterior={p:.2f}, entropy={entropy:.3f}). "
                "Additional corroborating evidence would solidify or dismiss this claim."
            ),
            "HIGH": (
                f"Corvus is uncertain about this hypothesis (posterior={p:.2f}, entropy={entropy:.3f}). "
                "Significant additional evidence required before any conclusion can be drawn."
            ),
            "CRITICAL": (
                f"Corvus is at maximum uncertainty (posterior={p:.2f}, entropy={entropy:.3f} ≈ 1.0). "
                "This hypothesis is no better than a coin flip at current evidence levels. "
                "Do NOT treat as actionable intelligence."
            ),
        }
        return narratives.get(level, "Uncertainty level unknown.")
