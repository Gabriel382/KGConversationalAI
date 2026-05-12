# ADR 0002: Knowledge-graph abstraction over RDF + Neo4j

**Status:** Accepted &nbsp;·&nbsp; **Date:** 2026-05-12

## Context

The "knowledge" in a phone-assistant agent — dialogue states, intents,
transitions, FAQ entries, business entities — is naturally graph-shaped.
Two ecosystems dominate:

- **RDF / OWL / SPARQL.** Semantic web stack. Mature, standards-based,
  in-process via rdflib.
- **Neo4j / Cypher.** Property-graph stack. Industry-standard, great
  visualisation (Neo4j Browser), but needs a running database.

## Decision

Define a `KnowledgeGraph` abstract interface plus `KGImporter` and
`KGExporter` ABCs. Ship two implementations: `RDFBackend` and `Neo4jBackend`.
Both round-trip the same canonical `KGData` JSON.

## Consequences

**Positive.**

- CI runs entirely against rdflib — no Docker required.
- Demos run against Neo4j and get the visual editor for free.
- Tests parameterise over both backends, so neither can silently drift.

**Negative.**

- Two storage formats to keep in sync. Mitigated by the round-trip property
  test and the canonical JSON between them.
- Each backend has its own query language; the `query()` method just returns
  rows-of-dicts and lets callers pick the dialect.
