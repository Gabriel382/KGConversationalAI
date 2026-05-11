"""Offline TTS via the cross-platform pyttsx3 library."""

from __future__ import annotations

from kgconvai.logging import get_logger
from kgconvai.tts.base import TTS

log = get_logger(__name__)


class Pyttsx3TTS(TTS):
    """Wraps pyttsx3 with one initialised engine, configurable rate/volume."""

    def __init__(self, *, rate: int = 175, volume: float = 1.0) -> None:
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)

    def say(self, text: str) -> None:
        if not text.strip():
            log.debug("tts.empty")
            return
        log.info("tts.speak", text=text)
        self._engine.say(text)
        self._engine.runAndWait()


class NullTTS(TTS):
    """No-op TTS used in CI and tests."""

    def say(self, text: str) -> None:
        log.debug("tts.null", text=text)
