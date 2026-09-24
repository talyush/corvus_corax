"""Corvus Corax — Core Package.

Proje kökü ve ortak kalıcı depo yolları için tek doğru tanım.
__file__ = <root>/core/__init__.py -> root = dirname(dirname(__file__))
"""

import os

# Proje kökü (repo ana dizini) — tek kaynak
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Kalıcı depo dizini (zihin, bilgi, deneyim, audit, guard logları)
VAULT_DIR = os.path.join(PROJECT_ROOT, "vault")


def _load_env_file(path: str = "") -> None:
    """v1.3.2: Basit, bağımlılıksız .env yükleyici (python-dotenv gerektirmez).

    Proje kökündeki `.env` dosyasını okur ve ortam değişkenlerine işler.
    Kurallar:
      - `KEY=VALUE` satırları işlenir (baştaki/arkadaki boşluklar atılır).
      - `#` / `;` ile başlayan satırlar yorumdur, atlanır.
      - Değerlerdeki çift/tek tırnak temizlenir.
      - MECVUT ortam değişkenleri ASLA ezilmez (OS env > .env önceliği).
    """
    env_path = path or os.path.join(PROJECT_ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8-sig") as _f:
            for line in _f:
                line = line.strip()
                if not line or line.startswith(("#", ";")):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # .env okunamazsa sessizce geç — LLM provider'ları zaten opsiyonel
        pass


_load_env_file()


def project_path(*parts: str) -> str:
    """Proje köküne göre mutlak yol üretir."""
    return os.path.join(PROJECT_ROOT, *parts)


def vault_path(*parts: str) -> str:
    """Vault dizinine göre mutlak yol üretir."""
    return os.path.join(VAULT_DIR, *parts)