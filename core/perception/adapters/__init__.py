"""Corvus Perception — Builtin adaptörler.

Mevcut modülleri (modules/*.py) Perception pipeline'a bağlayan wrapper'lar.
Her adaptör, kaynak kodunu değiştirmeden modülü sarar.
"""

from core.perception.adapters.whois import WhoisAdapter
from core.perception.adapters.social import SocialAdapter

__all__ = ["WhoisAdapter", "SocialAdapter"]