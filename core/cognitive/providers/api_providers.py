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
    """Yerel Ollama Model Sağlayıcısı (DeepSeek, Llama3, Mistral vb.)."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3"):
        self.host = os.getenv("CORVUS_OLLAMA_HOST", host).rstrip("/")
        self.model = os.getenv("CORVUS_OLLAMA_MODEL", model)

    @property
    def provider_name(self) -> str:
        return f"Ollama Local LLM ({self.model})"

    def is_available(self) -> bool:
        # Only consider Ollama available if explicitly configured via env or model is pulled
        if not os.getenv("CORVUS_USE_OLLAMA") and not os.getenv("CORVUS_OLLAMA_HOST"):
            return False
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
        messages = [{"role": "system", "content": system_prompt or MachinePersona.SYSTEM_PROMPT}]
        for turn in conversation_history[-6:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"[Ollama Error: {e}]"


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
