"""Corvus Corax Evidence Extractor.

Modül ham çıktılarını Observation nesnelerine ve atomik Evidence kayıtlarına dönüştürür.
"""
from core.evidence.model import Observation, Evidence


class EvidenceExtractor:
    """Gözlem ve kanıt çıkarma motoru."""

    def __init__(self):
        self.observations = []
        self.evidence_store = []

    def create_observation(self, target, source_module, payload) -> Observation:
        """Modül payload'ından ham gözlem (Observation) nesnesi üretir."""
        obs = Observation(target=target, source_module=source_module, payload=payload)
        self.observations.append(obs)
        return obs

    def extract_evidence_from_result(self, module_result) -> list:
        """Bir modülün çalıştırılma sonucundan atomik kanıtlar çıkarır."""
        if not module_result or not isinstance(module_result, dict):
            return []

        target = module_result.get("target", "unknown")
        module_name = module_result.get("module", "unknown")
        data = module_result.get("data", {})

        obs = self.create_observation(target=target, source_module=module_name, payload=data)

        extracted = []

        # 1. İlişkilerden (relationships) kanıt çıkarma
        relationships = module_result.get("relationships", [])
        for rel in relationships:
            src = rel.get("src", {})
            dst = rel.get("dst", {})
            relation = rel.get("relation", "relates_to")
            conf = rel.get("confidence", 0.8)

            ev_val = f"{src.get('value')} ==[{relation}]==> {dst.get('value')}"
            ev = Evidence(
                evidence_type=relation,
                observed_value=ev_val,
                target=target,
                source_module=module_name,
                admiralty_code="B2",
                confidence=conf,
                raw_observation_id=obs.obs_id,
            )
            extracted.append(ev)
            self.evidence_store.append(ev)

        # 2. Özel veri alanlarından kanıt çıkarma (IP, Geo, Cert, Tech)
        if "ip" in data:
            ev = Evidence("ip_resolution", str(data["ip"]), target, module_name, "A1", 0.95, raw_observation_id=obs.obs_id)
            extracted.append(ev)
            self.evidence_store.append(ev)

        if "open_ports" in data and isinstance(data["open_ports"], list):
            for p in data["open_ports"]:
                port_str = f"{p.get('port')}/{p.get('service', 'unknown')}"
                ev = Evidence("open_port", port_str, target, module_name, "A1", 0.9, raw_observation_id=obs.obs_id)
                extracted.append(ev)
                self.evidence_store.append(ev)

        if "country" in data:
            geo_str = f"{data.get('city', '')}, {data.get('country', '')}".strip(", ")
            if geo_str:
                ev = Evidence("geoip_location", geo_str, target, module_name, "B2", 0.8, raw_observation_id=obs.obs_id)
                extracted.append(ev)
                self.evidence_store.append(ev)

        return extracted
