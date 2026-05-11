"""Dialogue graph: states, transitions, and helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ActionNode:
    """Outcome of one dialogue transition."""

    next_state: str
    requires_kb: bool = False


class DialogueGraph:
    """A finite-state dialogue graph loaded from JSON.

    The JSON shape is::

        {
          "state_a": {"intent_x": "state_b", "intent_y": "state_c"},
          "state_b": {...},
          ...
          "end": {}
        }
    """

    KB_STATES: frozenset[str] = frozenset({"provide_information"})

    def __init__(self, transitions: dict[str, dict[str, str]]) -> None:
        if "start" not in transitions:
            raise ValueError("Dialogue graph must contain a 'start' state.")
        self._transitions = transitions

    @classmethod
    def from_path(cls, path: str | Path) -> DialogueGraph:
        with Path(path).open(encoding="utf-8") as f:
            return cls(json.load(f))

    def states(self) -> list[str]:
        return list(self._transitions.keys())

    def candidate_intents(self) -> list[str]:
        """All intent labels that appear anywhere as a transition trigger."""
        labels: set[str] = set()
        for outgoing in self._transitions.values():
            labels.update(outgoing.keys())
        return sorted(labels)

    def transition(self, current_state: str, intent: str) -> ActionNode:
        """Resolve the next state, falling back to staying if no match."""
        outgoing = self._transitions.get(current_state, {})
        next_state = outgoing.get(intent, current_state)
        return ActionNode(
            next_state=next_state,
            requires_kb=next_state in self.KB_STATES,
        )
