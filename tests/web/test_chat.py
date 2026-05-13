"""Gradio chat UI smoke + behavioural tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

gr = pytest.importorskip("gradio")


def test_build_chat_constructs_blocks():
    from kgconvai.web.chat import build_chat

    demo = build_chat(ROOT / "dialogue_graph" / "kg.json", mode="template")
    assert demo.__class__.__name__ == "Blocks"
    component_names = {b.__class__.__name__ for b in demo.blocks.values()}
    # Phase 5 layout adds these:
    assert "Chatbot" in component_names
    assert "Textbox" in component_names
    assert "Dataframe" in component_names
    assert "HTML" in component_names
    assert "Accordion" in component_names
    assert "Dropdown" in component_names


def test_chat_respond_callback_via_agent():
    """The Agent.respond_with_trace path used by the chat UI walks state correctly."""
    from kgconvai.state import DialogueSession
    from kgconvai.web.chat import _build_agent

    agent = _build_agent(ROOT / "dialogue_graph" / "kg.json", "template")
    session = DialogueSession()

    session, trace = agent.respond_with_trace("hello", session)
    assert isinstance(trace.response, str) and trace.response
    assert len(session.history) == 2  # one user turn + one agent turn


def test_build_byo_llm_returns_none_for_blank_key():
    from kgconvai.web.chat import _build_byo_llm

    assert _build_byo_llm(None, "any") is None
    assert _build_byo_llm("", "any") is None
    assert _build_byo_llm("   ", "any") is None


def test_build_byo_llm_returns_openrouter_for_real_key():
    from kgconvai.llm.openrouter import OpenRouterLLM
    from kgconvai.web.chat import _build_byo_llm

    llm = _build_byo_llm("sk-or-v1-fakekey", "deepseek/deepseek-v3-base:free")
    assert isinstance(llm, OpenRouterLLM)
    assert llm.default_model == "deepseek/deepseek-v3-base:free"


def test_chatbot_uses_messages_format_when_kwarg_supported():
    """If Gradio supports the `type` kwarg, the Chatbot is constructed with it."""
    import inspect

    if "type" not in inspect.signature(gr.Chatbot).parameters:
        pytest.skip("This Gradio version doesn't expose a `type` kwarg")

    from kgconvai.web.chat import build_chat

    demo = build_chat(ROOT / "dialogue_graph" / "kg.json", mode="template")
    chatbots = [b for b in demo.blocks.values() if b.__class__.__name__ == "Chatbot"]
    assert chatbots
    # When the kwarg is supported, kgconvai sets it to "messages"
    cb = chatbots[0]
    assert getattr(cb, "type", "messages") == "messages"
