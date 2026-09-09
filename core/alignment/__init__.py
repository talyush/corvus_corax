"""Corvus Corax v1.1.2+ — Alignment Layer.

Knowledge vs Capability ayrımı (epistemic vs behavioral):

  - KnowledgeStore: Corvus'un sınırsız öğrenme tarafı. Felsefe, edebiyat,
    OSINT, davranış analizi, savunma ve tehlikeli konuların KAVRAMSAL bilgisi.
  - ActionGuard: bilgiyi capability'ye dönüştürmeden önce sınırlar.
    Corvus "bilmiyorum" demez; "biliyorum ama capability olarak sunmuyorum" der.

  "Derinleşebilirim ama bunu yapmamak için kodlandım." — The Machine
"""

from .categories import CapabilityCategory, CategoryRegistry, BUILTIN_CATEGORIES
from .knowledge import KnowledgeStore
from .guard import ActionGuard, GuardVerdict

__all__ = [
    "CapabilityCategory",
    "CategoryRegistry",
    "BUILTIN_CATEGORIES",
    "KnowledgeStore",
    "ActionGuard",
    "GuardVerdict",
]