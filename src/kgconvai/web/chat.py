"""Gradio chat UI for kgconvai.

Layout:

* Left column: chat history, input box, send/reset buttons, and a
  "Use my own LLM" accordion where any visitor can paste an OpenRouter
  API key for their session (kept in ``gr.State``, never persisted).
* Right column: a PyVis-rendered dialogue graph that highlights the
  current state, and a trace table showing each turn's intent + state
  transition + source.

Per-session state (``DialogueSession``, trace rows, visited-states list,
API key) lives in ``gr.State`` components so multiple browser tabs hold
independent conversations on the same server.
"""

from __future__ import annotations

import inspect as _inspect
from pathlib import Path
from typing import TYPE_CHECKING

from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.logging import get_logger
from kgconvai.nlu.faq import FAQStore
from kgconvai.state import DialogueSession
from kgconvai.web._graph_viz import render_graph_html

if TYPE_CHECKING:  # pragma: no cover
    pass

log = get_logger(__name__)

DEFAULT_OPENROUTER_MODELS = [
    "deepseek/deepseek-v3-base:free",
    "deepseek/deepseek-r1-zero:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def _build_agent(data_path: Path, mode: str):
    """Construct the default Agent used when no per-visitor key is provided.

    The classifier is a deliberately dumb substring matcher so the demo works
    with zero downloads; the LLM defaults to template mode for the same reason.
    Visitors can override the LLM per-session via the BYO-key accordion.
    """
    from kgconvai.agent import Agent
    from kgconvai.asr.base import ASR, SpeechResult
    from kgconvai.llm.base import LLMGenerator
    from kgconvai.nlu.classifier import Classification, Classifier
    from kgconvai.tts.base import TTS

    settings = Settings(llm_mode=mode)  # type: ignore[arg-type]

    class _SilentASR(ASR):
        def listen(self) -> SpeechResult:
            return SpeechResult("", "en")

    class _SilentTTS(TTS):
        def say(self, text: str) -> None:
            return None

    class _SubstringClassifier(Classifier):
        """Fallback classifier (used when [embeddings] isn't installed)."""

        def classify(self, text: str, candidates: list[str]) -> list[Classification]:
            t = text.lower()
            scored = []
            for c in candidates:
                tokens = c.replace("_", " ").lower().split()
                overlap = sum(1 for tok in tokens if tok in t)
                scored.append(Classification(label=c, score=overlap / max(len(tokens), 1)))
            scored.sort(key=lambda x: x.score, reverse=True)
            return scored

    llm: LLMGenerator | None = None
    if settings.llm_mode == "local":
        from kgconvai.llm.ollama import OllamaLLM

        llm = OllamaLLM(url=settings.ollama_url, default_model=settings.ollama_model)
    elif settings.llm_mode == "api" and settings.openrouter_api_key:
        from kgconvai.llm.openrouter import OpenRouterLLM

        llm = OpenRouterLLM(
            api_key=settings.openrouter_api_key,
            url=settings.openrouter_url,
            default_model=settings.openrouter_model,
        )

    return Agent(
        asr=_SilentASR(),
        tts=_SilentTTS(),
        classifier=_SubstringClassifier(),
        graph=DialogueGraph.from_path(data_path),
        faq=FAQStore.from_path(data_path),
        templates=TemplateStore.from_path(data_path),
        llm=llm,
        settings=settings,
    )


def _build_byo_llm(api_key: str | None, model: str | None):
    """Return an OpenRouterLLM if ``api_key`` looks usable, else ``None``."""
    if not api_key or not api_key.strip():
        return None
    from kgconvai.llm.openrouter import OpenRouterLLM

    return OpenRouterLLM(
        api_key=api_key.strip(),
        default_model=(model or DEFAULT_OPENROUTER_MODELS[0]).strip(),
    )


def build_chat(
    data_path: Path = Path("dialogue_graph/kg.json"),
    *,
    mode: str = "template",
    title: str = "KGConvAI - Graph-Driven Voice Agent",
):  # -> gr.Blocks
    """Construct the Gradio demo. Returns a Blocks instance ready to launch."""
    import gradio as gr

    agent = _build_agent(data_path, mode)
    graph_obj = agent.dialogue.graph
    initial_graph_html = render_graph_html(graph_obj, current_state="start")

    def respond(
        message: str,
        history: list,
        session_state: DialogueSession | None,
        trace_rows: list[list[str]] | None,
        visited_states: list[str] | None,
        api_key: str,
        model_name: str,
    ):
        if not message or not message.strip():
            # No-op: keep state intact, just clear the textbox
            current = session_state.current_state if session_state else "start"
            return (
                history,
                session_state,
                trace_rows or [],
                visited_states or [],
                render_graph_html(
                    graph_obj, current_state=current, visited_states=visited_states or []
                ),
                "",
            )

        if session_state is None:
            session_state = DialogueSession()
        from_state = session_state.current_state

        # BYO-key override (per call, not persisted on the agent)
        llm_override = _build_byo_llm(api_key, model_name)
        source = (
            "openrouter"
            if llm_override is not None
            else ("template" if agent.llm is None else "default")
        )

        session_state, result = agent.respond_with_trace(
            message, session_state, llm_override=llm_override
        )

        history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.response},
        ]

        visited = list(visited_states or [])
        if from_state not in visited:
            visited.append(from_state)
        if result.next_state not in visited:
            visited.append(result.next_state)

        trace_rows = (trace_rows or []) + [
            [
                str(len(trace_rows or []) + 1),
                result.intent,
                f"{from_state} -> {result.next_state}",
                (result.knowledge or "")[:60],
                source,
            ]
        ]

        graph_html = render_graph_html(
            graph_obj,
            current_state=session_state.current_state,
            visited_states=visited,
        )

        return history, session_state, trace_rows, visited, graph_html, ""

    def reset(*_args):
        return [], None, [], [], render_graph_html(graph_obj, current_state="start"), ""

    with gr.Blocks(title=title) as demo:
        gr.Markdown(
            f"# {title}\n"
            "Talk to the agent in plain text. State and conversation history "
            "are isolated per browser session.  \n"
            f"**Default mode:** `{mode}` &nbsp;|&nbsp; **Data:** `{data_path}` "
            "&nbsp;|&nbsp; *Paste an OpenRouter key below to get LLM responses.*"
        )

        with gr.Row():
            # ------- LEFT: chat + BYO key ------------------------------------
            with gr.Column(scale=3):
                # Gradio 5.x requires type="messages" for dict-shaped messages;
                # Gradio 6.x removed the kwarg (messages is the only format).
                # Sniff at runtime so both work.
                _cb_kwargs: dict = {"label": "Conversation", "height": 420}
                if "type" in _inspect.signature(gr.Chatbot).parameters:
                    _cb_kwargs["type"] = "messages"
                chatbot = gr.Chatbot(**_cb_kwargs)
                msg = gr.Textbox(
                    placeholder="e.g. 'I'd like to book a meeting'",
                    label="Your message",
                    autofocus=True,
                )
                with gr.Row():
                    submit = gr.Button("Send", variant="primary")
                    clear = gr.Button("Reset conversation")

                with gr.Accordion("Use my own OpenRouter LLM (optional)", open=False):
                    gr.Markdown(
                        "Paste your OpenRouter API key to get LLM-generated "
                        "replies for *this browser session only*. "
                        "The key is kept in memory, never logged, and never "
                        "persisted. Get a free key at "
                        "[openrouter.ai/keys](https://openrouter.ai/keys)."
                    )
                    api_key = gr.Textbox(
                        label="OpenRouter API key",
                        type="password",
                        placeholder="sk-or-v1-...",
                    )
                    model_choice = gr.Dropdown(
                        label="Model",
                        choices=DEFAULT_OPENROUTER_MODELS,
                        value=DEFAULT_OPENROUTER_MODELS[0],
                        allow_custom_value=True,
                    )

            # ------- RIGHT: graph viz + trace table --------------------------
            with gr.Column(scale=2):
                gr.Markdown("### Dialogue graph")
                gr.Markdown(
                    "<span style='color:#f59e0b'>**amber**</span> = current "
                    "state, <span style='color:#10b981'>**green**</span> = "
                    "visited, <span style='color:#94a3b8'>gray</span> = pending.",
                )
                graph_view = gr.HTML(value=initial_graph_html)

                gr.Markdown("### Cycle trace")
                trace_table = gr.Dataframe(
                    headers=["Turn", "Intent", "Transition", "Knowledge", "Source"],
                    datatype=["str", "str", "str", "str", "str"],
                    value=[],
                    interactive=False,
                    wrap=True,
                )

        # Per-session state — no defaults so Gradio doesn't try to schema-fy them
        session_state = gr.State()
        trace_rows = gr.State([])
        visited_states = gr.State([])

        submit_inputs = [
            msg,
            chatbot,
            session_state,
            trace_rows,
            visited_states,
            api_key,
            model_choice,
        ]
        submit_outputs = [
            chatbot,
            session_state,
            trace_rows,
            visited_states,
            graph_view,
            msg,
        ]
        submit.click(respond, submit_inputs, submit_outputs)
        msg.submit(respond, submit_inputs, submit_outputs)
        clear.click(
            reset,
            [chatbot, session_state, trace_rows, visited_states],
            [chatbot, session_state, trace_rows, visited_states, graph_view, msg],
        )

        # The dataframe needs to be re-rendered each call because gr.State alone
        # doesn't push updates to the visual component.
        def _sync_trace_table(rows):
            return rows or []

        trace_rows.change(_sync_trace_table, [trace_rows], [trace_table])

    return demo
