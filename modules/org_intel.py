import re
from core.module_base import BaseModule
from core.config import load_rules


class OrgIntelModule(BaseModule):
    """
    v0.9 — Organization Intelligence Module.

    Organizasyon/şirket varlıklarını analiz eder:
    - Domain bağlama (org owns domain — candidate)
    - ASN/WHOIS altyapı örtüşmesi korelasyonu
    - Personel bağlama (org employs person — candidate)
    - Bağlı şirket/ana şirket ilişkisi
    """
    name = "org"

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: org <company_name> [domain] [person] [parent:ParentCo]")

        org_name = args[0]
        domain = None
        person = None
        parent = None

        for arg in args[1:]:
            if arg.startswith("parent:"):
                parent = arg.split(":", 1)[1]
            elif "." in arg and " " not in arg:
                domain = arg
            else:
                person = arg

        self.begin_investigation(
            goal=f"Organization Intelligence — {org_name}",
            phases=[
                (1, "ORGANIZATION IDENTIFICATION"),
                (2, "INFRASTRUCTURE CORRELATION"),
                (3, "RELATIONSHIP MAPPING"),
            ],
        )

        # 1. Organizasyon varlığı
        self.status_step(f"Registering organization '{org_name}'")
        org_props = {"name": org_name}
        self.add_entity("organization", org_name, org_props)

        self.log_event("org_identified", entity=f"organization:{org_name}",
                       metadata={"name": org_name})

        # 2. Domain bağlama (candidate)
        if domain:
            self.status_step(f"Linking domain {domain} as candidate owner")
            self.add_entity("domain", domain)
            self.add_relation(
                "organization", org_name, "org_owns_domain", "domain", domain,
                evidence=f"User-provided association: {org_name} linked to domain {domain} as candidate owner",
                confidence=0.6,
            )
            self.log_event("org_domain_mapped", entity=f"organization:{org_name}",
                           metadata={"domain": domain, "confidence": 0.6})

        # 3. Mevcut contexteki altyapı korelasyonu
        self.status_step("Correlating existing infrastructure in context")
        infra_matches = []
        if self.context:
            # ASN intelligence'dan aynı org adını bul
            asn_intel = self.context.data.get("asn_intel", {})
            org_keywords = org_name.lower().split()
            for ip, asn_data in asn_intel.items():
                org_in_data = asn_data.get("organization", "").lower()
                if any(kw in org_in_data for kw in org_keywords):
                    infra_matches.append(f"ip:{ip} (AS{asn_data.get('as_number', '?')})")

            # Domain ASN data
            tech_intel = self.context.data.get("tech_intel", {})
            for dom, t_data in tech_intel.items():
                server = str(t_data.get("server", "")).lower()
                if any(kw in server for kw in org_keywords):
                    infra_matches.append(f"domain:{dom} (server: {t_data.get('server')})")

            # Meta data from metadata_intel (org hints)
            metadata_intel = self.context.data.get("metadata_intel", {})
            for dom, m_data in metadata_intel.items():
                humans = m_data.get("humans_txt", {})
                tech_hints = humans.get("tech_hints", [])
                for hint in tech_hints:
                    if any(kw in hint.lower() for kw in org_keywords):
                        infra_matches.append(f"domain:{dom} (meta: {hint})")

        if infra_matches:
            self.status_step(f"Found {len(infra_matches)} infrastructure matches")
            for match in infra_matches[:10]:
                self.add_note(f"Infrastructure correlation: {match}", severity="info")
                self.log_event("org_infra_correlated", entity=f"organization:{org_name}",
                               metadata={"match": match})
        else:
            self.status_step("No existing infrastructure matches found in context")

        # 4. Personel bağlama (candidate)
        if person:
            self.status_step(f"Linking {person} as candidate employee")
            self.add_person(person)
            self.add_relation(
                "organization", org_name, "employs_candidate", "person", person,
                evidence=f"User-provided association: {org_name} linked to {person} as candidate employee",
                confidence=0.4,
            )
            self.log_event("org_personnel_mapped", entity=f"person:{person}",
                           metadata={"org": org_name, "confidence": 0.4})

        # 5. Parent/child ilişkisi
        if parent:
            self.status_step(f"Linking parent company {parent}")
            self.add_entity("organization", parent)
            self.add_relation(
                "organization", parent, "owns_subsidiary", "organization", org_name,
                evidence=f"User-provided association: {parent} owns subsidiary {org_name}",
                confidence=0.5,
            )
            self.log_event("org_subsidiary_mapped", entity=f"organization:{parent}",
                           metadata={"subsidiary": org_name})

        self.add_note(
            f"Organization {org_name} registered with {len(infra_matches)} infra correlations",
            severity="info", confidence=0.6,
        )

        data = {
            "organization": org_name,
            "domain": domain,
            "person": person,
            "parent": parent,
            "infra_correlations": infra_matches,
        }
        return self.success(target=org_name, data=data)