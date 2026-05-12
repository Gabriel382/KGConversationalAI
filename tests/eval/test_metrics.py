"""Unit tests for the eval-harness metrics primitives."""

from __future__ import annotations

import math

from kgconvai.eval.runner import (
    Metrics,
    _accuracy,
    _percentile,
    _precision_at_k,
    _reciprocal_rank,
)
from kgconvai.nlu.classifier import Classification


def test_accuracy_simple():
    assert _accuracy([True, True, False, True]) == 0.75
    assert _accuracy([]) == 0.0


def test_precision_at_k_is_just_accuracy_over_bools():
    assert _precision_at_k([True, False, True]) == 2 / 3


def test_reciprocal_rank_finds_match():
    ranking = [
        Classification("a", 0.9),
        Classification("b", 0.7),
        Classification("c", 0.4),
    ]
    assert _reciprocal_rank(ranking, "a") == 1.0
    assert _reciprocal_rank(ranking, "b") == 0.5
    assert _reciprocal_rank(ranking, "c") == 1 / 3
    assert _reciprocal_rank(ranking, "missing") == 0.0


def test_percentile_basics():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert math.isclose(_percentile(xs, 0.5), 3.0)
    assert math.isclose(_percentile(xs, 0.95), 4.8, rel_tol=1e-9)
    assert _percentile([], 0.5) == 0.0


def test_metrics_default_values():
    m = Metrics()
    assert m.n == 0
    assert m.accuracy == 0.0
    assert m.mrr == 0.0
