"""Corvus Mind v1.2 Faz B — Kalıcılık (Persistence).

Corvus'un hafızasını (turlar, olgular, iç-gözlemler) ve kullanıcı modelini
oturumlar arası saklar — The Machine gibi, her oturum bir öncekinden devam eder.

Dosya: vault/mind.json  (CORVUS_MIND_STATE env ile değiştirilebilir)
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from collections import Counter
from typing import TYPE_CHECKING

from .memory import MemoryTurn

if TYPE_CHECKING:
    from .brain import MindBrain

BRAIN_VERSION = "1.2-phase-b"


def default_state_path() -> str:
    """Proje köküne göre vault/mind.json üretir."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # core/mind -> proje kökü
    return os.path.join(root, "vault", "mind.json")


def _restore_turn(d: dict) -> MemoryTurn:
    return MemoryTurn(
        role=d.get("role", "user"),
        content=d.get("content", ""),
        register=d.get("register", "conversational"),
        topics=d.get("topics", []),
        valence=d.get("valence", 0.0),
        salience=d.get("salience", 1.0),
        turn_no=d.get("turn_no", 0),
    )


def snapshot_brain(brain) -> dict:
    """MindBrain'in anlık görüntüsünü JSON'lanabilir dict'e çevirir."""
    m, u, s = brain.memory, brain.user, brain.state
    return {
        "brain_version": BRAIN_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "memory": {
            "turns": [t.to_dict() for t in m.turns],
            "facts": dict(m.facts),
            "observations": list(m.observation_log),
            "turn_no": m.turn_no,
        },
        "user": {
            "language": u.language,
            "name_hint": u.name_hint,
            "trust": u.trust,
            "expertise_impression": u.expertise_impression,
            "interests": dict(u.interests),
            "goal_signals": dict(u.goal_signals),
            "mood_counts": dict(u.mood_counts),
            "self_references": list(u.self_references),
        },
        "state": {
            "curiosity": s.curiosity,
            "vigilance": s.vigilance,
            "engagement": s.engagement,
            "empathy": s.empathy,
            "calmness": s.calmness,
            "drive_axis": s.drive_axis,
            "reflection": s.reflection,
            "turn_count": s.turn_count,
            "mood": s.mood,
            "observations": list(s.observations),
        },
    }


def save_brain(brain, path: str = None) -> str:
    """MindBrain durumunu diske yazar. Başarılıysa path, değilse boş string döner."""
    path = path or default_state_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot_brain(brain), f, ensure_ascii=False, indent=2)
        return path
    except Exception:
        return ""


def load_brain(brain, path: str = None) -> bool:
    """Diskten MindBrain durumunu geri yükler. Başarılıysa True döner."""
    path = path or default_state_path()
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mem = data.get("memory", {})
        turns = [_restore_turn(t) for t in mem.get("turns", [])]
        brain.memory.turns.clear()
        brain.memory.turns.extend(turns)
        brain.memory.facts = {k: list(v) for k, v in mem.get("facts", {}).items()}
        brain.memory.observation_log = list(mem.get("observations", []))
        brain.memory.turn_no = int(mem.get("turn_no", 0))

        u = data.get("user", {})
        brain.user.language = u.get("language")
        brain.user.name_hint = u.get("name_hint")
        brain.user.trust = float(u.get("trust", 0.5))
        brain.user.expertise_impression = float(u.get("expertise_impression", 0.4))
        brain.user.interests = Counter(u.get("interests", {}))
        brain.user.goal_signals = Counter(u.get("goal_signals", {}))
        brain.user.mood_counts = Counter(u.get("mood_counts", {}))
        brain.user.self_references = list(u.get("self_references", []))

        st = data.get("state", {})
        for attr in ("curiosity", "vigilance", "engagement", "empathy",
                     "calmness", "drive_axis", "reflection"):
            if attr in st:
                setattr(brain.state, attr, float(st[attr]))
        brain.state.turn_count = int(st.get("turn_count", 0))
        brain.state.mood = st.get("mood", "observant")
        brain.state.observations = list(st.get("observations", []))
        return True
    except Exception:
        return False