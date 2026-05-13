"""Ensure the PyVis graph viz renders inside an iframe so Gradio doesn't strip it."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytest.importorskip("pyvis")

from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.web._graph_viz import render_graph_html


@pytest.fixture()
def graph() -> DialogueGraph:
    return DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")


def test_output_is_an_iframe(graph):
    html = render_graph_html(graph, current_state="start")
    assert html.startswith("<iframe ")
    assert html.rstrip().endswith("</iframe>")


def test_iframe_uses_srcdoc(graph):
    html = render_graph_html(graph, current_state="start")
    assert 'srcdoc="' in html


def test_iframe_sandbox_allows_scripts(graph):
    """PyVis scripts must execute, so sandbox must include allow-scripts."""
    html = render_graph_html(graph, current_state="start")
    assert 'sandbox="allow-scripts allow-same-origin"' in html


def test_iframe_srcdoc_contains_full_pyvis_document(graph):
    """The srcdoc attribute should embed the entire PyVis HTML document
    (HTML-escaped). State ids appear inside that document."""
    html = render_graph_html(graph, current_state="start")
    # State ids appear in the escaped srcdoc payload
    for state_id in graph.states():
        assert state_id in html
