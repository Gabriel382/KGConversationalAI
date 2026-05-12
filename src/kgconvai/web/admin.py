"""Streamlit admin panel for editing the dialogue knowledge graph.

Run with:
    kgconvai web admin --data dialogue_graph/kg.json

The app reads ``KGData`` from disk, lets the user edit each section in
data-editor tables, visualises the dialogue graph as a PyVis network, and
writes the canonicalised JSON back when "Save" is clicked. Edits are
validated against the JSON Schema before save, so invalid input never reaches
disk.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from kgconvai.kg.schema import KGData

PYVIS_HTML_TMPL = """
<!doctype html><html><body style="margin:0">{body}</body></html>
"""


def _load(path: Path) -> KGData:
    return KGData.from_json(path)


def _save(path: Path, data: KGData) -> None:
    data.to_json(path)


def _graph_html(data: KGData) -> str:
    """Render the dialogue graph as a PyVis network and return its HTML."""
    from pyvis.network import Network

    net = Network(height="500px", width="100%", directed=True, notebook=False)
    net.toggle_physics(True)
    for s in data.states:
        color = "#ef4444" if s.is_terminal else ("#10b981" if s.requires_knowledge else "#3b82f6")
        net.add_node(s.id, label=s.id, color=color, title=s.description or s.id)
    for t in data.transitions:
        net.add_edge(t.from_state, t.to, label=t.intent, arrows="to")
    return net.generate_html(notebook=False)


def render() -> None:  # pragma: no cover -- streamlit driver
    """Top-level entry point invoked by streamlit run."""
    st.set_page_config(
        page_title="KGConvAI admin",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("KGConvAI — knowledge-graph admin")

    default_path = os.environ.get("KGCONVAI_DATA", "dialogue_graph/kg.json")
    with st.sidebar:
        path = Path(st.text_input("Data file", value=default_path))
        if not path.exists():
            st.error(f"{path} does not exist")
            return
        if st.button("Reload from disk", use_container_width=True):
            st.session_state.pop("data", None)

    if "data" not in st.session_state:
        st.session_state.data = _load(path)
    data: KGData = st.session_state.data

    tabs = st.tabs(["Graph", "States", "Intents", "Transitions", "FAQ", "Templates", "Raw JSON"])

    with tabs[0]:
        st.subheader("Dialogue graph")
        st.caption(
            "Nodes — blue: regular state, green: requires knowledge, red: terminal. "
            "Edges labelled by intent."
        )
        try:
            st.components.v1.html(_graph_html(data), height=520)
        except Exception as exc:
            st.warning(f"Graph rendering failed: {exc}")

    with tabs[1]:
        st.subheader("States")
        edited = st.data_editor(
            [s.model_dump() for s in data.states],
            num_rows="dynamic",
            use_container_width=True,
            key="states_editor",
        )
        data.states = (
            [type(data.states[0]).model_validate(r) for r in edited if r.get("id")]
            if data.states
            else []
        )

    with tabs[2]:
        st.subheader("Intents")
        edited = st.data_editor(
            [i.model_dump() for i in data.intents],
            num_rows="dynamic",
            use_container_width=True,
            key="intents_editor",
        )
        if data.intents:
            intent_cls = type(data.intents[0])
            data.intents = [intent_cls.model_validate(r) for r in edited if r.get("id")]

    with tabs[3]:
        st.subheader("Transitions")
        edited = st.data_editor(
            [t.model_dump(by_alias=True) for t in data.transitions],
            num_rows="dynamic",
            use_container_width=True,
            key="transitions_editor",
        )
        if data.transitions:
            cls = type(data.transitions[0])
            data.transitions = [
                cls.model_validate(r)
                for r in edited
                if r.get("from") and r.get("to") and r.get("intent")
            ]

    with tabs[4]:
        st.subheader("FAQ entries")
        edited = st.data_editor(
            [f.model_dump() for f in data.faqs],
            num_rows="dynamic",
            use_container_width=True,
            key="faqs_editor",
        )
        if data.faqs:
            faq_cls = type(data.faqs[0])
            data.faqs = [faq_cls.model_validate(r) for r in edited if r.get("id")]

    with tabs[5]:
        st.subheader("Response templates")
        edited = st.data_editor(
            [tpl.model_dump() for tpl in data.templates],
            num_rows="dynamic",
            use_container_width=True,
            key="templates_editor",
        )
        if data.templates:
            tpl_cls = type(data.templates[0])
            data.templates = [tpl_cls.model_validate(r) for r in edited if r.get("intent")]

    with tabs[6]:
        st.subheader("Raw canonical JSON")
        st.code(data.to_json(), language="json")

    # --- Save bar ---
    st.divider()
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("Save to disk", type="primary", use_container_width=True):
            try:
                _save(path, data)
                st.success(f"Saved {path}")
                st.session_state.pop("data", None)  # force reload from disk
            except Exception as exc:
                st.error(f"Validation or write failed: {exc}")
    with cols[1]:
        if st.button("Discard changes", use_container_width=True):
            st.session_state.pop("data", None)
            st.rerun()


if __name__ == "__main__":  # pragma: no cover
    render()
