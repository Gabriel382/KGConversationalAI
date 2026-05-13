"""OpenRouter chat-completions backend.

Used for hosted models like DeepSeek, Mistral, etc. when running in ``api``
mode. The API key is read from configuration, never hard-coded.
"""

from __future__ import annotations

import requests

from kgconvai.llm.base import LLMGenerator
from kgconvai.logging import get_logger

log = get_logger(__name__)


class OpenRouterLLM(LLMGenerator):
    def __init__(
        self,
        *,
        api_key: str,
        url: str = "https://openrouter.ai/api/v1/chat/completions",
        default_model: str = "deepseek/deepseek-v3-base:free",
        timeout_s: float = 60.0,
    ) -> None:
        super().__init__(chat_format=True, default_model=default_model)
        if not api_key:
            raise ValueError("OpenRouterLLM requires an API key.")
        self.api_key = api_key
        self.url = url
        self.timeout_s = timeout_s

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(
        self,
        prompt_or_messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = 200,
        temperature: float = 0.7,
    ) -> str:
        payload = {
            "model": model or self.default_model,
            "messages": prompt_or_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            r = requests.post(
                self.url, headers=self._headers(), json=payload, timeout=self.timeout_s
            )
            status = r.status_code
            if status == 429:
                log.warning("llm.openrouter.rate_limited", status=status)
                return (
                    "_(OpenRouter rate-limit reached on the free tier - try "
                    "again in a minute, or pick a paid model.)_"
                )
            if status == 401:
                log.warning("llm.openrouter.unauthorized", status=status)
                return (
                    "_(OpenRouter rejected the API key. Generate a fresh one at "
                    "https://openrouter.ai/keys.)_"
                )
            if status == 404:
                # Most often: the requested model id no longer exists.
                log.warning(
                    "llm.openrouter.not_found",
                    status=status,
                    model=model or self.default_model,
                )
                return (
                    "_(OpenRouter doesn't know the model "
                    f"`{model or self.default_model}`. Try a different one "
                    "from the dropdown.)_"
                )
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if not choices:
                raise ValueError("no 'choices' in response")
            return str(choices[0]["message"]["content"]).strip()
        except (requests.RequestException, ValueError, KeyError) as exc:
            log.warning("llm.openrouter.error", err=str(exc))
            return f"_(LLM call failed: {exc!s})_"
