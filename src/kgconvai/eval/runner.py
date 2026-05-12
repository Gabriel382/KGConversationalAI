"""Eval runner + metrics."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from kgconvai.eval.dataset import FAQDataset, IntentDataset
from kgconvai.nlu.classifier import Classification, Classifier

# ---------- Metric primitives ------------------------------------------------


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def _accuracy(top1: list[bool]) -> float:
    return sum(top1) / len(top1) if top1 else 0.0


def _precision_at_k(top_k_correct: list[bool]) -> float:
    return sum(top_k_correct) / len(top_k_correct) if top_k_correct else 0.0


def _reciprocal_rank(ranking: list[Classification], expected: str) -> float:
    for idx, c in enumerate(ranking, start=1):
        if c.label == expected:
            return 1.0 / idx
    return 0.0


@dataclass(slots=True)
class Metrics:
    """Standard retrieval/classification metrics."""

    n: int = 0
    accuracy: float = 0.0  # = P@1
    p_at_1: float = 0.0
    p_at_3: float = 0.0
    mrr: float = 0.0
    latency_ms_p50: float = 0.0
    latency_ms_p95: float = 0.0
    latency_ms_mean: float = 0.0


@dataclass(slots=True)
class PerExample:
    utterance: str
    expected: str
    top1: str
    correct: bool
    score: float
    latency_ms: float
    ranking: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RunReport:
    """A full eval run: name, dataset size, metrics, per-example outcomes."""

    name: str
    classifier: str
    dataset_version: str
    metrics: Metrics
    examples: list[PerExample] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "classifier": self.classifier,
            "dataset_version": self.dataset_version,
            "metrics": asdict(self.metrics),
            "examples": [asdict(e) for e in self.examples],
        }

    def to_json(self, path: str | Path | None = None) -> str:
        text = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        if path is not None:
            Path(path).write_text(text + "\n", encoding="utf-8")
        return text


# ---------- Runners ----------------------------------------------------------


def run_intent_eval(
    dataset: IntentDataset,
    classifier: Classifier,
    *,
    classifier_name: str = "unknown",
) -> RunReport:
    top1, top3, rr, lat = [], [], [], []
    examples: list[PerExample] = []
    for ex in dataset.examples:
        t0 = time.perf_counter()
        ranking = classifier.classify(ex.utterance, dataset.candidates)
        latency_ms = (time.perf_counter() - t0) * 1000

        labels = [c.label for c in ranking]
        is_top1 = bool(ranking) and ranking[0].label == ex.expected
        is_top3 = ex.expected in labels[:3]
        top1.append(is_top1)
        top3.append(is_top3)
        rr.append(_reciprocal_rank(ranking, ex.expected))
        lat.append(latency_ms)
        examples.append(
            PerExample(
                utterance=ex.utterance,
                expected=ex.expected,
                top1=ranking[0].label if ranking else "<empty>",
                correct=is_top1,
                score=ranking[0].score if ranking else 0.0,
                latency_ms=latency_ms,
                ranking=labels[:5],
            )
        )

    metrics = Metrics(
        n=len(dataset),
        accuracy=_accuracy(top1),
        p_at_1=_precision_at_k(top1),
        p_at_3=_precision_at_k(top3),
        mrr=sum(rr) / len(rr) if rr else 0.0,
        latency_ms_p50=_percentile(lat, 0.50),
        latency_ms_p95=_percentile(lat, 0.95),
        latency_ms_mean=sum(lat) / len(lat) if lat else 0.0,
    )
    return RunReport(
        name="intents",
        classifier=classifier_name,
        dataset_version=dataset.version,
        metrics=metrics,
        examples=examples,
    )


def run_faq_eval(
    dataset: FAQDataset,
    classifier: Classifier,
    candidates_by_intent: dict[str, list[str]],
    *,
    classifier_name: str = "unknown",
) -> RunReport:
    top1, top3, rr, lat = [], [], [], []
    examples: list[PerExample] = []
    for ex in dataset.examples:
        candidates = candidates_by_intent.get(ex.intent, [])
        t0 = time.perf_counter()
        ranking = classifier.classify(ex.utterance, candidates)
        latency_ms = (time.perf_counter() - t0) * 1000

        labels = [c.label for c in ranking]
        is_top1 = bool(ranking) and ranking[0].label == ex.expected
        is_top3 = ex.expected in labels[:3]
        top1.append(is_top1)
        top3.append(is_top3)
        rr.append(_reciprocal_rank(ranking, ex.expected))
        lat.append(latency_ms)
        examples.append(
            PerExample(
                utterance=ex.utterance,
                expected=ex.expected,
                top1=ranking[0].label if ranking else "<empty>",
                correct=is_top1,
                score=ranking[0].score if ranking else 0.0,
                latency_ms=latency_ms,
                ranking=labels[:5],
            )
        )

    metrics = Metrics(
        n=len(dataset),
        accuracy=_accuracy(top1),
        p_at_1=_precision_at_k(top1),
        p_at_3=_precision_at_k(top3),
        mrr=sum(rr) / len(rr) if rr else 0.0,
        latency_ms_p50=_percentile(lat, 0.50),
        latency_ms_p95=_percentile(lat, 0.95),
        latency_ms_mean=sum(lat) / len(lat) if lat else 0.0,
    )
    return RunReport(
        name="faq",
        classifier=classifier_name,
        dataset_version=dataset.version,
        metrics=metrics,
        examples=examples,
    )


# ---------- Pretty formatting -----------------------------------------------


def format_report(report: RunReport, *, show_examples: bool = True) -> str:
    """Render a RunReport as a multi-section rich.Table string."""
    import io

    from rich.console import Console
    from rich.table import Table

    sink = io.StringIO()
    buf = Console(record=True, file=sink, width=120)

    summary = Table(title=f"{report.name} eval — {report.classifier}", show_header=False)
    summary.add_column("Metric", style="bold")
    summary.add_column("Value")
    m = report.metrics
    summary.add_row("N", str(m.n))
    summary.add_row("Accuracy / P@1", f"{m.accuracy * 100:.1f}%")
    summary.add_row("P@3", f"{m.p_at_3 * 100:.1f}%")
    summary.add_row("MRR", f"{m.mrr:.3f}")
    summary.add_row(
        "Latency p50 / p95 / mean (ms)",
        f"{m.latency_ms_p50:.1f} / {m.latency_ms_p95:.1f} / {m.latency_ms_mean:.1f}",
    )
    buf.print(summary)

    if show_examples and report.examples:
        ex = Table(title="Per-example outcomes", show_header=True, show_lines=False)
        ex.add_column("OK")
        ex.add_column("utterance", overflow="fold")
        ex.add_column("expected")
        ex.add_column("got")
        ex.add_column("score")
        for e in report.examples:
            ex.add_row(
                "[green]✓[/]" if e.correct else "[red]✗[/]",
                e.utterance[:60],
                e.expected,
                e.top1,
                f"{e.score:.2f}",
            )
        buf.print(ex)

    return buf.export_text()
