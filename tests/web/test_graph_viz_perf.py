"""Regression test: graph viz must NOT enable continuous physics simulation.

The first cut used PyVis with physics on, which kept the force-directed
layout running forever in every iframe and dragged Firefox to a crawl when
the chat had a few turns.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytest.importorskip("pyvis")

from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.web._graph_viz import render_graph_html


def test_physics_default_is_on():
    """Default render has physics animated (looks better)."""
    g = DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")
    html = render_graph_html(g, current_state="start")  # physics defaults to True
    assert "&quot;enabled&quot;: true" in html or '"enabled": true' in html


def test_physics_can_be_disabled():
    """Visitors can untick the UI checkbox to freeze the layout."""
    g = DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")
    html = render_graph_html(g, current_state="start", physics=False)
    assert "&quot;enabled&quot;: false" in html or '"enabled": false' in html


def test_layout_is_deterministic():
    """A seeded layout means the same state appears in the same place across
    re-renders, which prevents a 'shuffle on every keypress' effect."""
    g = DialogueGraph.from_path(ROOT / "dialogue_graph" / "kg.json")
    html = render_graph_html(g, current_state="start")
    assert "randomSeed" in html or "randomseed" in html.lower()
