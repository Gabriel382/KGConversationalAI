"""Session state.

The previous implementation kept ``current_state`` as a module-level global
inside ``thought/dialogue_manager.py``, which made the agent impossible to run
in more than one conversation at once and impossible to unit-test in
isolation. :class:`DialogueSession` replaces that global with an explicit,
constructor-injected object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Speaker(str, Enum):
    """Who produced a given conversational turn."""

    USER = "user"
    AGENT = "agent"


@dataclass(slots=True)
class Turn:
    """A single utterance in the conversation history."""

    speaker: Speaker
    text: str


@dataclass(slots=True)
class DialogueSession:
    """Mutable state for one conversation.

    Attributes:
        current_state: The current node of the dialogue graph.
        history: Ordered list of turns. Newest turn is last.
    """

    current_state: str = "start"
    history: list[Turn] = field(default_factory=list)

    def add_user_turn(self, text: str) -> None:
        self.history.append(Turn(Speaker.USER, text))

    def add_agent_turn(self, text: str) -> None:
        self.history.append(Turn(Speaker.AGENT, text))

    def recent(self, n: int = 6) -> list[Turn]:
        """Return the last ``n`` turns (oldest first)."""
        return self.history[-n:]

    def is_finished(self) -> bool:
        return self.current_state == "end"
