"""Application configuration.

Settings are read (in order of precedence) from:

1. Constructor keyword arguments (programmatic use).
2. Environment variables prefixed with ``KGCONVAI_``.
3. A ``.env`` file in the working directory.
4. Defaults defined below.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMMode = Literal["local", "api", "template"]


class Settings(BaseSettings):
    """Runtime configuration for the agent."""

    model_config = SettingsConfigDict(
        env_prefix="KGCONVAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Mode selection -----------------------------------------------------
    llm_mode: LLMMode = Field(
        default="template",
        description=(
            "Which LLM backend to use. 'local' uses Ollama, 'api' uses "
            "OpenRouter, 'template' falls back to canned templates (no LLM)."
        ),
    )

    # --- Ollama -------------------------------------------------------------
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "llama3"

    # --- OpenRouter ---------------------------------------------------------
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_model: str = "deepseek/deepseek-v3-base:free"
    openrouter_api_key: str | None = None

    # --- ASR / TTS ----------------------------------------------------------
    whisper_model: str = "base"
    vad_aggressiveness: int = 2
    speech_max_record_seconds: float = 10.0
    speech_silence_padding_seconds: float = 0.5
    tts_rate: int = 175
    tts_volume: float = 1.0

    # --- NLU ----------------------------------------------------------------
    classifier_model: str = "facebook/bart-large-mnli"
    faq_confidence_threshold: float = 0.4

    # --- Data files ---------------------------------------------------------
    data_dir: Path = Path("dialogue_graph")

    @property
    def conversation_graph_path(self) -> Path:
        return self.data_dir / "conversation_graph.json"

    @property
    def faq_path(self) -> Path:
        return self.data_dir / "faq.json"

    @property
    def templates_path(self) -> Path:
        return self.data_dir / "templates.json"
