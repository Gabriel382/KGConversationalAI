"""Sanity check that the shipped dialogue_graph/*.json files actually load."""

from pathlib import Path

import pytest

from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.nlu.faq import FAQStore

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_repo_dialogue_graph_loads():
    g = DialogueGraph.from_path(ROOT / "dialogue_graph" / "conversation_graph.json")
    assert "start" in g.states()


@pytest.mark.integration
def test_repo_faq_loads():
    faq = FAQStore.from_path(ROOT / "dialogue_graph" / "faq.json")
    assert faq.intents()  # non-empty


@pytest.mark.integration
def test_repo_templates_load():
    t = TemplateStore.from_path(ROOT / "dialogue_graph" / "templates.json")
    assert t.instruction_for("greet")
