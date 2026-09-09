"""Corvus Self-Learning — Experience Store.

Kalıcı deneyim veritabanı. Her araç çalıştırması (Observation), her kullanıcı
geri bildirimi ve her iç gözlem burada saklanır ve oturumlar arası yaşar.

  vault/experience.json  (CORVUS_EXPERIENCE_STATE env ile değiştirilebilir)

Aynı zamanda her aracın istatistiğini tutar (çağrı, başarı, hata, ortalama
yeni varlık) — Calibration motoru bu istatistikleri kullanır.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict


@dataclass
class Experience:
    """Tek bir deneyim kaydı."""

    tool: str
    target_type: str = "unknown"
    target: str = ""
    status: str = "success"            # success | error | denied | skipped
    error_type: str = ""               # privacy_wall, timeout, no_data, invalid_target ...
    summary: str = ""
    new_entities: int = 0
    context_keywords: List[str] = field(default_factory=list)
    user_satisfaction: Optional[int] = None   # 1..5 (kullanıcı geri bildirimi)
    user_note: str = ""                # "şunu yapsaydın" öğrenme kaynağı
    alternatives: List[str] = field(default_factory=list)  # önerilen pivot araçlar
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ToolStats:
    """Bir aracın birikmiş istatistiği (kalibrasyon girdisi)."""

    name: str
    calls: int = 0
    successes: int = 0
    failures: int = 0
    denied: int = 0
    total_new_entities: int = 0
    total_notes: int = 0
    avg_time: float = 0.0
    success_rate: float = 0.0
    weight: float = 1.0               # 0.0 .. 2.0 (CalibrationEngine günceller)
    last_used: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ExperienceStore:
    """Kalıcı deneyim deposu + araç istatistikleri."""

    def __init__(self, path: Optional[str] = None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = path or os.getenv("CORVUS_EXPERIENCE_STATE") or os.path.join(root, "vault", "experience.json")
        self.experiences: List[Experience] = []
        self.tool_stats: Dict[str, ToolStats] = defaultdict(lambda: ToolStats(name=""))
        self._load()
# ------------------------------------------------------------------
    # Kalıcılık
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for e in data.get("experiences", []):
                self.experiences.append(Experience(**e))
            for name, s in data.get("tool_stats", {}).items():
                self.tool_stats[name] = ToolStats(name=name, **s)
        except Exception:
            self.experiences = []
            self.tool_stats = defaultdict(lambda: ToolStats(name=""))

    def save(self) -> str:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiences": [e.to_dict() for e in self.experiences],
                    "tool_stats": {k: v.to_dict() for k, v in self.tool_stats.items()},
                }, f, ensure_ascii=False, indent=2)
            return self.path
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Kayıt
    # ------------------------------------------------------------------
    def record(self, tool: str, target_type: str = "unknown", target: str = "",
               status: str = "success", error_type: str = "", summary: str = "",
               new_entities: int = 0, context_keywords: Optional[List[str]] = None,
               alternatives: Optional[List[str]] = None) -> Experience:
        exp = Experience(
            tool=tool, target_type=target_type, target=target,
            status=status, error_type=error_type, summary=summary,
            new_entities=new_entities,
            context_keywords=context_keywords or [],
            alternatives=alternatives or [],
        )
        self.experiences.append(exp)
        self._update_stats(exp)
        if len(self.experiences) > 500:
            self.experiences = self.experiences[-500:]
        try:
            self.save()
        except Exception:
            pass
        return exp

    def _update_stats(self, exp: Experience) -> None:
        st = self.tool_stats[exp.tool]
        st.name = exp.tool
        st.calls += 1
        st.last_used = exp.timestamp
        if exp.status == "success":
            st.successes += 1
            st.total_new_entities += exp.new_entities
        elif exp.status == "error":
            st.failures += 1
        elif exp.status == "denied":
            st.denied += 1
        total_ok = st.successes + st.failures
        st.success_rate = (st.successes / total_ok) if total_ok else 0.0
# ------------------------------------------------------------------
    # Sorgu
    # ------------------------------------------------------------------
    def recent_failures(self, tool: str = "", limit: int = 5) -> List[Experience]:
        exps = [e for e in self.experiences if e.status == "error"]
        if tool:
            exps = [e for e in exps if e.tool == tool]
        return exps[-limit:][::-1]

    def failures_by_tool(self, tool: str = "") -> List[Experience]:
        return self.recent_failures(tool=tool, limit=20)

    def stats(self, tool: Optional[str] = None) -> Dict:
        if tool:
            st = self.tool_stats.get(tool)
            return st.to_dict() if st else {}
        return {k: v.to_dict() for k, v in sorted(self.tool_stats.items())}

    def most_recent(self, tool: str, limit: int = 3) -> List[Experience]:
        return [e for e in self.experiences if e.tool == tool][-limit:][::-1]

    def summary(self) -> Dict:
        return {
            "experience_count": len(self.experiences),
            "tools_tracked": len(self.tool_stats),
            "total_success": sum(1 for e in self.experiences if e.status == "success"),
            "total_errors": sum(1 for e in self.experiences if e.status == "error"),
            "total_denied": sum(1 for e in self.experiences if e.status == "denied"),
        }