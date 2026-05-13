"""High-level Agent orchestrating the TAO cycle."""

from __future__ import annotations

from dataclasses import dataclass

from kgconvai.asr.base import ASR
from kgconvai.config import Settings
from kgconvai.dialogue.graph import DialogueGraph
from kgconvai.dialogue.manager import DialogueManager
from kgconvai.dialogue.templates import TemplateStore, generate_response
from kgconvai.llm.base import LLMGenerator
from kgconvai.logging import get_logger
from kgconvai.nlu.classifier import Classifier
from kgconvai.nlu.faq import FAQStore, retrieve_answer
from kgconvai.nlu.intent import detect_intent
from kgconvai.state import DialogueSession
from kgconvai.tts.base import TTS

log = get_logger(__name__)


@dataclass(slots=True)
class CycleResult:
    """One iteration of the TAO loop."""

    user_text: str
    intent: str
    next_state: str
    knowledge: str | None
    response: str


class Agent:
    """Wires the TAO cycle: Observation -> Thought -> Action."""

    def __init__(
        self,
        *,
        asr: ASR,
        tts: TTS,
        classifier: Classifier,
        graph: DialogueGraph,
        faq: FAQStore,
        templates: TemplateStore,
        llm: LLMGenerator | None,
        settings: Settings,
    ) -> None:
        self.asr = asr
        self.tts = tts
        self.classifier = classifier
        self.dialogue = DialogueManager(graph)
        self.faq = faq
        self.templates = templates
        self.llm = llm
        self.settings = settings
        self.candidate_labels = graph.candidate_intents()

    def step(self, session: DialogueSession) -> CycleResult:
        """Run a single Observation -> Thought -> Action cycle."""
        # --- OBSERVATION -----------------------------------------------------
        speech = self.asr.listen()
        session.add_user_turn(speech.text)

        # --- THOUGHT ---------------------------------------------------------
        intent = detect_intent(speech.text, self.classifier, self.candidate_labels)
        action_node = self.dialogue.step(session, intent)
        knowledge: str | None = None
        if action_node.requires_kb:
            knowledge = retrieve_answer(
                speech.text,
                intent,
                self.faq,
                self.classifier,
                confidence_threshold=self.settings.faq_confidence_threshold,
            )

        response = generate_response(
            session,
            intent,
            action_node,
            knowledge,
            templates=self.templates,
            llm=self.llm,
        )
        session.add_agent_turn(response)

        # --- ACTION ----------------------------------------------------------
        self.tts.say(response)

        return CycleResult(
            user_text=speech.text,
            intent=intent,
            next_state=action_node.next_state,
            knowledge=knowledge,
            response=response,
        )

    def respond(self, user_text: str, session: DialogueSession | None = None) -> str:
        """Programmatic single-turn: skip ASR/TTS, return the reply string.

        Useful in tests and when embedding the agent in another application
        (e.g. a chat UI). Convenience wrapper around :meth:`respond_with_trace`.
        """
        _, trace = self.respond_with_trace(user_text, session)
        return trace.response

    def respond_with_trace(
        self,
        user_text: str,
        session: DialogueSession | None = None,
        *,
        llm_override: LLMGenerator | None = None,
    ) -> tuple[DialogueSession, CycleResult]:
        """Single programmatic turn that returns the full :class:`CycleResult`.

        This is the entry point used by the Gradio chat UI so it can show
        the user the intent, state transition, and source of the reply.

        Args:
            user_text: Raw user utterance.
            session: Conversation state. A fresh ``DialogueSession`` is
                created if ``None``.
            llm_override: Temporarily use this LLM for this single turn
                instead of ``self.llm`` (e.g. when a visitor pastes their
                own API key in the web UI). The override is not persisted.

        Returns:
            ``(session, CycleResult)`` -- the mutated session and the trace.
        """
        if session is None:
            session = DialogueSession()
        session.add_user_turn(user_text)
        intent = detect_intent(user_text, self.classifier, self.candidate_labels)
        action_node = self.dialogue.step(session, intent)
        knowledge: str | None = None
        if action_node.requires_kb:
            knowledge = retrieve_answer(
                user_text,
                intent,
                self.faq,
                self.classifier,
                confidence_threshold=self.settings.faq_confidence_threshold,
            )
        llm_for_call = llm_override if llm_override is not None else self.llm
        response = generate_response(
            session,
            intent,
            action_node,
            knowledge,
            templates=self.templates,
            llm=llm_for_call,
        )
        session.add_agent_turn(response)
        return session, CycleResult(
            user_text=user_text,
            intent=intent,
            next_state=action_node.next_state,
            knowledge=knowledge,
            response=response,
        )

    def run(self) -> None:
        """Loop until the conversation reaches the 'end' state."""
        session = DialogueSession()
        log.info("agent.run.start", candidate_labels=self.candidate_labels)
        while not session.is_finished():
            result = self.step(session)
            log.info("agent.cycle", **vars(result))
        log.info("agent.run.end")
