"""Stateful wrapper that drives a ``DialogueGraph`` over a ``DialogueSession``."""

from __future__ import annotations

from kgconvai.dialogue.graph import ActionNode, DialogueGraph
from kgconvai.logging import get_logger
from kgconvai.state import DialogueSession

log = get_logger(__name__)


class DialogueManager:
    """Owns the dialogue graph; mutates a session by computing transitions."""

    def __init__(self, graph: DialogueGraph) -> None:
        self.graph = graph

    def step(self, session: DialogueSession, intent: str) -> ActionNode:
        """Compute the next action for ``intent`` and update ``session``."""
        if session.current_state not in self.graph.states():
            log.warning(
                "dialogue.unknown_state",
                state=session.current_state,
                fallback="start",
            )
            session.current_state = "start"

        node = self.graph.transition(session.current_state, intent)
        log.info(
            "dialogue.transition",
            from_state=session.current_state,
            intent=intent,
            to_state=node.next_state,
            requires_kb=node.requires_kb,
        )
        session.current_state = node.next_state
        return node
