"""Intent detection."""

from __future__ import annotations

from kgconvai.logging import get_logger
from kgconvai.nlu.classifier import Classifier

log = get_logger(__name__)


def detect_intent(
    user_text: str,
    classifier: Classifier,
    candidate_labels: list[str],
    *,
    unknown_label: str = "unknown",
) -> str:
    """Return the highest-scoring intent label, or ``unknown_label`` on empty input."""
    if not user_text.strip():
        return unknown_label
    results = classifier.classify(user_text, candidate_labels)
    if not results:
        return unknown_label
    top = results[0]
    log.info("nlu.intent_detected", intent=top.label, score=top.score)
    return top.label
