"""Abstract ASR interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SpeechResult:
    """Output of an ASR transcription."""

    text: str
    language: str = "unknown"


class ASR(ABC):
    """Capture and transcribe spoken input."""

    @abstractmethod
    def listen(self) -> SpeechResult:
        """Block until a complete utterance is captured, then return it.

        Implementations should return ``SpeechResult("", "unknown")`` on
        failure or empty input rather than raising.
        """
