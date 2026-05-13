"""PyVis-based dialogue-graph renderer used by the Gradio chat UI.

Renders a :class:`~kgconvai.dialogue.graph.DialogueGraph` as an interactive
PyVis network with three node colour states:

* **amber** -- the conversation's current state
* **green** -- a previously visited state (in this conversation)
* **gray**  -- not yet visited

The result is a self-contained HTML string suitable for injection into
``gr.HTML``.
"""

from __future__ import annotations

import html

from kgconvai.dialogue.graph import DialogueGraph

CURRENT_COLOR = "#f59e0b"  # amber-500
VISITED_COLOR = "#10b981"  # emerald-500
PENDING_COLOR = "#94a3b8"  # slate-400


def render_graph_html(
    graph: DialogueGraph,
    *,
    current_state: str | None = None,
    visited_states: list[str] | None = None,
    height_px: int = 380,
) -> str:
    """Return a self-contained HTML snippet that renders ``graph`` with
    the given state highlighted.

    PyVis is imported lazily so headless environments (no [web] extra
    installed) can still ``import kgconvai.web``.
    """
    from pyvis.network import Network

    visited = set(visited_states or [])
    net = Network(
        height=f"{height_px}px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#0f172a",  # slate-900, matches dark Gradio themes
        font_color="#f1f5f9",
    )
    # Disable the live force-directed physics simulation -- it burns CPU
    # forever and the graph never reaches a stable layout, which made
    # Firefox slow to a crawl on each turn. Use a deterministic seed so
    # nodes stay in place across re-renders.
    net.toggle_physics(False)
    net.set_options("""
    {
      "interaction": {"hover": true, "navigationButtons": false, "zoomView": true},
      "physics": {"enabled": false},
      "layout": {"randomSeed": 42, "improvedLayout": true},
      "nodes": {"shape": "dot", "borderWidth": 2},
      "edges": {"smooth": {"type": "continuous"}, "color": {"color": "#475569"}}
    }
    """)

    for state_id in graph.states():
        if state_id == current_state:
            color = CURRENT_COLOR
            size = 28
        elif state_id in visited:
            color = VISITED_COLOR
            size = 22
        else:
            color = PENDING_COLOR
            size = 20
        net.add_node(state_id, label=state_id, color=color, size=size)

    for from_state, intent, to_state in graph.edges():
        net.add_edge(from_state, to_state, label=intent, arrows="to")

    # PyVis returns a full <html> document with inline <script> tags that
    # pull vis-network.js from a CDN. Gradio's gr.HTML strips/sanitises
    # scripts, so render the network inside an <iframe srcdoc="..."> where
    # those scripts can execute in their own isolated context.
    body = net.generate_html(notebook=False)
    escaped = html.escape(body, quote=True)
    return (
        f'<iframe srcdoc="{escaped}" '
        f'style="width:100%;height:{height_px}px;border:0;'
        f'border-radius:8px;background:#0f172a;" '
        f'sandbox="allow-scripts allow-same-origin"></iframe>'
    )
