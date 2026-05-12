# KGConvAI

**A modular, graph-driven voice agent following the Thought-Action-Observation cycle.**

[![CI](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/ci.yml)
[![Eval](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/eval.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/eval.yml)
[![Docs](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/docs.yml/badge.svg)](https://github.com/Gabriel382/KGConversationalAI/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Gabriel382/KGConversationalAI/blob/main/LICENSE)

KGConvAI is a conversational agent that lives over a **knowledge graph**:
dialogue states, intents, transitions, FAQ entries and templates are all
represented as a single canonical structure. That graph can run in-process
(rdflib) or in a real graph database (Neo4j), and can be edited either as
JSON (versioned in git) or visually (Neo4j Browser, or the bundled Streamlit
admin panel).

## What you can do with it

- Hold a real-time voice conversation (Whisper STT → agent → pyttsx3 TTS).
- Or text chat in the browser via the Gradio UI.
- Or use it as a library: `from kgconvai import Agent; agent.respond(text)`.
- Author the dialogue graph in JSON, or visually in the Streamlit admin panel.
- Run it locally with Ollama, or against a hosted OpenRouter model.
- Reload from disk with no downtime — the agent is stateless above its
  per-session `DialogueSession`.

## Why it's interesting

A "real" conversational AI system needs four kinds of structure that most
hobby projects collapse into ad-hoc dicts:

1. A **state machine** (where am I in the conversation?).
2. A **knowledge graph** (what do I know that I might need to look up?).
3. A **slot/template language** (what do I tell the user?).
4. A **session model** (who am I talking to right now?).

KGConvAI treats each as a first-class concern with its own module, tested in
isolation, swappable behind an interface. The `KnowledgeGraph` abstraction
lets you run the same agent over either an RDF triple store or a Neo4j
property graph, and round-trip the data back to canonical JSON.

## Getting started

- [Quickstart](quickstart.md) — install, run the chat UI in 5 minutes.
- [Architecture](architecture.md) — high-level diagram and module map.
- [Knowledge graph](kg/overview.md) — the ontology, the schema, the backends.
- [Evaluation](evaluation.md) — how the harness scores intents and FAQ retrieval.
- [ADRs](adr/index.md) — the reasoning behind the design choices.
