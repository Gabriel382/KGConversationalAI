"""PyVis graph rendering tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytest.importorskip("pyvis")

from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.web._graph_viz import (
    CURRENT_COLOR,
    PENDING_COLOR,
    VISITED_COLOR,
    render_graph_html,
)


@pytest.fixture()
def graph() -> DialogueGraph:
    return DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")


def test_render_graph_html_highlights_current_state(graph):
    html = render_graph_html(graph, current_state="book_meeting")
    assert CURRENT_COLOR in html
    # Every state's id should appear as a node label
    for state_id in graph.states():
        assert state_id in html


def test_render_graph_html_marks_visited_states(graph):
    html = render_graph_html(
        graph,
        current_state="ask_information",
        visited_states=["start", "ask_information"],
    )
    # Both the current and visited colours should appear
    assert CURRENT_COLOR in html  # ask_information is current
    assert VISITED_COLOR in html  # start is visited but not current


def test_render_graph_html_default_state_all_pending(graph):
    html = render_graph_html(graph)
    assert PENDING_COLOR in html  # nothing highlighted -> everything pending
    assert CURRENT_COLOR not in html


def test_render_graph_html_contains_transition_labels(graph):
    html = render_graph_html(graph, current_state="start")
    # 'greet' is a transition label from start -> ask_information
    assert "greet" in html
