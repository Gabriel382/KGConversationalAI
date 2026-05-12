# ADR 0004: Use sentence-transformer embeddings for FAQ retrieval (not zero-shot NLI)

**Status:** Accepted &nbsp;·&nbsp; **Date:** 2026-05-12

## Context

The original codebase used `facebook/bart-large-mnli` (1.6 GB) via
zero-shot classification for both intent detection **and** FAQ retrieval.
Zero-shot NLI is the right tool for "given this hypothesis, does the
premise entail it?" — but FAQ matching is a **semantic similarity**
problem, which a sentence-transformer is trained to solve directly.

## Decision

Introduce an `EmbeddingRetriever` implementing the `Classifier` protocol,
backed by `sentence-transformers/all-MiniLM-L6-v2` (80 MB). It's a drop-in
replacement for `ZeroShotClassifier` for retrieval-style tasks. Keep BART-MNLI
available as one of three classifiers selectable on the CLI, so eval
comparisons remain reproducible.

## Consequences

**Positive.**

- ~10× smaller model.
- Faster inference (no per-pair forward pass; vectorise candidates once and
  cosine-compare).
- Candidate-vector cache keeps subsequent calls O(1).

**Negative.**

- One more dependency in the `[embeddings]` extra.
- Cold-start cost on first use (the model downloads ~80 MB once).

## Verified

The eval harness compares all three classifiers on the same labelled set,
so the choice is reproducible rather than asserted.
