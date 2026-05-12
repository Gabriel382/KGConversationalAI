# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-11

### Added
- Restructured as a proper Python package (`src/kgconvai/`) with subpackages
  for `asr/`, `tts/`, `llm/`, `nlu/`, `dialogue/`.
- `pyproject.toml` with `hatchling` build backend and optional extras
  (`[voice]`, `[nlu]`, `[api]`, `[dev]`).
- New `kgconvai` CLI (built with `typer`) exposing `run`, `info`, `validate`,
  and `version` subcommands.
- `Settings` class using `pydantic-settings` for env/file-based configuration.
- Structured logging via `structlog` (console and JSON formats).
- `DialogueSession` and `Turn` types replacing the previous module-level
  global state in `dialogue_manager`.
- `Agent` class orchestrating the TAO cycle, with both `agent.run()` (voice)
  and `agent.respond(text)` (programmatic) entry points.
- 38 unit + integration tests in `tests/`, including a regression test for
  the conversation-history corruption bug.
- GitHub Actions CI: ruff, mypy, pytest on Python 3.10/3.11/3.12.
- `.pre-commit-config.yaml` with ruff, mypy, and basic file checks.

### Changed
- FAQ retrieval, intent detection, response generation, and dialogue
  transitions now take their collaborators (classifier, FAQ store, templates)
  as constructor arguments instead of relying on module-level state. This
  enables clean unit testing and lets the agent serve multiple sessions.
- Whisper, sounddevice, webrtcvad, pyttsx3, and Transformers are imported
  lazily so `import kgconvai` works in headless environments.

### Fixed
- Conversation history was corrupted by mixing bare strings and tuples
  (`history += [response_text]` then `history.append(("Agent", ...))`), which
  caused a runtime `ValueError` when the response generator unpacked
  `for speaker, text in history`. History is now strongly typed (`list[Turn]`).
- `current_state` was a module-level global, preventing concurrent sessions.
  Each conversation now gets its own `DialogueSession` instance.

### Removed
- The old top-level `observation/`, `action/`, `thought/`, `services/`, and
  `utils/` packages have been replaced by `src/kgconvai/*`. The original
  `main.py` entry point is superseded by the `kgconvai` CLI / `python -m kgconvai`.

## [0.1.0] - 2025-05-02

Initial public version. See git history for details.

## [0.3.0] - 2026-05-12

### Added
- **Knowledge-graph layer** (`src/kgconvai/kg/`)
  - `KGData` Pydantic models matching the canonical JSON schema at
    `schemas/kgconvai.schema.json`.
  - Abstract `KnowledgeGraph`, `KGImporter`, `KGExporter`, `KGBackend`
    interfaces.
  - `RDFBackend` (rdflib): in-process, zero-install, used in CI. Round-trips
    canonical JSON via RDF triples. Supports SPARQL queries.
  - `Neo4jBackend`: property-graph backend behind the same interface.
    Round-trips JSON via Cypher. Auto-skipped in CI when no Neo4j is
    reachable; full docker-compose setup at `docker/docker-compose.yml`.
- **RDF/OWL ontology** in `ontology/`:
  - `core.ttl` — generic vocabulary (`DialogueState`, `Intent`, `Transition`,
    `FAQEntry`, `ResponseTemplate`).
  - `examples/phone_call.ttl` — domain-specific extension (`Caller`,
    `Service`, `Appointment`, `BusinessHours`).
- **Canonical JSON Schema** (`schemas/kgconvai.schema.json`) validated on
  import via `jsonschema`.
- **Embedding-based FAQ retrieval** (`src/kgconvai/nlu/embeddings.py`).
  `EmbeddingRetriever` implements the `Classifier` protocol and is a drop-in
  replacement for `ZeroShotClassifier`. Caches candidate vectors.
- **CLI**: new `kgconvai kg` subcommand group with `validate`, `export`
  (round-trips through the chosen backend), `diff`.
- **Migration script** `scripts/migrate_legacy_data.py` and the resulting
  `dialogue_graph/kg.json` in the new canonical format.
- 19 new tests covering schema validation, RDF round-trip, Neo4j round-trip
  (skipped without server), embedding retriever, and canonical/legacy
  loader autodetection.

### Changed
- `DialogueGraph.from_path`, `FAQStore.from_path`, and `TemplateStore.from_path`
  now auto-detect the format and load the new canonical `kg.json`.
- `KGData.to_json` emits canonicalised output (sections sorted by stable
  key) for byte-identical round-trips across backends.

## [0.4.0] - 2026-05-12

### Added
- **Gradio chat UI** (`src/kgconvai/web/chat.py`).
  Per-session conversation state via `gr.State`. Wraps `Agent.respond()`.
- **Streamlit admin panel** (`src/kgconvai/web/admin.py`).
  Visual PyVis graph of the dialogue states; editable tables for states,
  intents, transitions, FAQ, templates. Validates against the canonical
  schema before saving.
- **CLI**: `kgconvai web chat`, `kgconvai web admin`.
- **Dockerfile** (multi-stage, ~250 MB) + extended `docker-compose.yml`
  (chat + admin + Neo4j on one `docker compose up`).
- **Hugging Face Space** scaffolding in `huggingface/` (app.py, requirements,
  README with Space metadata).
- 7 new tests covering Gradio Blocks construction, Streamlit admin helpers,
  PyVis graph rendering, and HF Space metadata.

### Changed
- New `[web]` optional extra in `pyproject.toml` for the browser deps.
- Dev extras now include gradio/streamlit/pyvis so CI exercises the web modules.

## [0.5.0] - 2026-05-12

### Added
- **Evaluation harness** (`src/kgconvai/eval/`)
  - Typed datasets: `IntentDataset`, `FAQDataset`, `IntentExample`, `FAQExample`.
  - Runners with metrics: accuracy / P@1, P@3, mean reciprocal rank,
    latency p50/p95/mean.
  - Per-example outcomes captured (utterance, expected, top1, ranking),
    serialisable to JSON.
  - `rich`-formatted summary tables.
- **CLI**: `kgconvai eval intents` and `kgconvai eval faq` with
  `--classifier substring|embedding|zero_shot`, `--threshold`, `--json-out`.
- **Labelled datasets** in `eval/`:
  - `intents.yaml`: 44 utterances across 7 intent classes.
  - `faq.yaml`: 18 paraphrased questions over 9 FAQ entries.
- **GitHub Actions** `.github/workflows/eval.yml` — runs the eval on every
  PR, uploads the metrics JSON, posts a comment with the table, and fails
  the run if accuracy drops below threshold.
- **MkDocs site** with `mkdocs-material` theme: home, quickstart,
  installation, architecture (with Mermaid diagram), KG overview/schema/
  backends, web interfaces, evaluation, plus 4 Architecture Decision
  Records (TAO, KG abstraction, canonical JSON, embeddings vs NLI).
- **GitHub Actions** `.github/workflows/docs.yml` — builds and deploys the
  docs to GitHub Pages on push to main.
- 13 new tests covering eval metrics, dataset loaders, and the runner.

### Changed
- `pyyaml` is now a base dependency (used by the eval-dataset loaders).
- `[docs]` optional extra: `mkdocs-material` + `pymdown-extensions`.
