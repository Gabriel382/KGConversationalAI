"""Dataset loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from kgconvai.eval import load_faq_dataset, load_intent_dataset

ROOT = Path(__file__).resolve().parents[2]


def test_intents_dataset_loads():
    ds = load_intent_dataset(ROOT / "eval" / "intents.yaml")
    assert len(ds) > 0
    assert "greet" in ds.candidates
    assert all(ex.expected in [*ds.candidates, "unknown"] for ex in ds.examples)


def test_faq_dataset_loads():
    ds = load_faq_dataset(ROOT / "eval" / "faq.yaml")
    assert len(ds) > 0
    for ex in ds.examples:
        assert ex.expected.startswith(f"{ex.intent}__")


def test_dataset_round_trip_with_yaml(tmp_path):
    import yaml

    payload = {
        "dataset": "intents",
        "version": "1.0",
        "candidates": ["a", "b"],
        "examples": [
            {"utterance": "hi", "expected": "a"},
            {"utterance": "bye", "expected": "b"},
        ],
    }
    p = tmp_path / "intents.yaml"
    p.write_text(yaml.safe_dump(payload), encoding="utf-8")
    ds = load_intent_dataset(p)
    assert ds.version == "1.0"
    assert len(ds) == 2
    assert ds.candidates == ["a", "b"]


def test_missing_dataset_raises(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        load_intent_dataset(missing)
