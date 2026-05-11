"""Typer CLI for kgconvai."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from kgconvai import __version__
from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.logging import configure_logging, get_logger
from kgconvai.nlu.faq import FAQStore

app = typer.Typer(
    name="kgconvai",
    help="Graph-driven voice agent with a Thought-Action-Observation control loop.",
    add_completion=False,
)
console = Console()
log = get_logger(__name__)


@app.callback()
def _global(
    log_level: str = typer.Option("INFO", "--log-level", help="Log level (DEBUG/INFO/WARN/ERROR)."),
    log_format: str = typer.Option("console", "--log-format", help="'console' or 'json'."),
) -> None:
    """Configure logging for every subcommand."""
    configure_logging(level=log_level, fmt=log_format)  # type: ignore[arg-type]


@app.command()
def version() -> None:
    """Print the installed kgconvai version."""
    console.print(f"kgconvai {__version__}")


@app.command()
def info() -> None:
    """Show resolved settings."""
    settings = Settings()
    table = Table(title="kgconvai settings", show_header=True)
    table.add_column("Key", style="bold")
    table.add_column("Value")
    for k, v in settings.model_dump().items():
        table.add_row(k, str(v))
    console.print(table)


@app.command()
def validate(
    data_dir: Path = typer.Option(Path("dialogue_graph"), help="Folder with JSON config."),
) -> None:
    """Validate the dialogue graph, FAQ and templates load correctly."""
    graph = DialogueGraph.from_path(data_dir / "conversation_graph.json")
    faq = FAQStore.from_path(data_dir / "faq.json")
    templates = TemplateStore.from_path(data_dir / "templates.json")

    console.print(
        f"[green]ok[/] dialogue graph: {len(graph.states())} states, "
        f"{len(graph.candidate_intents())} intents"
    )
    console.print(f"[green]ok[/] faq: {len(faq.intents())} intents")
    console.print(f"[green]ok[/] templates: {len(templates._templates)} entries")


@app.command()
def run(
    mode: str = typer.Option(
        "template",
        "--mode",
        help="'local' (Ollama), 'api' (OpenRouter), or 'template' (no LLM).",
    ),
    data_dir: Path = typer.Option(Path("dialogue_graph"), help="Folder with JSON config."),
) -> None:
    """Run the voice agent until the conversation reaches 'end'."""
    # Lazy imports so this CLI module works without [voice]/[nlu] extras
    # installed (used by `version`, `info`, `validate` in CI).
    from kgconvai.agent import Agent
    from kgconvai.asr.whisper import WhisperASR
    from kgconvai.llm.base import LLMGenerator
    from kgconvai.llm.ollama import OllamaLLM
    from kgconvai.llm.openrouter import OpenRouterLLM
    from kgconvai.nlu.classifier import ZeroShotClassifier
    from kgconvai.tts.pyttsx3_engine import Pyttsx3TTS

    settings = Settings(llm_mode=mode)  # type: ignore[arg-type]

    llm: LLMGenerator | None
    if settings.llm_mode == "api":
        if not settings.openrouter_api_key:
            raise typer.BadParameter(
                "OpenRouter API key not configured. Set KGCONVAI_OPENROUTER_API_KEY."
            )
        llm = OpenRouterLLM(
            api_key=settings.openrouter_api_key,
            url=settings.openrouter_url,
            default_model=settings.openrouter_model,
        )
    elif settings.llm_mode == "local":
        llm = OllamaLLM(url=settings.ollama_url, default_model=settings.ollama_model)
    else:
        llm = None

    agent = Agent(
        asr=WhisperASR(
            model_name=settings.whisper_model,
            max_record_seconds=settings.speech_max_record_seconds,
            silence_padding_seconds=settings.speech_silence_padding_seconds,
            vad_aggressiveness=settings.vad_aggressiveness,
        ),
        tts=Pyttsx3TTS(rate=settings.tts_rate, volume=settings.tts_volume),
        classifier=ZeroShotClassifier(model_name=settings.classifier_model),
        graph=DialogueGraph.from_path(data_dir / "conversation_graph.json"),
        faq=FAQStore.from_path(data_dir / "faq.json"),
        templates=TemplateStore.from_path(data_dir / "templates.json"),
        llm=llm,
        settings=settings,
    )
    agent.run()


# -----------------------------------------------------------------------------
# 'kg' subcommand group: import / export / validate / diff knowledge graphs
# -----------------------------------------------------------------------------

kg_app = typer.Typer(help="Manage knowledge-graph backends and JSON sync.")
app.add_typer(kg_app, name="kg")


@kg_app.command("validate")
def kg_validate(
    src: Path = typer.Argument(Path("dialogue_graph/kg.json"), help="Canonical KG JSON."),
) -> None:
    """Validate a KG JSON file against the canonical schema."""
    from kgconvai.kg.schema import KGData

    data = KGData.from_json(src)
    console.print(
        f"[green]ok[/] {src}: {len(data.states)} states, "
        f"{len(data.intents)} intents, {len(data.transitions)} transitions, "
        f"{len(data.faqs)} faqs, {len(data.templates)} templates"
    )


@kg_app.command("export")
def kg_export(
    backend: str = typer.Option("rdf", "--backend", help="rdf | neo4j"),
    src: Path = typer.Option(Path("dialogue_graph/kg.json"), "--from"),
    dst: Path = typer.Option(Path("dialogue_graph/kg.export.json"), "--to"),
    ontology: Path | None = typer.Option(None, help="Optional ontology .ttl to load."),
    neo4j_uri: str = typer.Option("bolt://localhost:7687", help="Neo4j Bolt URI."),
    neo4j_user: str = typer.Option("neo4j", help="Neo4j user."),
    neo4j_password: str = typer.Option("kgconvai", help="Neo4j password."),
) -> None:
    """Import canonical JSON into the chosen backend, then export back to JSON.

    The result of a clean round-trip should equal the input. Use this to
    sanity-check edits made directly in Neo4j Browser.
    """
    from kgconvai.kg.schema import KGData

    data = KGData.from_json(src)
    if backend == "rdf":
        from kgconvai.kg.rdf_backend import RDFBackend

        rdf_be = RDFBackend(ontology_paths=[ontology] if ontology else [])
        rdf_graph = rdf_be.import_(data)
        exported = rdf_be.export(rdf_graph)
    elif backend == "neo4j":
        from kgconvai.kg.neo4j_backend import Neo4jBackend

        with Neo4jBackend(neo4j_uri, neo4j_user, neo4j_password) as neo_be:
            neo_graph = neo_be.import_(data)
            exported = neo_be.export(neo_graph)
    else:
        raise typer.BadParameter(f"unknown backend: {backend!r}")

    exported.to_json(dst)
    console.print(f"[green]ok[/] exported {backend} graph -> {dst}")


@kg_app.command("diff")
def kg_diff(
    a: Path = typer.Argument(..., help="First KG JSON."),
    b: Path = typer.Argument(..., help="Second KG JSON."),
) -> None:
    """Show a structural diff between two KG JSON files (canonicalised)."""
    import json

    from kgconvai.kg.schema import KGData

    la = json.loads(KGData.from_json(a).to_json())
    lb = json.loads(KGData.from_json(b).to_json())

    sections = ("states", "intents", "transitions", "faqs", "templates", "entities", "relations")
    any_diff = False
    for section in sections:
        if la.get(section) != lb.get(section):
            any_diff = True
            la_n = len(la.get(section, []))
            lb_n = len(lb.get(section, []))
            console.print(f"[yellow]{section} differs[/] (a={la_n}, b={lb_n})")
    if not any_diff:
        console.print("[green]identical[/]")


# -----------------------------------------------------------------------------
# 'web' subcommand group: launch browser-based chat / admin
# -----------------------------------------------------------------------------

web_app = typer.Typer(help="Launch browser-based interfaces (Gradio / Streamlit).")
app.add_typer(web_app, name="web")


@web_app.command("chat")
def web_chat(
    data: Path = typer.Option(Path("dialogue_graph/kg.json"), help="Canonical KG JSON."),
    mode: str = typer.Option("template", help="LLM mode: local | api | template."),
    host: str = typer.Option("127.0.0.1", help="Host to bind."),
    port: int = typer.Option(7860, help="Port to bind."),
    share: bool = typer.Option(False, help="Create a public Gradio share link."),
) -> None:
    """Run the Gradio chat UI."""
    from kgconvai.web.chat import build_chat

    demo = build_chat(data, mode=mode)
    demo.launch(server_name=host, server_port=port, share=share)


@web_app.command("admin")
def web_admin(
    data: Path = typer.Option(Path("dialogue_graph/kg.json"), help="Canonical KG JSON."),
    port: int = typer.Option(8501, help="Port to bind."),
) -> None:
    """Run the Streamlit admin panel (visual graph + section editors)."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "KGCONVAI_DATA": str(data)}
    admin_py = Path(__file__).parent / "web" / "admin.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(admin_py),
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    console.print(f"[bold]Launching admin panel at[/] http://localhost:{port}")
    subprocess.run(cmd, env=env, check=False)
