"""Corvus Agent Layer â€” Tool Executor.

Bir aracÄ± (modÃ¼lÃ¼) gÃ¼venli ÅŸekilde Ã§alÄ±ÅŸtÄ±rÄ±r ve sonucu canonic ToolResult
olarak iÅŸler.

v1.4 kararÄ±: Agent/Engine sÄ±nÄ±rÄ±nda TEK canonical sonuÃ§ tipi ToolResult'ur.
Observation, ToolResult'e baÄŸlÄ± iÃ§ gÃ¶zlem kaydÄ±dÄ±r (Evidence Engine iÃ§in
hazÄ±r); eski `run() -> Observation` dÄ±ÅŸ sÃ¶zleÅŸme olmaktan Ã§Ä±kar, uyumluluk
iÃ§in deprecated wrapper olarak tutulur.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from core.evidence.model import Evidence


@dataclass
class Observation:
    """Bir aracÄ±n Ã§alÄ±ÅŸtÄ±rÄ±lmasÄ±ndan doÄŸan iÃ§ gÃ¶zlem kaydÄ± (Evidence Engine hazÄ±rlÄ±ÄŸÄ±)."""

    tool: str
    target: str
    status: str = "skipped"            # success | error | skipped | denied
    summary: str = ""
    new_entities: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    obs_id: str = ""                   # Ã§alÄ±ÅŸma zamanÄ±nda atanÄ±r (obs-NNN)

    _sequence = 0  # tekil gÃ¶zlem kimliÄŸi sayaÃ§Ä±

    def __post_init__(self):
        Observation._sequence += 1
        self.obs_id = f"obs-{Observation._sequence}"

    def to_dict(self) -> Dict:
        return {
            "tool": self.tool,
            "target": self.target,
            "status": self.status,
            "summary": self.summary,
            "new_entities": self.new_entities,
            "notes": self.notes,
            "obs_id": self.obs_id,
        }


@dataclass
class ToolResult:
    """Kanonic aksiyon sonucu â€” Agent/Engine arasÄ±ndaki TEK dÄ±ÅŸ sÃ¶zleÅŸme.

    evidence: mevcut core/evidence/model.Evidence NESNELERÄ° (yeni model YOK).
    observation_ref: baÄŸlÄ± Observation kaydÄ±nÄ±n kimliÄŸi (obs_id).
    observation: bu sonuca baÄŸlanan iÃ§ gÃ¶zlem kaydÄ±.
    """

    ok: bool
    tool: str
    data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    error: Optional[str] = None
    observation_ref: str = ""

    observation: Optional[Observation] = None
class ToolExecutor:
    """ModÃ¼l Ã§alÄ±ÅŸtÄ±rma + gÃ¶zlem dilimleme."""

    def __init__(self, config=None, logger=None, context=None, dry_run: bool = False):
        self.config = config or {}
        self.logger = logger
        self.context = context
        self.dry_run = dry_run   # True: gerÃ§ek modÃ¼lÃ¼ Ã§aÄŸÄ±rmaz, sahte gÃ¶zlem Ã¼retir (test)

    # ------------------------------------------------------------------
    # CANONIC SÃ–ZLEÅME â€” v1.4
    # ------------------------------------------------------------------
    def execute(self, tool_name: str, target: str, module_registry: Dict) -> ToolResult:
        """AracÄ± modÃ¼l registry'den Ã§alÄ±ÅŸtÄ±rÄ±r ve ToolResult dÃ¶ndÃ¼rÃ¼r.

        v1.4: Agent bu metodu Ã§aÄŸÄ±rÄ±r (executor.run DEÄÄ°L). Observation,
        ToolResult.observation Ã¼zerinden eriÅŸilir; observation_ref baÄŸlantÄ±yÄ±
        saÄŸlar. evidence, mevcut Evidence modeliyle Ã¼retilir.
        """
        obs = self.run(tool_name, target, module_registry)
        return ToolResult(
            ok=obs.status == "success",
            tool=tool_name,
            data=obs.data,
            evidence=self._evidence_from_observation(obs),
            error=(obs.notes[-1] if obs.notes else None) if obs.status != "success" else None,
            observation_ref=obs.obs_id,
            observation=obs,
        )

    # ------------------------------------------------------------------
    # LEGACY â€” deprecated wrapper (uyumluluk iÃ§in tutulur, dÄ±ÅŸ sÃ¶zleÅŸme deÄŸil)
    # ------------------------------------------------------------------
    def run(self, tool_name: str, target: str, module_registry: Dict) -> Observation:
        """Eski Observation dÃ¶nÃ¼ÅŸÃ¼ â€” yalnÄ±zca geriye dÃ¶nÃ¼k uyumluluk.

        v1.4 kararÄ±: dÄ±ÅŸ sÃ¶zleÅŸme `execute() -> ToolResult`'tÃ¼r. Bu metot
        yalnÄ±zca eski Ã§aÄŸÄ±ranlarÄ± kÄ±rmamak iÃ§in korunmaktadÄ±r.
        """
        obs = Observation(tool=tool_name, target=target)

        if self.dry_run or tool_name not in module_registry:
            obs.status = "success" if self.dry_run else "skipped"
            obs.summary = f"[dry-run] {tool_name} {target} Ã§aÄŸrÄ±ldÄ± (gerÃ§ek modÃ¼l atlandÄ±)"
            obs.notes.append("dry-run modu â€” modÃ¼l sonucu iÅŸlenmedi")
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
                obs.summary = f"{tool_name} hatayla dÃ¶ndÃ¼: {result.get('error', 'bilinmiyor') if result else 'boÅŸ sonuÃ§'}"
                obs.notes.append(str(result.get("error", "")) if result else "boÅŸ")
                return obs

            obs.status = "success"
            data = result.get("data", {}) or {}
            obs.data = data
            notes = result.get("notes", []) or []
            rels = result.get("relationships", []) or []

            # Yeni varlÄ±klar (relations iÃ§inden)
            for rel in rels:
                for side in ("src", "dst"):
                    ent = rel.get(side, {}) or {}
                    if ent.get("type") and ent.get("value"):
                        key = f"{ent['type']}:{ent['value']}"
                        if key not in obs.new_entities:
                            obs.new_entities.append(key)

            # Not Ã¶zetleri
            for n in notes[:5]:
                obs.notes.append(str(n.get("text", str(n)))[:120])

            obs.summary = f"{tool_name} tamamlandÄ±: {len(obs.new_entities)} yeni varlÄ±k, {len(notes)} not"
            return obs

        except Exception as e:
            obs.status = "error"
            obs.summary = f"{tool_name} istisna: {e}"
            obs.notes.append(str(e))
            return obs

    # ------------------------------------------------------------------
    # KanÄ±t Ã¼retimi (mevcut Evidence modeli â€” YENÄ° model yok)
    # ------------------------------------------------------------------
    def _evidence_from_observation(self, obs: Observation) -> List[Evidence]:
        """GÃ¶zlemdeki yeni varlÄ±klarÄ± mevcut Evidence modeline Ã§evirir.

        v1.4 kuralÄ±: core/evidence/model.Evidence kullanÄ±lÄ±r; her yeni varlÄ±k
        (tip:deÄŸer) bir atomik kanÄ±t kaydÄ±dÄ±r.
        """
        evidence: List[Evidence] = []
        for key in obs.new_entities:
            ent_type, sep, value = key.partition(":")
            if not sep or not value:
                continue
            evidence.append(Evidence(
                evidence_type=ent_type,
                observed_value=value,
                target=obs.target,
                source_module=obs.tool,
                admiralty_code="B2",
                confidence=0.8,
                raw_observation_id=obs.obs_id,
            ))
        return evidence
    observation: Optional[Observation] = None
