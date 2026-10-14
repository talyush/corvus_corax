"""Corvus Corax v1.0 — Nexus Intelligence Engine.

Graph Reasoning, Temporal Timelines, and Asset Intelligence.
"""

# v1.4 notu: core/nexus.py (legacy NexusEngine) ile core/nexus/ paketi
# aynı adı paylaşıyor; paket, modülü gölgeliyor. Bu lazy re-export,
# `from core.nexus import NexusEngine` çağrılarını (örn. core/exporter.py)
# dosya taşıma/rename yapmadan çalışır tutar.
__all__ = ["NexusEngine"]


def __getattr__(name):
    if name == "NexusEngine":
        import importlib.util
        import os
        _legacy = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nexus.py")
        _spec = importlib.util.spec_from_file_location("core._nexus_legacy", _legacy)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        return _mod.NexusEngine
    raise AttributeError(f"module 'core.nexus' has no attribute {name!r}")

