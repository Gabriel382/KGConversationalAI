"""Response generation: templates and LLM dispatch."""

from __future__ import annotations

import json
from pathlib import Path

from kgconvai.dialogue.graph import ActionNode
from kgconvai.llm.base import LLMGenerator
from kgconvai.logging import get_logger
from kgconvai.state import DialogueSession, Speaker

log = get_logger(__name__)


class TemplateStore:
    """Per-intent instruction templates loaded from JSON."""

    def __init__(self, templates: dict[str, str]) -> None:
        self._templates = templates

    @classmethod
    def from_path(cls, path: str | Path) -> TemplateStore:
        with Path(path).open(encoding="utf-8") as f:
            return cls(json.load(f))

    def instruction_for(self, intent: str) -> str:
        return self._templates.get(intent, "Assist the user politely.")

    def fallback_for(self, intent: str) -> str:
        return self._templates.get(intent, "I'm here to assist you!")


def generate_response(
    session: DialogueSession,
    intent: str,
    action_node: ActionNode,
    knowledge: str | None,
    *,
    templates: TemplateStore,
    llm: LLMGenerator | None = None,
    model: str | None = None,
) -> str:
    """Build a final reply, either via the LLM or by falling back to templates."""

    if llm is None:
        return knowledge or templates.fallback_for(intent)

    instruction = templates.instruction_for(intent)
    knowledge_text = f"Use this information if needed: {knowledge}" if knowledge else ""
    next_state_note = f"Moving to dialogue state '{action_node.next_state}'."

    recent = session.recent(6)

    if llm.chat_format:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful and concise English-speaking voice assistant. "
                    "Always respond briefly and naturally in English. "
                    "Do not use code formatting, document outlines, or markdown."
                ),
            }
        ]
        for turn in recent:
            role = "user" if turn.speaker is Speaker.USER else "assistant"
            messages.append({"role": role, "content": turn.text})
        user_prompt = (
            f"The user would like to {intent.replace('_', ' ')}.\n"
            f"{instruction}\n"
            f"{knowledge_text}\n"
            f"Now give what would be a good assistant reply."
        ).strip()
        messages.append({"role": "user", "content": user_prompt})
        reply = llm.generate(messages, model=model)
    else:
        history_text = "\n".join(
            f"{turn.speaker.value.capitalize()}: {turn.text}" for turn in recent
        )
        prompt = (
            "You are a helpful voice assistant.\n"
            "Always reply in short, natural English sentences.\n"
            f"Intent detected: {intent}\n"
            f"{next_state_note}\n"
            f"{knowledge_text}\n"
            f"Conversation history:\n{history_text}\n"
            "Now continue as the Agent."
        )
        reply = llm.generate(prompt, model=model)

    if not reply.strip():
        log.warning("response.empty_llm_reply")
        return knowledge or templates.fallback_for(intent)
    return reply
