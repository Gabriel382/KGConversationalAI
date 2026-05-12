# Evaluation

The agent ships with a labelled-test-set harness so we can answer the
question "is my new classifier actually better?" with a number, not a vibe.

## Test sets

- `eval/intents.yaml` — 44 hand-labelled utterances across all 7 intents
  (including utter-nonsense for the `unknown` class).
- `eval/faq.yaml` — 18 paraphrased questions over the 9 FAQ entries.

Both files are checked into git. They are intentionally small — the goal is
fast CI runs, not benchmark dominance.

## Metrics

For each labelled example:

- **P@1 / Accuracy** — top-1 match.
- **P@3** — expected label in top-3 predictions.
- **MRR** — mean reciprocal rank.
- **Latency p50 / p95 / mean** — wall-clock per `classifier.classify()` call.

## Running locally

```bash
kgconvai eval intents --classifier substring --no-show-examples
kgconvai eval faq     --classifier substring --no-show-examples
```

Use `--classifier embedding` to evaluate `sentence-transformers/all-MiniLM-L6-v2`
or `--classifier zero_shot` for `facebook/bart-large-mnli`.

## Running in CI

`.github/workflows/eval.yml` runs on every pull request, posts a comment with
the metrics, and **fails the run if accuracy drops below the configured
threshold**. The threshold is set on the CLI invocation — currently 0.40 for
intents and 0.50 for FAQ with the cheap substring baseline. Raise it as the
classifier improves.

## Why this matters

Most chatbot projects ship with no metrics. Adding even a small labelled
test set means you can say things in interviews like "swapping BART-MNLI for
MiniLM embeddings improved FAQ P@1 from 72% to 91% and reduced latency 8x" —
which is the kind of sentence that gets you hired.
