from datetime import datetime, timezone

from core.investigation_flow import InvestigationSession
from core.analyst_runtime import AnalystRuntime


class BaseModule:
    name = "base"

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target
        self.config = config
        self.logger = logger
        self.context = context
        self.notes = []
        self.relationships = []
        self._investigation = None

    def execute(self):
        raise NotImplementedError("Module must implement execute()")

    def begin_investigation(self, goal, phases):
        """Start a live investigation session with goal header and phased UI."""
        runtime = AnalystRuntime(self.context, self.name, self.target)
        self._investigation = InvestigationSession(self.name, goal, phases, runtime)
        self._investigation.begin()
        return self._investigation

    def status_step(self, message, work=None, analyst=None):
        """
        Dynamic analysis step — runs work live between RUNNING and OK states.
        Falls back to legacy instant-OK if no investigation session is active.
        """
        if self._investigation:
            return self._investigation.run_step(message, work=work, analyst=analyst)

        import time
        from colorama import Fore, Style

        if work is not None:
            dots = "." * max(1, 32 - len(message[:52]))
            print(
                f"  {Fore.BLUE}[~]{Style.RESET_ALL} {message} {Fore.BLACK}{Style.DIM}{dots}{Style.RESET_ALL}",
                end="",
                flush=True,
            )
            time.sleep(0.04)
            result = work()
            print(f" [{Fore.GREEN}{Style.BRIGHT}OK{Style.RESET_ALL}]")
            if analyst:
                self.analyst_log(analyst)
            return result

        dots = "." * (35 - len(message[:35]))
        print(
            f"  {Fore.BLUE}[+]{Style.RESET_ALL} {message} {Fore.BLACK}{Style.BRIGHT}{dots}{Style.RESET_ALL} "
            f"[{Fore.GREEN}{Style.BRIGHT}OK{Style.RESET_ALL}]"
        )
        time.sleep(0.04)

    def analyst_log(self, action_text):
        """Context-aware analyst commentary during module execution."""
        from colorama import Fore, Style

        if self._investigation:
            self._investigation.analyst(action_text)
            return
        print(f"  {Fore.YELLOW}[Analyst Log]{Style.RESET_ALL} {action_text}")

    def add_note(self, text, severity="info", confidence=1.0):
        """Add a note locally to the module output and sync to central context."""
        note = {
            "text": str(text),
            "source": self.name,
            "severity": severity,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.notes.append(note)
        if self.context:
            self.context.add_note(text, source=self.name, severity=severity, confidence=confidence)

    def add_relation(self, src_type, src_value, relation, dst_type, dst_value, evidence=None, confidence=1.0):
        """Add a relation locally to the module output and sync to central context."""
        rel = {
            "src": {"type": src_type, "value": src_value},
            "relation": relation,
            "dst": {"type": dst_type, "value": dst_value},
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.relationships.append(rel)
        if self.context:
            self.context.add_relation(
                src_type, src_value, relation, dst_type, dst_value,
                evidence=evidence, confidence=confidence,
            )

    def log_event(self, action, entity=None, source=None, location=None, metadata=None):
        """
        v0.9 — Temporal olay kaydı (Pattern of Life altyapısı).
        Modül sırasında gerçekleşen bir olayı merkezi context'in event store'una ekler.
        entity: "{type}:{value}" formatinda varlik referansi.
                Belirtilmezse module target'ından entity otomatik türetilir.
        """
        if not self.context:
            return None
        if entity is None and self.target:
            target = self.target if isinstance(self.target, str) else " ".join(self.target)
            entity = f"module:{target}"
        return self.context.add_event(
            entity=entity,
            action=action,
            source=source or self.name,
            location=location,
            metadata=metadata,
        )

    def add_entity(self, entity_type, value, properties=None, provenance=None):
        """
        v0.9/Faz 6 — Merkezi context'e entity-agnostic varlık ekler.
        person, organization, phone, email, social_profile, wallet, location vb.
        tüm varlık tipleri bu metodla eklenebilir.

        Faz 6 — Seed ≠ Evidence:
        - Modüller tarafından eklenen varlıklar otomatik 'discovered' statüsü alır.
        - 'discovered_by' alanı modülün kendi adıyla (self.name) set edilir.
        - Kullanıcı tarafından explicit seed verilmediği sürece bu geçerlidir.
        """
        if self.context:
            if provenance is None:
                provenance = {
                    "source": "corvus",
                    "status": "discovered",
                    "discovered_by": self.name,
                }
            return self.context.add_entity(entity_type, value, properties, provenance=provenance)
        return None

    def add_person(self, name, properties=None):
        """v0.9 — Kişi varlığı ekler (merkezi intelligence graph'a)."""
        return self.add_entity("person", name, properties)

    def add_phone(self, number, properties=None):
        """v0.9 — Telefon varlığı ekler."""
        return self.add_entity("phone", number, properties)

    def add_email(self, email, properties=None):
        """v0.9 — Email varlığı ekler."""
        return self.add_entity("email", email, properties)

    def add_social_profile(self, platform, handle, properties=None):
        """v0.9 — Sosyal medya profili varlığı ekler."""
        if self.context:
            return self.context.add_social_profile(platform, handle, properties)
        return None

    def add_wallet(self, address, chain="btc", properties=None):
        """v0.9 — Kripto cüzdan varlığı ekler."""
        if self.context:
            return self.context.add_wallet(address, chain, properties)
        return None

    def add_organization(self, name, properties=None):
        """v0.9 — Organizasyon/şirket varlığı ekler."""
        return self.add_entity("organization", name, properties)

    def add_location(self, lat, lon, label=None, properties=None):
        """v0.9 — Coğrafi konum varlığı ekler."""
        if self.context:
            return self.context.add_location(lat, lon, label, properties)
        return None

    def success(self, target="local", data=None):
        """Return a normalized success payload for all modules."""
        if self._investigation:
            self._investigation.finish()
            self._investigation = None
        return {
            "module": self.name,
            "target": target,
            "status": "success",
            "data": data or {},
            "notes": self.notes,
            "relationships": self.relationships,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def error(self, message, target="local"):
        """Return a normalized error payload for all modules."""
        if self._investigation:
            self._investigation.finish(summary="Investigation halted — error encountered")
            self._investigation = None
        return {
            "module": self.name,
            "target": target,
            "status": "error",
            "error": str(message),
            "notes": self.notes,
            "relationships": self.relationships,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Geriye uyumluluk
Module = BaseModule
