"""Corvus Corax v1.1 - Negative Evidence & Absence Reasoning Engine.

"Yokluğun kendisi de bir kanıttır."
Bir keşif modülü çalıştığı halde beklenen bir kanıt/ilişki bulunamadığında,
bu durum yokluk kanıtı (absence of evidence) olarak değerlendirilir ve
hipotezin Bayesian inanç değerine negatif güncelleme uygular.

Örnekler:
  - DNS modülü çalıştı fakat MX kaydı dönmedi -> Email altyapısı yokluğu
  - WHOIS sorgulandı fakat registrant gizli -> Anonimlik / Proxy göstergesi
  - Port taraması yapıldı fakat web portları kapalı -> Doğrudan web sunucusu yokluğu
"""
from typing import Dict, List, Set, Any
from .bayesian import BayesianUpdater, HypothesisBelief


# Modüllere göre aranması ve bulunması beklenen temel kanıt tipleri
MODULE_EXPECTED_EVIDENCE = {
    "dns": {"ip", "cname", "mx", "ns", "txt"},
    "whois": {"registrant_name", "registrant_email", "registrar", "org"},
    "cert": {"san", "issuer", "validity"},
    "subdomain": {"subdomain"},
    "social": {"username", "profile_url"},
    "tech": {"cms", "server", "framework"},
}


class NegativeEvidenceEngine:
    """Yokluk ve Negatif Kanıt Değerlendirme Motoru."""

    def __init__(self, bayesian_updater: BayesianUpdater = None):
        self.updater = bayesian_updater or BayesianUpdater()

    def assess_expected_but_absent(self, entity_value: str, modules_run: List[str],
                                   observed_evidence_types: Set[str]) -> List[Dict[str, Any]]:
        """
        Çalıştırılan modüllerin sonucunda üretilmesi beklenen ancak gözlemlenmeyen
        kanıt tiplerini tespit eder.
        
        Args:
            entity_value: İncelenen hedef varlık
            modules_run: Çalıştırılan modül isimleri listesi (örn. ['dns', 'whois'])
            observed_evidence_types: Mevcut toplanmış kanıt tipleri kümesi
            
        Returns:
            list of dict: Eksik/yok olan kanıtların listesi ve analitik açıklamaları
        """
        absent_records = []
        observed_types = set(observed_evidence_types or set())

        for mod in modules_run:
            expected = MODULE_EXPECTED_EVIDENCE.get(mod.lower(), set())
            missing = expected - observed_types

            for ev_type in sorted(missing):
                absent_records.append({
                    "entity": entity_value,
                    "module": mod,
                    "absent_evidence_type": ev_type,
                    "strength": self._get_absence_strength(mod, ev_type),
                    "analytical_significance": self._get_significance_note(mod, ev_type),
                })

        return absent_records

    def apply_negative_evidence(self, belief: HypothesisBelief, absent_record: Dict[str, Any]) -> float:
        """
        Tespit edilen bir yokluk kaydını hipotez inancına negatif Bayesian güncelleme olarak uygular.
        
        Args:
            belief: HypothesisBelief nesnesi
            absent_record: assess_expected_but_absent çıktısından tek bir kayıt
            
        Returns:
            float: Güncellenen yeni posterior değeri
        """
        ev_type = absent_record.get("absent_evidence_type", "unknown")
        strength = absent_record.get("strength", 0.40)
        return self.updater.negative_update(belief, expected_evidence_type=ev_type, absence_strength=strength)

    def batch_apply_negative_evidence(self, hypotheses: List[Any], absent_records: List[Dict[str, Any]]) -> None:
        """
        Tüm ilgili hipotezlere negatif kanıtları uygular.
        """
        for record in absent_records:
            ev_type = record.get("absent_evidence_type")
            for h in hypotheses:
                # Eğer hipotez bu kanıt tipinin varlığına dayanıyorsa posterior düşürülür
                if self._is_hypothesis_impacted(h, ev_type):
                    self.apply_negative_evidence(h.belief, record)
                    h.contradicting_evidence_ids.append(f"absent:{record['module']}:{ev_type}")

    def _is_hypothesis_impacted(self, hypothesis: Any, absent_evidence_type: str) -> bool:
        """Hipotezin bu yokluktan etkilenip etkilenmeyeceğini belirler."""
        hyp_type = getattr(hypothesis, "type", "")
        # Örnek: OWNERSHIP hipotezi registrant_name yoksa veya INFRASTRUCTURE mx/ip yoksa etkilenir
        impact_map = {
            "OWNERSHIP": {"registrant_name", "registrant_email", "org"},
            "INFRASTRUCTURE": {"ip", "mx", "ns", "san"},
            "IDENTITY": {"username", "profile_url", "registrant_email"},
        }
        relevant_types = impact_map.get(hyp_type, set())
        return absent_evidence_type in relevant_types

    @staticmethod
    def _get_absence_strength(module: str, evidence_type: str) -> float:
        """Yokluğun kanıt gücü (P(E|H)). Düşük değer = H doğruysa yokluk daha beklenmediktir."""
        # DNS A kaydı yoksa domain aktif değil demektir -> çok güçlü negatif sinyal
        if module == "dns" and evidence_type == "ip":
            return 0.15
        if module == "whois" and evidence_type == "registrant_name":
            return 0.35  # Privacy guard yaygın olduğu için orta negatif sinyal
        if module == "cert" and evidence_type == "san":
            return 0.45
        return 0.40

    @staticmethod
    def _get_significance_note(module: str, evidence_type: str) -> str:
        """Yokluğun analitik anlamı."""
        notes = {
            ("dns", "ip"): "No A/AAAA resolution recorded; domain may be parked or inactive.",
            ("dns", "mx"): "No Mail Exchange (MX) records found; target likely lacks active email hosting.",
            ("whois", "registrant_name"): "Registrant identity unlisted or protected by privacy proxy.",
            ("cert", "san"): "No Subject Alternative Names found; certificate is single-host or wildcard.",
            ("social", "username"): "No public social profiles matched with high confidence.",
        }
        return notes.get((module, evidence_type), f"Expected '{evidence_type}' from '{module}' was absent.")
