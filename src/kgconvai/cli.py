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
