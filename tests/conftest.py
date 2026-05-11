"""Shared pytest fixtures."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from kgconvai.asr.base import ASR, SpeechResult
from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.llm.base import LLMGenerator
from kgconvai.nlu.classifier import Classification, Classifier
from kgconvai.nlu.faq import FAQStore
from kgconvai.tts.base import TTS

# ---------- Test doubles ------------------------------------------------------


class FakeClassifier(Classifier):
    """Returns canned scores for given (text, candidates) pairs.

    If no rule matches, returns the candidates ranked alphabetically with
    decreasing scores so tests are deterministic.
    """

    def __init__(self, rules: dict[str, str] | None = None) -> None:
        self.rules = rules or {}

    def classify(self, text: str, candidates: list[str]) -> list[Classification]:
        if not text.strip() or not candidates:
            return []
        forced = self.rules.get(text.strip().lower())
        if forced and forced in candidates:
            head = Classification(forced, 0.99)
            tail = [Classification(c, 0.01) for c in candidates if c != forced]
            return [head, *tail]
        # No rule matched — return low, decaying scores so hedge-path tests
        # can verify behaviour below the default confidence threshold.
        ordered = sorted(candidates)
        len(ordered)
        return [
            Classification(label, max(0.01, 0.30 - i * 0.05)) for i, label in enumerate(ordered)
        ]


class FakeASR(ASR):
    """Yields a scripted sequence of SpeechResults."""

    def __init__(self, scripted: list[SpeechResult]) -> None:
        self._queue = list(scripted)

    def listen(self) -> SpeechResult:
        if not self._queue:
            return SpeechResult("", "unknown")
        return self._queue.pop(0)


@dataclass(slots=True)
class RecordingTTS(TTS):
    """Records every spoken phrase instead of producing audio."""

    spoken: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.spoken is None:
            self.spoken = []

    def say(self, text: str) -> None:
        self.spoken.append(text)


class FakeLLM(LLMGenerator):
    """Returns a configurable canned reply; works for chat or prompt format."""

    def __init__(self, reply: str = "ok", chat_format: bool = False) -> None:
        super().__init__(chat_format=chat_format, default_model="fake")
        self.reply = reply
        self.calls: list = []

    def generate(self, prompt_or_messages, *, model=None, max_tokens=200, temperature=0.3):
        self.calls.append(prompt_or_messages)
        return self.reply


# ---------- Sample data fixtures ---------------------------------------------


@pytest.fixture()
def sample_graph() -> DialogueGraph:
    return DialogueGraph(
        {
            "start": {"greet": "ask_information", "book_meeting": "book_meeting", "goodbye": "end"},
            "ask_information": {"ask_information": "provide_information", "goodbye": "end"},
            "book_meeting": {"confirm_booking": "end", "goodbye": "end"},
            "provide_information": {"goodbye": "end"},
            "end": {},
        }
    )


@pytest.fixture()
def sample_faq() -> FAQStore:
    return FAQStore(
        {
            "ask_information": {
                "what_are_your_opening_hours": "We are open 9 to 6, Mon-Fri.",
                "where_are_you_located": "Downtown Paris.",
            },
            "book_meeting": {
                "how_to_book_an_appointment": "Provide date and time.",
            },
        }
    )


@pytest.fixture()
def sample_templates() -> TemplateStore:
    return TemplateStore(
        {
            "greet": "Say hello.",
            "ask_information": "Ask what they need.",
            "book_meeting": "Ask for date and time.",
            "goodbye": "Say goodbye.",
            "unknown": "Politely ask for clarification.",
        }
    )


@pytest.fixture()
def settings() -> Settings:
    return Settings(llm_mode="template")


# ---------- Re-export test doubles for convenient import in tests -----------


@pytest.fixture()
def fake_classifier_cls():
    return FakeClassifier


@pytest.fixture()
def fake_asr_cls():
    return FakeASR


@pytest.fixture()
def recording_tts_cls():
    return RecordingTTS


@pytest.fixture()
def fake_llm_cls():
    return FakeLLM
