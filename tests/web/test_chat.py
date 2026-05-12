"""Gradio chat UI smoke tests.

We don't actually launch the server; just verify the Blocks construct and
that the underlying respond() callback walks the dialogue graph and updates
the per-session state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

gr = pytest.importorskip("gradio")


def test_build_chat_constructs_blocks():
    from kgconvai.web.chat import build_chat

    demo = build_chat(ROOT / "dialogue_graph" / "kg.json", mode="template")
    # Gradio Blocks is the top-level container; spot-check it has children.
    assert demo.__class__.__name__ == "Blocks"
    component_names = {b.__class__.__name__ for b in demo.blocks.values()}
    assert "Chatbot" in component_names
    assert "Textbox" in component_names


def test_chat_respond_callback_via_agent():
    """The Agent.respond path used by the chat UI walks state correctly."""
    from kgconvai.state import DialogueSession
    from kgconvai.web.chat import _build_agent

    agent = _build_agent(ROOT / "dialogue_graph" / "kg.json", "template")
    session = DialogueSession()

    reply = agent.respond("hello", session)
    assert isinstance(reply, str) and reply
    assert session.current_state in {"ask_information", "start"}
    assert len(session.history) == 2  # one user turn + one agent turn
