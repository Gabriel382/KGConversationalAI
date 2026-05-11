"""FAQ knowledge base + retrieval."""

from __future__ import annotations

import json
from pathlib import Path

from kgconvai.logging import get_logger
from kgconvai.nlu.classifier import Classifier

log = get_logger(__name__)


class FAQStore:
    """Loads and queries the FAQ knowledge base."""

    def __init__(self, data: dict[str, dict[str, str]]) -> None:
        self._data = data

    @classmethod
    def from_path(cls, path: str | Path) -> FAQStore:
        with Path(path).open(encoding="utf-8") as f:
            return cls(json.load(f))

    def intents(self) -> list[str]:
        return list(self._data.keys())

    def questions(self, intent: str) -> list[str]:
        return list(self._data.get(intent, {}).keys())

    def answer(self, intent: str, question: str) -> str | None:
        return self._data.get(intent, {}).get(question)


def retrieve_answer(
    user_text: str,
    intent: str,
    faq: FAQStore,
    classifier: Classifier,
    *,
    confidence_threshold: float = 0.4,
) -> str:
    """Return the best matching FAQ answer for the user's text under ``intent``."""
    if not user_text.strip():
        return "I'm sorry, I didn't catch that. Could you please repeat?"

    questions = faq.questions(intent)
    if not questions:
        log.info("nlu.faq.no_entries", intent=intent)
        return "I'm not sure about that topic."

    results = classifier.classify(user_text, questions)
    if not results:
        return "I'm having trouble understanding your question right now."

    best = results[0]
    log.info(
        "nlu.faq_matched",
        intent=intent,
        question=best.label,
        score=best.score,
    )
    if best.score < confidence_threshold:
        return "I'm not fully sure, but I will try to help."

    answer = faq.answer(intent, best.label)
    return answer or "I'm sorry, I don't have information about that yet."
