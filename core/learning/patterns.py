"""Corvus Self-Learning — Pattern Learning.

Tekrar eden başarı/başarısızlık desenlerini çıkarır ve kalıcı saklar.

Örnek: "social aracı person hedeflerinde 3 kez privacy_wall hatası aldı"
        -> LearnedPattern: trigger=(tool=social, error=privacy_wall, target_type=person)
           alternatifler: github, academic, social_alt

Bu kalıplar FailureLearner'a (pivot önerisi) ve selection'a beslenir.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .experience import ExperienceStore


@dataclass
class LearnedPattern:
    """Öğrenilen bir desen."""

    tool: str
    error_type: str
    target_type: str
    count: int = 1
    alternatives: List[str] = field(default_factory=list)
    last_seen: str = ""

    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "error_type": self.error_type,
            "target_type": self.target_type,
            "count": self.count,
            "alternatives": list(self.alternatives),
            "last_seen": self.last_seen,
        }


class PatternLearning:
    """Deneyimlerden desen çıkarır."""

    MIN_PATTERN_COUNT = 2   # bu kadar tekrar olunca "öğrenildi" sayılır

    def __init__(self, store: ExperienceStore):
        self.store = store
        self.patterns: Dict[str, LearnedPattern] = {}
        self._load()

    def _load(self) -> None:
        try:
            import json
            import os
            path = getattr(self.store, "path", "")
            data_path = path.replace("experience.json", "patterns.json")
            if os.path.exists(data_path):
                with open(data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, p in data.items():
                    self.patterns[key] = LearnedPattern(**p)
        except Exception:
            self.patterns = {}

    def _save(self) -> None:
        try:
            import json
            import os
            data_path = getattr(self.store, "path", "").replace("experience.json", "patterns.json")
            os.makedirs(os.path.dirname(data_path), exist_ok=True)
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({k: v.to_dict() for k, v in self.patterns.items()},
                          f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def learn_from_recent(self) -> List[LearnedPattern]:
        """Son deneyimlerden desen çıkar (her çağrıda çalışır)."""
        changed = []
        errors = [e for e in self.store.experiences if e.status == "error"]
        for e in errors:
            # privacy_wall, timeout, no_data gibi error_type'ı çıkar
            err_type = e.error_type or self._infer_error_type(e)
            key = f"{e.tool}|{err_type}|{e.target_type}"

            pat = self.patterns.get(key)
            if pat is None:
                pat = LearnedPattern(
                    tool=e.tool, error_type=err_type, target_type=e.target_type,
                    alternatives=list(e.alternatives),
                )
                self.patterns[key] = pat
            else:
                pat.count += 1
                for alt in e.alternatives:
                    if alt and alt not in pat.alternatives:
                        pat.alternatives.append(alt)
            pat.last_seen = e.timestamp
            changed.append(pat)

        self._save()
        return changed

    @staticmethod
    def _infer_error_type(e) -> str:
        """Hata notundan başarısızlık tipi çıkar (kaba + niyet)."""
        text = (e.summary or "") + " " + " ".join(getattr(e, "user_note", "") or [])
        low = text.lower()
        if any(k in low for k in ("privacy", "gizli", "private", "locked", "permission")):
            return "privacy_wall"
        if any(k in low for k in ("timeout", "zaman aşımı", "timed out")):
            return "timeout"
        if any(k in low for k in ("no data", "veri yok", "bulunamadı", "not found", "empty", "0 new")):
            return "no_data"
        if e.status != "success":
            return "generic_failure"
        return "unknown"

    # ------------------------------------------------------------------
    def mature_patterns(self) -> List[LearnedPattern]:
        """Yeterince tekrar eden (öğrenilmiş) desenler."""
        return [p for p in self.patterns.values() if p.count >= self.MIN_PATTERN_COUNT]

    def alternatives_for(self, tool: str, target_type: str = "") -> List[str]:
        """Bir aracın bilinen alternatif pivot araçları."""
        alts = []
        for p in self.patterns.values():
            if p.tool == tool and (not target_type or p.target_type == target_type):
                for a in p.alternatives:
                    if a not in alts:
                        alts.append(a)
        return alts

    def summary(self) -> Dict:
        return {
            "pattern_count": len(self.patterns),
            "mature": len(self.mature_patterns()),
            "patterns": [p.to_dict() for p in self.mature_patterns()],
        }