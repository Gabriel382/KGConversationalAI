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
        (e.g. a chat UI).
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
        response = generate_response(
            session,
            intent,
            action_node,
            knowledge,
            templates=self.templates,
            llm=self.llm,
        )
        session.add_agent_turn(response)
        return response

    def run(self) -> None:
        """Loop until the conversation reaches the 'end' state."""
        session = DialogueSession()
        log.info("agent.run.start", candidate_labels=self.candidate_labels)
        while not session.is_finished():
            result = self.step(session)
            log.info("agent.cycle", **vars(result))
        log.info("agent.run.end")
