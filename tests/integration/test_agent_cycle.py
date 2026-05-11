"""End-to-end test of the TAO cycle with all backends mocked."""

from __future__ import annotations

import pytest

from kgconvai.agent import Agent
from kgconvai.asr.base import SpeechResult
from kgconvai.state import DialogueSession
from tests.conftest import FakeASR, FakeClassifier, FakeLLM, RecordingTTS


@pytest.mark.integration
def test_full_tao_cycle_to_end(sample_graph, sample_faq, sample_templates, settings):
    """Walk the agent from start -> ask_information -> end with scripted ASR."""
    asr = FakeASR(
        [
            SpeechResult("hi there", "en"),
            SpeechResult("goodbye", "en"),
        ]
    )
    tts = RecordingTTS()
    classifier = FakeClassifier(rules={"hi there": "greet", "goodbye": "goodbye"})

    agent = Agent(
        asr=asr,
        tts=tts,
        classifier=classifier,
        graph=sample_graph,
        faq=sample_faq,
        templates=sample_templates,
        llm=None,  # template mode
        settings=settings,
    )

    session = DialogueSession()
    r1 = agent.step(session)
    assert r1.intent == "greet"
    assert r1.next_state == "ask_information"
    # Templates are keyed by intent, not next_state, so the reply is the
    # template for "greet" (not for "ask_information").
    assert r1.response == "Say hello."

    r2 = agent.step(session)
    assert r2.intent == "goodbye"
    assert r2.next_state == "end"
    assert session.is_finished()

    # TTS recorded exactly two utterances, both non-empty
    assert len(tts.spoken) == 2
    assert all(t.strip() for t in tts.spoken)


@pytest.mark.integration
def test_respond_programmatic_api(sample_graph, sample_faq, sample_templates, settings):
    """Agent.respond(text) is the library-style API: no audio, just strings."""
    agent = Agent(
        asr=FakeASR([]),  # unused
        tts=RecordingTTS(),
        classifier=FakeClassifier(rules={"hello": "greet"}),
        graph=sample_graph,
        faq=sample_faq,
        templates=sample_templates,
        llm=None,
        settings=settings,
    )
    out = agent.respond("hello")
    assert out == "Say hello."


@pytest.mark.integration
def test_history_no_longer_corrupts_with_mixed_types(
    sample_graph, sample_faq, sample_templates, settings
):
    """
    Regression for the bug in the legacy main.py:

        history += [response_text]              # bare string
        history.append(("Agent", response_text))  # tuple

    ...which would crash when response_generator did
        for speaker, text in history
    The new DialogueSession always stores Turn objects via add_*_turn.
    """
    llm = FakeLLM(reply="hi back", chat_format=False)
    agent = Agent(
        asr=FakeASR([SpeechResult("hi", "en")]),
        tts=RecordingTTS(),
        classifier=FakeClassifier(rules={"hi": "greet"}),
        graph=sample_graph,
        faq=sample_faq,
        templates=sample_templates,
        llm=llm,
        settings=settings,
    )
    session = DialogueSession()
    agent.step(session)
    # All entries are Turn objects with proper Speaker enum values
    assert all(hasattr(t, "speaker") and hasattr(t, "text") for t in session.history)
    speakers = {t.speaker.value for t in session.history}
    assert speakers == {"user", "agent"}
