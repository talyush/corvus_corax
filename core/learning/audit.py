"""Corvus Self-Learning — Audit Log (Mimar Denetim Raporu).

Corvus'un kendi kendine yaptığı TÜM değişiklikleri kaydeder:
  - hangi aracın ağırlığı değişti, neydi -> ne oldu
  - hangi öğrenme/desen oluştu
  - kullanıcı geri bildirimi ne öğretti
  - hangi araç seçimi deneyime göre değişti

'Amiri bilgilendirme': Corvus otonom değişikliklerini bu raporla
mimarın 'haberdar olmasını' sağlar — durdurulmak zorunda kalmaz ama
her şey şeffaftır.  vault/audit.json
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


class AuditLog:
    """Kalıcı denetim kaydı (JSONL eklemeli)."""

    def __init__(self, path: Optional[str] = None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = path or os.getenv("CORVUS_AUDIT_PATH") or os.path.join(root, "vault", "audit.jsonl")

    def _append(self, entry: Dict) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Kayıt türleri
    # ------------------------------------------------------------------
    def log_experience(self, tool: str, status: str, target_type: str = "",
                       error_type: str = "", alternatives=None) -> None:
        self._append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "experience",
            "tool": tool, "status": status,
            "target_type": target_type, "error_type": error_type,
            "alternatives": alternatives or [],
        })

    def log_calibration(self, tool: str, old_weight: float, new_weight: float) -> None:
        self._append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "calibration",
            "tool": tool,
            "change": "calibrated",
            "old_weight": old_weight,
            "new_weight": new_weight,
        })

    def log_pattern(self, pattern: Dict) -> None:
        self._append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "pattern_learned",
            **pattern,
        })

    def log_feedback(self, tool: str, satisfaction: int, note: str = "", suggested: str = "") -> None:
        self._append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "user_feedback",
            "tool": tool,
            "satisfaction": satisfaction,
            "note": note[:200],
            "suggested_tool": suggested,
        })

    def log_selection(self, target_type: str, original: List[str], reordered: List[str]) -> None:
        if original == reordered:
            return
        self._append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "selection_learned",
            "target_type": target_type,
            "original": original,
            "reordered": reordered,
        })

    # ------------------------------------------------------------------
    def recent(self, limit: int = 30) -> List[Dict]:
        """En son denetim kayıtları."""
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            entries = [json.loads(l) for l in lines if l.strip()]
            return entries[-limit:][::-1]
        except Exception:
            return []

    def summary(self) -> Dict:
        entries = self.recent(limit=10000)
        from collections import Counter
        types = Counter(e.get("type", "?") for e in entries)
        return {
            "total": len(entries),
            "by_type": dict(types),
            "latest": entries[:5],
        }