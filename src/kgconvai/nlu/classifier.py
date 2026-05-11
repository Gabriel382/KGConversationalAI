"""Zero-shot classification adapter.

Wraps Hugging Face's ``pipeline("zero-shot-classification", ...)`` behind a
small interface so tests can substitute a deterministic fake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class Classification:
    """A scored label."""

    label: str
    score: float


class Classifier(Protocol):
    """Anything that scores a text against candidate labels."""

    def classify(self, text: str, candidates: list[str]) -> list[Classification]: ...


class ZeroShotClassifier:
    """Transformer-based zero-shot classifier.

    The Transformers pipeline is loaded lazily so callers can construct the
    object without paying the model-load cost in tests.
    """

    def __init__(self, model_name: str = "facebook/bart-large-mnli") -> None:
        self.model_name = model_name
        self._pipeline = None

    def _ensure_pipeline(self):  # pragma: no cover - heavy import
        if self._pipeline is None:
            from transformers import pipeline

            self._pipeline = pipeline("zero-shot-classification", model=self.model_name)
        return self._pipeline

    def classify(self, text: str, candidates: list[str]) -> list[Classification]:
        if not text.strip() or not candidates:
            return []
        pipe = self._ensure_pipeline()
        result = pipe(text, candidates)
        labels = result["labels"]
        scores = result["scores"]
        return [
            Classification(label=lab, score=float(sc))
            for lab, sc in zip(labels, scores, strict=False)
        ]
