"""Corvus Corax — Core Package.

Proje kökü ve ortak kalıcı depo yolları için tek doğru tanım.
__file__ = <root>/core/__init__.py -> root = dirname(dirname(__file__))
"""

import os

# Proje kökü (repo ana dizini) — tek kaynak
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Kalıcı depo dizini (zihin, bilgi, deneyim, audit, guard logları)
VAULT_DIR = os.path.join(PROJECT_ROOT, "vault")


def project_path(*parts: str) -> str:
    """Proje köküne göre mutlak yol üretir."""
    return os.path.join(PROJECT_ROOT, *parts)


def vault_path(*parts: str) -> str:
    """Vault dizinine göre mutlak yol üretir."""
    return os.path.join(VAULT_DIR, *parts)