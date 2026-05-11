"""Gradio chat UI for kgconvai.

Wraps the existing :class:`~kgconvai.Agent` so anyone can talk to the agent
in a browser without installing audio dependencies. The UI keeps a
``DialogueSession`` per Gradio session (``gr.State``), so multiple visitors
on the same server hold independent conversations.

Usage:
    >>> from kgconvai.web.chat import build_chat
    >>> demo = build_chat()
    >>> demo.launch()

Or via the CLI: ``kgconvai web chat --port 7860``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.logging import get_logger
from kgconvai.nlu.faq import FAQStore
from kgconvai.state import DialogueSession

if TYPE_CHECKING:  # pragma: no cover
    pass

log = get_logger(__name__)


def _build_agent(
    data_path: Path,
    mode: str,
):  # -> kgconvai.Agent (forward import to keep package importable headless)
    from kgconvai.agent import Agent
    from kgconvai.asr.base import ASR, SpeechResult
    from kgconvai.llm.base import LLMGenerator
    from kgconvai.nlu.classifier import Classification, Classifier
    from kgconvai.tts.base import TTS

    settings = Settings(llm_mode=mode)  # type: ignore[arg-type]

    # ASR/TTS aren't used in the web UI — bind harmless stand-ins.
    class _SilentASR(ASR):
        def listen(self) -> SpeechResult:
            return SpeechResult("", "en")

    class _SilentTTS(TTS):
        def say(self, text: str) -> None:
            return None

    # Use a fast, deterministic classifier for FAQ in the demo if available.
    # Falls back to a trivial substring classifier so the demo works without
    # any heavy NLU models installed.
    class _SubstringClassifier(Classifier):
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


def build_chat(
    data_path: Path = Path("dialogue_graph/kg.json"),
    *,
    mode: str = "template",
    title: str = "KGConvAI — Graph-Driven Voice Agent",
):  # -> gr.Blocks
    """Construct the Gradio demo. Returns a Blocks instance ready to launch."""
    import gradio as gr

    agent = _build_agent(data_path, mode)

    def respond(message: str, history: list, session_state: DialogueSession | None):
        if session_state is None:
            session_state = DialogueSession()
        reply = agent.respond(message, session_state)
        history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply},
        ]
        return history, session_state, ""

    def reset(_history, _state):
        return [], DialogueSession(), ""

    with gr.Blocks(title=title) as demo:
        gr.Markdown(
            f"# {title}\n"
            "Talk to the agent in plain text. State and conversation history "
            "are isolated per browser session.\n"
            f"**Mode:** `{mode}` &nbsp;|&nbsp; **Data:** `{data_path}`"
        )
        chatbot = gr.Chatbot(label="Conversation", height=420)
        msg = gr.Textbox(
            placeholder="e.g. 'I'd like to book a meeting'",
            label="Your message",
            autofocus=True,
        )
        with gr.Row():
            submit = gr.Button("Send", variant="primary")
            clear = gr.Button("Reset conversation")
        session_state = gr.State(value=DialogueSession())

        submit.click(respond, [msg, chatbot, session_state], [chatbot, session_state, msg])
        msg.submit(respond, [msg, chatbot, session_state], [chatbot, session_state, msg])
        clear.click(reset, [chatbot, session_state], [chatbot, session_state, msg])

    return demo
