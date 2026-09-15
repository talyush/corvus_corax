"""Corvus Corax v1.1.1 - API-based Cognitive Providers (Ollama, OpenAI, Gemini, Anthropic).

Plug-and-play integrations for live local LLMs (via Ollama REST API)
and cloud LLMs when configured in config.json or environment variables.
"""
import os
import json
import urllib.request
from typing import List, Dict, Any, Optional
from .interface import AbstractCognitiveProvider
from ..persona import MachinePersona


class OllamaProvider(AbstractCognitiveProvider):
    """Yerel Ollama Model Sağlayıcısı (qwen, llama, deepseek, mistral vb.).

    v1.1.2+ Akıllı model seçimi:
      - CORVUS_OLLAMA_MODEL env varsa onu kullan.
      - Yoksa ollama list'e bak: tercih sırasına göre ilk yüklü modeli seç.
      - CORVUS_USE_OLLAMA gerekmez — Ollama çalışıyorsa Otomatik aktifleşir.
    """

    # Tercih sırası — makinede hangi model varsa kullan
    PREFERRED_MODELS = [
        "qwen2.5-coder", "qwen2.5", "qwen2", "deepseek-r1", "llama3",
        "llama3.1", "llama3.2", "mistral", "gemma2", "phi3", "llama2",
    ]

    def __init__(self, host: str = "http://localhost:11434", model: str = ""):
        self.host = os.getenv("CORVUS_OLLAMA_HOST", host).rstrip("/")
        self.model = os.getenv("CORVUS_OLLAMA_MODEL", model) or self._detect_model()

    def _detect_model(self) -> str:
        """Makinede kurulu uygun modeli bulur (tercih sırasına göre, TAM ADIYLA)."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
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
        # Ollama çalışıyorsa ve model kuruluysa otomatik kullanılır
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
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
            "temperature": 0.7,
            "options": {"num_ctx": 4096},
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                out = result.get("message", {}).get("content", "").strip()
                if out:
                    return out
                # chat formatı boşsa completion'a düş
                return self._complete(user_prompt, system_prompt)
        except Exception as e:
            # chat formatı desteklenmiyor (codar/non-chat modeller) -> completion
            try:
                return self._complete(user_prompt, system_prompt)
            except Exception as e2:
                return f"[Ollama Error: chat={e} | completion={e2}]"

    def _complete(self, user_prompt: str, system_prompt: Optional[str]) -> str:
        """Completion tabanlı fallback (/api/generate) — tüm modeller destekler."""
        sys_text = system_prompt or MachinePersona.SYSTEM_PROMPT
        full_prompt = f"{sys_text}\n\nUser: {user_prompt}\n\nCorvus:"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "temperature": 0.7,
            "options": {"num_ctx": 4096},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()


class OpenAIProvider(AbstractCognitiveProvider):
    """OpenAI GPT API Sağlayıcısı."""

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
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[OpenAI Error: {e}]"
