"""Corvus Corax v1.1.1 - API-based Cognitive Providers (Ollama, OpenAI, Gemini, Anthropic).

Plug-and-play integrations for live local LLMs (via Ollama REST API)
and cloud LLMs when configured in config.json or environment variables.
"""
import os
import json
import urllib.request
from typing import List, Dict, Any, Optional
from .interface import AbstractCognitiveProvider, Capability
from ..persona import MachinePersona


class OllamaProvider(AbstractCognitiveProvider):
    """Yerel Ollama Model Sağlayıcısı (qwen, llama, deepseek, mistral vb.).

    v1.1.2+ Akıllı model seçimi:
      - CORVUS_OLLAMA_MODEL env varsa onu kullan.
      - Yoksa ollama list'e bak: tercih sırasına göre ilk yüklü modeli seç.
      - CORVUS_USE_OLLAMA gerekmez — Ollama çalışıyorsa Otomatik aktifleşir.
    """

    provider_id = "ollama"
    capabilities = [Capability.GENERAL, Capability.CODE, Capability.DEEP, Capability.LOCAL]
    priority = 20   # yerel olmasiyla hizli/onceli — ama Cloud daha guclu ise arkaya duser (router karari)

    # Tercih sırası — makinede hangi model varsa kullan
    PREFERRED_MODELS = [
        "qwen2.5-coder", "qwen2.5", "qwen2", "deepseek-r1", "llama3",
        "llama3.1", "llama3.2", "mistral", "gemma2", "phi3", "llama2",
    ]

    def __init__(self, host: str = "http://localhost:11434", model: str = ""):
        self.host = os.getenv("CORVUS_OLLAMA_HOST", host).rstrip("/")
        self.model = os.getenv("CORVUS_OLLAMA_MODEL", model) or self._detect_model()
        self._avail_cache = None      # (timestamp, bool)
        self._avail_ttl = 10.0        # saniye — her turda HTTP yapma

    def _detect_model(self) -> str:
        """Makinede kurulu uygun modeli bulur (tercih sırasına göre, TAM ADIYLA)."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    installed = [m.get("name", "") for m in data.get("models", [])]  # tam ad (qwen2.5-coder:7b)
                    for pref in self.PREFERRED_MODELS:
                        for m in installed:
                            if m.split(":")[0] == pref:
                                return m
                    if installed:
                        return installed[0]
        except Exception:
            pass
        return "llama3"

    @property
    def provider_name(self) -> str:
        return f"Ollama Local LLM ({self.model})"

    def is_available(self) -> bool:
        # TTL cache: her chat turunda HTTP isteği atmadan hızlı karar
        import time
        now = time.time()
        if self._avail_cache is not None and now - self._avail_cache[0] < self._avail_ttl:
            return self._avail_cache[1]
        ok = self._check_available()
        self._avail_cache = (now, ok)
        return ok

    def _check_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                    return self.model.split(":")[0] in models
                return False
        except Exception:
            return False

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        sys_text = system_prompt or MachinePersona.SYSTEM_PROMPT

        # Context grafiğinden kısa bağlam özeti ekle (gerçek istihbarat bağlamı)
        if context_data:
            entities = context_data.get("entities", {}) or {}
            rels = context_data.get("relations", []) or []
            n_ent = len(entities)
            n_rel = len(rels)
            ctx_line = f"\n[Current intelligence context: {n_ent} entities, {n_rel} relations tracked.]"
            if isinstance(entities, dict) and entities:
                sample = list(entities.keys())[:4]
                ctx_line += f" Focus on: {', '.join(sample)}."
            sys_text = sys_text + ctx_line

        messages = [{"role": "system", "content": sys_text}]
        for turn in conversation_history[-8:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.8,
            "options": {
                "num_ctx": 4096,
                "num_predict": 300,     # derinlik öncelikli — uzun/katmanlı cevaplar
                "keep_alive": "10m",    # modeli bellekte tut (tekrar yükleme yok)
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                out = result.get("message", {}).get("content", "").strip()
                if out:
                    return out
                # chat formatı boşsa completion'a düş (history ile)
                return self._complete(user_prompt, system_prompt, conversation_history)
        except Exception:
            # chat formatı desteklenmiyor / timeout (coder/non-chat) -> completion (8s, history ile)
            try:
                return self._complete(user_prompt, system_prompt, conversation_history)
            except Exception as e2:
                return f"[Ollama Error: completion={e2}]"

    def _complete(self, user_prompt: str, system_prompt: Optional[str],
                  conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """Completion tabanlı fallback (/api/generate) — tüm modeller destekler.
        Konuşma geçmişini prompt'a gömer (çok turlu bağlam korunur)."""
        sys_text = system_prompt or MachinePersona.SYSTEM_PROMPT

        # Konuşma geçmişini metne dönüştür (son 6 tur)
        history_text = ""
        if conversation_history:
            lines = []
            for turn in conversation_history[-6:]:
                role = "Kullanıcı" if turn.get("role") == "user" else "Corvus"
                lines.append(f"{role}: {turn.get('content', '')}")
            if lines:
                history_text = "\n".join(lines) + "\n"

        full_prompt = (
            f"{sys_text}\n\n"
            f"{history_text}"
            f"Kullanıcı: {user_prompt}\n"
            f"Corvus:"
        )
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "temperature": 0.8,
            "options": {
                "num_ctx": 4096,
                "num_predict": 300,     # derinlik öncelikli
                "keep_alive": "10m",
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()


class OpenAIProvider(AbstractCognitiveProvider):
    """OpenAI GPT API Sağlayıcısı."""

    provider_id = "openai"
    capabilities = [Capability.GENERAL, Capability.CREATIVE, Capability.DEEP, Capability.CLOUD]
    priority = 10    # bulut güçlü -> önce

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    @property
    def provider_name(self) -> str:
        return f"OpenAI Cloud API ({self.model})"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        if not self.is_available():
            return "[OpenAI API key missing]"

        messages = [{"role": "system", "content": system_prompt or MachinePersona.SYSTEM_PROMPT}]
        for turn in conversation_history[-6:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[OpenAI Error: {e}]"
class AnthropicProvider(AbstractCognitiveProvider):
    """Anthropic Claude API Sağlayıcısı — bulut, güçlü, hafif."""

    provider_id = "anthropic"
    capabilities = [Capability.GENERAL, Capability.DEEP, Capability.CREATIVE, Capability.CLOUD]
    priority = 8     # Claude en güçlü genel — fallback zincirinde önce

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

    @property
    def provider_name(self) -> str:
        return f"Anthropic Cloud API ({self.model})"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_response(self, user_prompt: str, conversation_history: List[Dict[str, Any]],
                          context_data: Optional[Dict[str, Any]] = None,
                          system_prompt: Optional[str] = None) -> str:
        if not self.is_available():
            return "[Anthropic API key missing]"

        # Anthropic /v1/messages API — Claude
        turns = []
        for turn in conversation_history[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            turns.append({"role": role, "content": turn.get("content", "")})
        turns.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "max_tokens": 1500,
            "system": system_prompt or MachinePersona.SYSTEM_PROMPT,
            "messages": turns,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["content"][0]["text"].strip()
        except Exception as e:
            return f"[Anthropic Error: {e}]"
