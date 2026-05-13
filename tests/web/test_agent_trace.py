"""Agent.respond_with_trace tests."""

from __future__ import annotations

import pytest

from kgconvai.agent import Agent, CycleResult
from kgconvai.asr.base import ASR, SpeechResult
from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.nlu.classifier import Classification, Classifier
from kgconvai.nlu.faq import FAQStore
from kgconvai.state import DialogueSession
from kgconvai.tts.base import TTS


class _FakeASR(ASR):
    def listen(self) -> SpeechResult:
        return SpeechResult("", "en")


class _FakeTTS(TTS):
    def say(self, text: str) -> None:
        return None


class _RuleClassifier(Classifier):
    def __init__(self, mapping: dict[str, str]):
        self.mapping = mapping

    def classify(self, text: str, candidates: list[str]) -> list[Classification]:
        target = self.mapping.get(text.lower())
        if target in candidates:
            ordered = [target] + [c for c in candidates if c != target]
        else:
            ordered = list(candidates)
        return [Classification(label=c, score=1.0 - (i * 0.1)) for i, c in enumerate(ordered)]


class _RecordingLLM:
    def __init__(self, name: str = "recorder") -> None:
        self.name = name
        self.calls: list = []
        self.chat_format = False
        self.default_model = "test"

    def generate(self, prompt, *, model=None, max_tokens=200, temperature=0.3):
        self.calls.append((self.name, prompt))
        return f"<{self.name}> reply"


@pytest.fixture()
def agent(tmp_path) -> Agent:
    import json

    kg = {
        "version": "1.0",
        "states": [
            {"id": "start"},
            {"id": "ask_information"},
            {"id": "end", "is_terminal": True},
        ],
        "intents": [{"id": "greet"}, {"id": "goodbye"}],
        "transitions": [
            {"from": "start", "intent": "greet", "to": "ask_information"},
            {"from": "ask_information", "intent": "goodbye", "to": "end"},
        ],
        "faqs": [],
        "templates": [
            {"intent": "greet", "text": "Say hello."},
            {"intent": "goodbye", "text": "Say bye."},
        ],
    }
    p = tmp_path / "kg.json"
    p.write_text(json.dumps(kg), encoding="utf-8")

    return Agent(
        asr=_FakeASR(),
        tts=_FakeTTS(),
        classifier=_RuleClassifier({"hello": "greet", "bye": "goodbye"}),
        graph=DialogueGraph.from_path(p),
        faq=FAQStore.from_path(p),
        templates=TemplateStore.from_path(p),
        llm=None,
        settings=Settings(llm_mode="template"),
    )


def test_respond_with_trace_returns_full_cycle_result(agent):
    session = DialogueSession()
    session, trace = agent.respond_with_trace("hello", session)
    assert isinstance(trace, CycleResult)
    assert trace.user_text == "hello"
    assert trace.intent == "greet"
    assert trace.next_state == "ask_information"
    assert trace.response  # non-empty string
    # Session has been mutated
    assert session.current_state == "ask_information"
    assert len(session.history) == 2


def test_respond_back_compat_returns_just_string(agent):
    """The old respond() API still works."""
    reply = agent.respond("hello")
    assert isinstance(reply, str)
    assert reply  # non-empty


def test_respond_with_trace_llm_override_used_for_one_call(agent):
    """An llm_override is used for that call but doesn't replace agent.llm."""
    default_llm = agent.llm  # None for this agent
    override = _RecordingLLM("override")

    session = DialogueSession()
    _, trace = agent.respond_with_trace("hello", session, llm_override=override)
    # The override was called
    assert len(override.calls) == 1
    # The reply came from the override
    assert trace.response.startswith("<override>")
    # agent.llm itself was not mutated
    assert agent.llm is default_llm


def test_respond_with_trace_no_override_falls_back_to_template(agent):
    """Without an override and without agent.llm, the template path runs."""
    session = DialogueSession()
    _, trace = agent.respond_with_trace("hello", session)
    # Template for greet
    assert trace.response == "Say hello."


def test_traces_accumulate_correctly_across_turns(agent):
    """Walking the graph step by step produces consistent CycleResults."""
    session = DialogueSession()
    _, t1 = agent.respond_with_trace("hello", session)
    _, t2 = agent.respond_with_trace("bye", session)
    assert t1.next_state == "ask_information"
    assert t2.next_state == "end"
    assert session.is_finished()
    assert len(session.history) == 4  # 2 turns * (user + agent)
