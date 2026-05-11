"""Abstract LLM generator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMGenerator(ABC):
    """Base class for prompt- and chat-format LLM backends.

    ``chat_format`` is True for backends that take ``messages=[{role,content}]``
    (OpenAI-compatible APIs) and False for backends that take a single ``prompt``
    string (Ollama, raw completion APIs).
    """

    chat_format: bool

    def __init__(self, *, chat_format: bool, default_model: str) -> None:
        self.chat_format = chat_format
        self.default_model = default_model

    @abstractmethod
    def generate(
        self,
        prompt_or_messages: Any,
        *,
        model: str | None = None,
        max_tokens: int = 200,
        temperature: float = 0.3,
    ) -> str:
        """Return the generated text or a safe fallback string on error."""
