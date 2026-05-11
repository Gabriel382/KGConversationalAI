"""Abstract TTS interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TTS(ABC):
    """Speak text aloud."""

    @abstractmethod
    def say(self, text: str) -> None:
        """Synthesize speech and block until playback finishes."""
