# ADR 0003: Canonical JSON is the source of truth

**Status:** Accepted &nbsp;·&nbsp; **Date:** 2026-05-12

## Context

The KG lives in two physical homes: a JSON file in git, and (sometimes) a
Neo4j database. Either could be "the truth", but only one can be at a time
or you get drift.

## Decision

JSON is canonical. Backends are views. `KGData.to_json` produces
**byte-identical** output regardless of which backend it came from
(lists are sorted by a stable key; dict keys are sorted). The schema in
`schemas/kgconvai.schema.json` is enforced on every `KGData.from_json` call.

## Consequences

**Positive.**

- Reviewable diffs in pull requests.
- The Streamlit admin panel reloads from disk after every save — no stale
  in-memory cache, no Cypher script to write.
- Round-trips are testable: `from_json → import → export` must equal the
  input.

**Negative.**

- Large dialogue graphs in JSON eventually get unwieldy. The Streamlit admin
  panel mitigates this for non-developers; very large graphs would warrant a
  proper editor down the road.
