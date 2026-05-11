"""Ollama (local) LLM backend.

Talks to an Ollama HTTP server (default ``http://localhost:11434``).
"""

from __future__ import annotations

import requests

from kgconvai.llm.base import LLMGenerator
from kgconvai.logging import get_logger

log = get_logger(__name__)


class OllamaLLM(LLMGenerator):
    def __init__(
        self,
        *,
        url: str = "http://localhost:11434/api/generate",
        default_model: str = "llama3",
        timeout_s: float = 60.0,
    ) -> None:
        super().__init__(chat_format=False, default_model=default_model)
        self.url = url
        self.timeout_s = timeout_s

    def generate(
        self,
        prompt_or_messages: str,
        *,
        model: str | None = None,
        max_tokens: int = 200,
        temperature: float = 0.3,
    ) -> str:
        payload = {
            "model": model or self.default_model,
            "prompt": prompt_or_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            r = requests.post(self.url, json=payload, timeout=self.timeout_s)
            r.raise_for_status()
            return str(r.json().get("response", "")).strip()
        except requests.RequestException as exc:
            log.warning("llm.ollama.error", err=str(exc))
            return "I'm sorry, I couldn't generate a response right now."
