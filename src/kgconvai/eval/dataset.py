"""Dataset loaders for the eval harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True, frozen=True)
class IntentExample:
    utterance: str
    expected: str


@dataclass(slots=True)
class IntentDataset:
    version: str
    candidates: list[str]
    examples: list[IntentExample] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.examples)


@dataclass(slots=True, frozen=True)
class FAQExample:
    utterance: str
    intent: str
    expected: str


@dataclass(slots=True)
class FAQDataset:
    version: str
    examples: list[FAQExample] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.examples)


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_intent_dataset(path: str | Path) -> IntentDataset:
    raw = _load_yaml(path)
    return IntentDataset(
        version=str(raw.get("version", "1.0")),
        candidates=list(raw.get("candidates") or []),
        examples=[
            IntentExample(utterance=e["utterance"], expected=e["expected"])
            for e in raw.get("examples") or []
        ],
    )


def load_faq_dataset(path: str | Path) -> FAQDataset:
    raw = _load_yaml(path)
    return FAQDataset(
        version=str(raw.get("version", "1.0")),
        examples=[
            FAQExample(utterance=e["utterance"], intent=e["intent"], expected=e["expected"])
            for e in raw.get("examples") or []
        ],
    )
