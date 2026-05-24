from datetime import datetime, timezone

class BaseModule:
    name = "base"

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target
        self.config = config
        self.logger = logger
        self.context = context
        self.notes = []
        self.relationships = []

    def execute(self):
        raise NotImplementedError("Module must implement execute()")

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
            self.context.add_relation(src_type, src_value, relation, dst_type, dst_value, evidence=evidence, confidence=confidence)

    def success(self, target="local", data=None):
        """Return a normalized success payload for all modules."""
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
        return {
            "module": self.name,
            "target": target,
            "status": "error",
            "error": str(message),
            "notes": self.notes,
            "relationships": self.relationships,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

# 🔥 GERİYE UYUMLULUK (çok önemli)
Module = BaseModule