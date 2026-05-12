"""Streamlit admin panel smoke tests.

Streamlit's `render()` requires a running script context, but we can still
exercise the helpers: load, _graph_html, _save.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

st = pytest.importorskip("streamlit")
pyvis = pytest.importorskip("pyvis")


def test_admin_module_imports():
    from kgconvai.web import admin  # noqa: F401


def test_admin_load_and_save_roundtrip(tmp_path):
    from kgconvai.web.admin import _load, _save

    src = ROOT / "dialogue_graph" / "kg.json"
    data = _load(src)
    out = tmp_path / "kg.json"
    _save(out, data)
    reloaded = _load(out)
    assert reloaded.state_ids() == data.state_ids()
    assert reloaded.intent_ids() == data.intent_ids()
    assert len(reloaded.transitions) == len(data.transitions)


def test_admin_graph_html_is_renderable():
    from kgconvai.kg.schema import KGData
    from kgconvai.web.admin import _graph_html

    data = KGData.from_json(ROOT / "dialogue_graph" / "kg.json")
    html = _graph_html(data)
    assert html  # non-empty
    # PyVis output is a full HTML document
    assert "<html" in html.lower()
    # Every state id should appear in the rendered graph
    for s in data.states:
        assert s.id in html
