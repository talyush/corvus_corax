"""Corvus Agent Layer — Tool Executor.

Bir aracı (modülü) güvenli şekilde çalıştırır ve sonucu GÖZLEM (Observation)
olarak işler. Gözlem; hangi bilgilerin toplandığını, yeni varlıkların
neler olduğunu ve sonraki adımlar için pivot adaylarını içerir.

Observation -> Action -> Observation döngüsünün "gözlem" yarısı burada üşer.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class Observation:
    """Bir aracın çalıştırılmasından doğan gözlem."""

    tool: str
    target: str
    status: str = "skipped"            # success | error | skipped | denied
    summary: str = ""
    new_entities: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "tool": self.tool,
            "target": self.target,
            "status": self.status,
            "summary": self.summary,
            "new_entities": self.new_entities,
            "notes": self.notes,
        }


class ToolExecutor:
    """Modül çalıştırma + gözlem dilimleme."""

    def __init__(self, config=None, logger=None, context=None, dry_run: bool = False):
        self.config = config or {}
        self.logger = logger
        self.context = context
        self.dry_run = dry_run   # True: gerçek modülü çağırmaz, sahte gözlem üretir (test)

    def run(self, tool_name: str, target: str, module_registry: Dict) -> Observation:
        """Aracı modül registry'den çalıştırır ve gözlem olarak işler."""
        obs = Observation(tool=tool_name, target=target)

        if self.dry_run or tool_name not in module_registry:
            obs.status = "success" if self.dry_run else "skipped"
            obs.summary = f"[dry-run] {tool_name} {target} çağrıldı (gerçek modül atlandı)"
            obs.notes.append("dry-run modu — modül sonucu işlenmedi")
            return obs

        try:
            module_cls = module_registry[tool_name]
            module = module_cls(
                target=[target],
                config=self.config,
                logger=self.logger,
                context=self.context,
            )
            result = module.execute()

            if not result or result.get("status") != "success":
                obs.status = "error"
                obs.summary = f"{tool_name} hatayla döndü: {result.get('error', 'bilinmiyor') if result else 'boş sonuç'}"
                obs.notes.append(str(result.get("error", "")) if result else "boş")
                return obs

            obs.status = "success"
            data = result.get("data", {}) or {}
            obs.data = data
            notes = result.get("notes", []) or []
            rels = result.get("relationships", []) or []

            # Yeni varlıklar (relations içinden)
            for rel in rels:
                for side in ("src", "dst"):
                    ent = rel.get(side, {}) or {}
                    if ent.get("type") and ent.get("value"):
                        key = f"{ent['type']}:{ent['value']}"
                        if key not in obs.new_entities:
                            obs.new_entities.append(key)

            # Not özetleri
            for n in notes[:5]:
                obs.notes.append(str(n.get("text", str(n)))[:120])

            obs.summary = f"{tool_name} tamamlandı: {len(obs.new_entities)} yeni varlık, {len(notes)} not"
            return obs

        except Exception as e:
            obs.status = "error"
            obs.summary = f"{tool_name} istisna: {e}"
            obs.notes.append(str(e))
            return obs