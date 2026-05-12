# 🎤🧠🔊 KGConvAI — Graph-Driven Voice Agent with TAO Cycle

[![CI](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/ci.yml)
[![Eval](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/eval.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/eval.yml)
[![Docs](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/docs.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/docs.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-1f5082.svg)](https://mypy.readthedocs.io/)

A modular voice-controlled conversational agent that follows the
**Thought-Action-Observation (TAO)** cycle, built around a graph-based
dialogue manager, optional FAQ retrieval, and pluggable LLM backends.

> **Status:** alpha (0.2.0). The package is usable as a library and via the
> CLI. Knowledge-graph backends (RDF/Neo4j) land in 0.3.0.

---

## What it does

```
[ user speech ]
       │
       ▼
┌──────────────┐    ┌────────────────────────────────┐    ┌──────────────┐
│  Observation │ →  │           Thought              │ →  │    Action    │
│  Whisper STT │    │  intent → dialogue graph →     │    │  pyttsx3 TTS │
│   + WebRTC   │    │  optional FAQ → LLM response   │    │              │
│      VAD     │    │                                │    │              │
└──────────────┘    └────────────────────────────────┘    └──────────────┘
```

Each iteration of the cycle reads from a `DialogueSession` (state +
conversation history) and writes back to it. State is explicit, not global,
so multiple sessions can run side-by-side and the agent is trivially
testable.

---

## Installation

The package ships with several optional extras so you only install what you
need.

```bash
# Library + template-mode CLI (no audio, no transformers, no LLM)
pip install -e .

# Voice mode (Whisper + sounddevice + WebRTC VAD + pyttsx3)
pip install -e ".[voice]"

# Add NLU (HuggingFace Transformers for zero-shot intent/FAQ)
pip install -e ".[voice,nlu]"

# Development (tests, ruff, mypy, pre-commit)
pip install -e ".[dev]"
```

You can also install a single base set from `requirements.txt`, but `.[…]`
extras are the recommended path.

### Running the LLM

* `--mode local` talks to a local [Ollama](https://ollama.com/) server.
  Install Ollama, run `ollama pull llama3`, then `ollama serve`.
* `--mode api` talks to [OpenRouter](https://openrouter.ai/). Set
  `KGCONVAI_OPENROUTER_API_KEY` in your environment or in a `.env` file.
* `--mode template` (default) skips the LLM and replies from static templates
  — useful for testing and CI.

---

## Quickstart

```bash
# Verify the dialogue graph, FAQ and templates load
kgconvai validate

# Show effective settings
kgconvai info

# Run the agent (template mode, no audio hardware needed for templates)
kgconvai run --mode template

# Run with local Ollama
kgconvai run --mode local

# Run with OpenRouter API
KGCONVAI_OPENROUTER_API_KEY=sk-or-... kgconvai run --mode api
```

`python -m kgconvai ...` works identically.

### Library usage

```python
from kgconvai import Agent, DialogueSession, Settings
from kgconvai.asr.whisper import WhisperASR
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.templates import TemplateStore
from kgconvai.llm.ollama import OllamaLLM
from kgconvai.nlu.classifier import ZeroShotClassifier
from kgconvai.nlu.faq import FAQStore
from kgconvai.tts.pyttsx3_engine import Pyttsx3TTS

settings = Settings()

agent = Agent(
    asr=WhisperASR("base"),
    tts=Pyttsx3TTS(),
    classifier=ZeroShotClassifier(),
    graph=DialogueGraph.from_path("dialogue_graph/conversation_graph.json"),
    faq=FAQStore.from_path("dialogue_graph/faq.json"),
    templates=TemplateStore.from_path("dialogue_graph/templates.json"),
    llm=OllamaLLM(),
    settings=settings,
)

# Voice loop
agent.run()

# Or programmatic single-turn
reply = agent.respond("I want to book a meeting")
```

---

## Project layout

```
src/kgconvai/
├── agent.py            # high-level Agent that drives the TAO cycle
├── cli.py              # typer CLI: run, info, validate, version
├── config.py           # Settings (pydantic-settings)
├── logging.py          # structlog setup
├── state.py            # DialogueSession + Turn (no more globals)
├── asr/                # speech-to-text (Whisper + WebRTC VAD)
├── tts/                # text-to-speech (pyttsx3)
├── llm/                # Ollama + OpenRouter clients (abstract LLMGenerator)
├── nlu/                # classifier + intent + FAQ retrieval
└── dialogue/           # DialogueGraph, DialogueManager, TemplateStore
dialogue_graph/
├── conversation_graph.json
├── faq.json
└── templates.json
tests/
├── unit/               # 30+ unit tests
└── integration/        # end-to-end TAO cycle with mocked backends
```

---

## Development

```bash
# Install dev extras and pre-commit hooks
pip install -e ".[dev]"
pre-commit install

# Lint, format, type-check, test
ruff check src tests
ruff format src tests
mypy
pytest --cov

# Run only the fast unit tests
pytest -m "not integration"
```

CI runs the same pipeline on Python 3.10, 3.11, and 3.12 via GitHub Actions.

---

## Roadmap

* **0.2.0** ✅ — package restructure, tests, CI, config, structured logging.
* **0.3.0** ✅ — RDF/OWL ontology, rdflib backend, Neo4j backend, sentence-transformers FAQ, JSON↔graph sync.
* **0.4.0** ✅ — Gradio chat UI, Streamlit admin panel, Dockerfile + docker-compose, Hugging Face Space.
* **0.5.0** ✅ — Eval harness with labelled datasets running in CI; MkDocs documentation site.


---

## References

1. Yin, M., Roccabruna, G., Azad, A., & Riccardi, G. (2023). *Let's Give a Voice to Conversational Agents in Virtual Reality*. arXiv:2308.02665.
2. Wang, H., Kwan, W.-C., Li, M., Zhou, Z., & Wong, K.-F. (2024). *KddRES: A Multi-level Knowledge-driven Dialogue Dataset for Restaurant*. Computer Speech & Language, 87.
3. Hussain, S., Ameri Sianaki, O., Ababneh, N. (2019). *A Survey on Conversational Agents/Chatbots Classification and Design Techniques*. WAINA 2019.
4. Fang, R., Bowman, D., & Kang, D. (2024). *Voice-Enabled AI Agents can Perform Common Scams*. arXiv:2410.15650.
5. Li, G., et al. (2023). *CAMEL: communicative agents for "mind" exploration of large language model society*. NeurIPS 2023.

---

## License

MIT — see [LICENSE](LICENSE). Built by **Gabriel Henrique Alencar Medeiros**.
