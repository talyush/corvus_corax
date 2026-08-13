import re
from datetime import datetime, timezone

from core.module_base import BaseModule
from core.config import load_rules


class PhoneIntelModule(BaseModule):
    """
    v0.9 — Telefon İstihbarat Modülü.

    Telefon numarasını analiz eder:
    - Format doğrulama & normalizasyon (ülke kodu çıkarımı)
    - Operatör prefix tespiti (prefix_detected + evidence/basis ayrımı)
    - Numara tipi sınıflandırması (mobil/sabit/özel servis)
    - Kişiye aday bağlantı kurma (candidate_link — KESİN sahiplik değil)
    """
    name = "phone"

    def _normalize_number(self, raw):
        """Numarayı normalize eder: sadece rakamlar, +90/90 önek tespiti."""
        if not raw:
            return None
        # Tüm non-digit karakterleri kaldır
        digits = re.sub(r"\D", "", raw)
        if not digits:
            return None

        # Ülke kodu tespiti
        country_code = None
        local_number = digits
        if digits.startswith("90") and len(digits) >= 12:
            country_code = "90"
            local_number = digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
            country_code = "90"
            local_number = digits[1:]

        return {
            "original": raw,
            "digits": digits,
            "country_code": country_code,
            "local_number": local_number,
            "e164": (f"+{country_code}{local_number}" if country_code else digits),
        }

    def _detect_operator(self, local_number, country_code):
        """
        Operatör prefix tespiti — config/rules.json'daki operator_prefixes kullanılır.
        ÖNEMLİ: Bu sadece 'prefix_detected' tahminidir, kesin operatör değildir.
        Numara taşınabilirliği (MNP) nedeniyle gerçek operatör doğrulanamaz.
        """
        rules = load_rules()
        prefixes = rules.get("operator_prefixes", {}).get(str(country_code), {})

        if not local_number or len(local_number) < 3:
            return None

        # En uzun eşleşen prefix'i bul (3 haneli mobil prefix'ler)
        candidate_prefix = local_number[:3]
        if candidate_prefix in prefixes:
            prefix_info = prefixes[candidate_prefix]
            return {
                "prefix_detected": candidate_prefix,
                "possible_operator": prefix_info.get("operator"),
                "basis": prefix_info.get("basis", "numbering_plan"),
                "confidence": 0.4,  # MNP nedeniyle düşük güven — kesin değil
                "note": "Number portability (MNP) may apply — verify via live operator lookup",
            }
        return {
            "prefix_detected": candidate_prefix,
            "possible_operator": "Unknown",
            "basis": "no_match",
            "confidence": 0.0,
            "note": "No operator prefix match in current numbering plan",
        }

    def _detect_number_type(self, local_number, country_code):
        """Numara tipini sınıflandırır (mobil/sabit/özel servis)."""
        if not local_number:
            return "unknown"

        # Türkiye (90) için
        if country_code == "90":
            if local_number.startswith("5") and len(local_number) == 10:
                return "mobile"
            elif local_number.startswith("2") and len(local_number) == 10:
                return "landline"
            elif local_number.startswith("8"):
                return "premium"
        return "unknown"

    def execute(self):
        target = self.target
        if not target:
            return self.error("No phone number provided. Usage: phone <number> [person_name]")

        # Hedef: ya "numperson" ya da sadece "num"
        number_input = target[0] if target else ""
        person_name = None
        if len(target) >= 2:
            person_name = target[1]

        self.begin_investigation(
            goal="Phone Intelligence Analysis",
            phases=[
                (1, "NUMBER NORMALIZATION"),
                (2, "OPERATOR PREFIX DETECTION"),
                (3, "ENTITY RELATIONSHIP MAPPING"),
            ],
        )

        # 1. Numara normalizasyonu
        def run_normalize():
            norm = self._normalize_number(number_input)
            if not norm:
                raise ValueError(f"Invalid phone number: {number_input}")
            return norm

        self.status_step(f"Normalizing number {number_input}", work=run_normalize)
        normalized = self._normalize_number(number_input)
        if not normalized:
            return self.error(f"Invalid phone number: {number_input}")

        # 2. Operatör prefix tespiti
        def run_operator():
            return self._detect_operator(normalized["local_number"], normalized["country_code"])

        self.status_step("Detecting operator prefix", work=run_operator)
        operator_info = self._detect_operator(normalized["local_number"], normalized["country_code"])

        # 3. Numara tipi
        number_type = self._detect_number_type(normalized["local_number"], normalized["country_code"])
        self.status_step(f"Classifying number type ({number_type})")

        # --- Varlık Kaydı ---
        phone_props = {
            "e164": normalized["e164"],
            "country_code": normalized["country_code"],
            "local_number": normalized["local_number"],
            "number_type": number_type,
            "operator": operator_info,
        }
        self.add_entity("phone", normalized["e164"], phone_props)

        # --- Temporal Olaylar ---
        self.log_event("phone_analyzed", entity=f"phone:{normalized['e164']}",
                       metadata={"number_type": number_type})
        if operator_info and operator_info.get("prefix_detected"):
            self.log_event("prefix_detected", entity=f"phone:{normalized['e164']}",
                           metadata={"prefix": operator_info["prefix_detected"],
                                     "possible_operator": operator_info.get("possible_operator"),
                                     "basis": operator_info.get("basis")})

        # --- İlişkiler ---
        self.add_relation(
            "phone", normalized["e164"], "has_number_type", "number_type", number_type,
            evidence=f"Number classified as {number_type} (E.164: {normalized['e164']})",
            confidence=0.9,
        )

        if operator_info and operator_info.get("possible_operator") != "Unknown":
            self.add_relation(
                "phone", normalized["e164"], "possible_operator", "operator", operator_info["possible_operator"],
                evidence=f"Prefix {operator_info['prefix_detected']} maps to {operator_info['possible_operator']} "
                         f"(basis: {operator_info['basis']})",
                confidence=operator_info["confidence"],
            )

        # --- Kişiye Aday Bağlantı (candidate_link — KESİN sahiplik değil) ---
        if person_name:
            self.add_person(person_name)
            self.add_relation(
                "phone", normalized["e164"], "phone_candidate_for", "person", person_name,
                evidence=f"User-provided association: phone {normalized['e164']} linked to {person_name} as candidate",
                confidence=0.4,  # candidate — kanıt doğrulanmadı
            )
            self.log_event("phone_candidate_for", entity=f"person:{person_name}",
                           metadata={"phone": normalized["e164"], "confidence": 0.4})

        self.add_note(
            f"Phone {normalized['e164']} analyzed — type: {number_type}, "
            f"operator prefix: {operator_info.get('possible_operator', 'unknown')} "
            f"(basis: {operator_info.get('basis', 'n/a')}, conf: {operator_info.get('confidence', 0)})",
            severity="info", confidence=0.7,
        )

        data = {
            "phone": normalized["e164"],
            "original_input": number_input,
            "country_code": normalized["country_code"],
            "local_number": normalized["local_number"],
            "number_type": number_type,
            "operator_prefix": operator_info,
            "person_candidate": person_name,
        }
        return self.success(target=number_input, data=data)