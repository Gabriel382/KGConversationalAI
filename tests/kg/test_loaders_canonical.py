"""Existing loaders (DialogueGraph, FAQStore, TemplateStore) must accept the
new canonical kg.json format AND the legacy nested format."""

from __future__ import annotations

import json
from pathlib import Path

from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.nlu.faq import FAQStore

ROOT = Path(__file__).resolve().parents[2]


def test_dialogue_graph_loads_canonical():
    g = DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")
    assert "start" in g.states()
    assert "end" in g.states()
    # provide_information must be a KB state per the kg.json definition
    node = g.transition("ask_information", "ask_information")
    assert node.next_state == "provide_information"
    assert node.requires_kb is True


def test_dialogue_graph_loads_legacy_format(tmp_path):
    legacy = tmp_path / "graph.json"
    legacy.write_text(json.dumps({"start": {"greet": "end"}, "end": {}}))
    g = DialogueGraph.from_path(legacy)
    assert g.transition("start", "greet").next_state == "end"


def test_faq_store_loads_canonical():
    faq = FAQStore.from_path(ROOT / "dialogue_graph" / "kg.json")
    assert "ask_information" in faq.intents()
    assert any(
        "9 AM to 6 PM" in (faq.answer("ask_information", q) or "")
        for q in faq.questions("ask_information")
    )


def test_faq_store_loads_legacy_format(tmp_path):
    legacy = tmp_path / "faq.json"
    legacy.write_text(json.dumps({"greet": {"hi": "hello"}}))
    faq = FAQStore.from_path(legacy)
    assert faq.answer("greet", "hi") == "hello"


def test_template_store_loads_canonical():
    tpl = TemplateStore.from_path(ROOT / "dialogue_graph" / "kg.json")
    assert tpl.fallback_for("greet")


def test_template_store_loads_legacy_format(tmp_path):
    legacy = tmp_path / "tpl.json"
    legacy.write_text(json.dumps({"greet": "Say hello"}))
    tpl = TemplateStore.from_path(legacy)
    assert tpl.fallback_for("greet") == "Say hello"
