"""Corvus Corax v1.1.2 — Self-Learning Layer ("The Machine learns").

Kullanıcıdan ve kendisinden öğrenir; öğrendiklerini TAM OTONOM uygular;
yaptığı her değişikliği audit (denetim) raporuna yazar.

Akış:
  Observation / UserFeedback / SelfReflection
    -> ExperienceStore (kalıcı deneyim)
    -> PatternLearning (tekrar eden başarı/başarısızlık kalıpları)
    -> Calibration (araç güven/öncelik ayarları)
    -> Selection (deneyim tabanlı araç seçimi -> Planner'a entegre)
    -> SelfLearn (failure -> alternatif öneriler -> pivot)
    -> Audit (mimar raporu: ne öğrendi, neyi değiştirdi)

GÜVENLİK DUVARI (asla değiştirilemez):
  - SafetyPolicy, onay mekanizması, DENIED araçlar mimarın alanıdır.
  - Öğrenme yalnızca taktik katmana dokunur: araç öncelikleri, puanlar,
    alternatif öneriler, kalibrasyon parametreleri.
"""

from .experience import ExperienceStore, Experience, ToolStats
from .feedback import FeedbackLoop
from .patterns import PatternLearning, LearnedPattern
from .calibration import CalibrationEngine
from .selection import ExperienceBasedSelection
from .self_learn import FailureLearner
from .audit import AuditLog

__all__ = [
    "ExperienceStore",
    "Experience",
    "ToolStats",
    "FeedbackLoop",
    "PatternLearning",
    "LearnedPattern",
    "CalibrationEngine",
    "ExperienceBasedSelection",
    "FailureLearner",
    "AuditLog",
]