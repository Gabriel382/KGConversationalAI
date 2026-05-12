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
        """Load from JSON. Accepts either the legacy nested format or the
        canonical KGData JSON (autodetected by a ``transitions`` array)."""
        with Path(path).open(encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "transitions" in raw and isinstance(raw["transitions"], list):
            return cls.from_kg_json(raw)
        return cls(raw)

    @classmethod
    def from_kg_json(cls, kg: dict) -> DialogueGraph:
        transitions: dict[str, dict[str, str]] = {}
        for t in kg.get("transitions", []):
            transitions.setdefault(t["from"], {})[t["intent"]] = t["to"]
        for s in kg.get("states", []):
            transitions.setdefault(s["id"], {})
        kb_states = frozenset(s["id"] for s in kg.get("states", []) if s.get("requires_knowledge"))
        graph = cls(transitions)
        if kb_states:
            graph._kb_states = kb_states  # type: ignore[attr-defined]
        return graph

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
        kb_states = getattr(self, "_kb_states", self.KB_STATES)
        return ActionNode(
            next_state=next_state,
            requires_kb=next_state in kb_states,
        )
