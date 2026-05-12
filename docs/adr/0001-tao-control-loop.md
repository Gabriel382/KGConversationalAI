# ADR 0001: Thought-Action-Observation control loop

**Status:** Accepted &nbsp;·&nbsp; **Date:** 2025-04-28

## Context

A voice assistant is, mechanically, a loop: hear → think → speak. Most chatbot
codebases collapse those three concerns into a single `respond(text)` function
and end up with implicit state, ad-hoc logging, and brittle tests.

## Decision

Structure the agent as an explicit **Observation → Thought → Action** cycle.
Each phase has a typed interface (`ASR.listen() -> SpeechResult`,
`DialogueManager.step(session, intent) -> ActionNode`, `TTS.say(text) -> None`)
and mutates state only through an injected `DialogueSession`.

## Consequences

**Positive.**

- Side-effects (audio I/O) are isolated to known modules, so the same agent
  drives the voice loop, a Gradio textbox, or a programmatic
  `agent.respond(text)` call.
- Tests can stub one phase at a time. The integration test exercises a full
  cycle with `FakeASR`, `FakeClassifier`, `FakeLLM`, `RecordingTTS`.
- Structured logging matches the phases (`asr.*`, `nlu.intent_detected`,
  `dialogue.transition`, `response.*`, `tts.*`), so traces tell a story.

**Negative.**

- Three explicit phases is more code than one big function.
- New contributors have to learn the vocabulary.

## Alternatives considered

- A single LLM call doing intent + retrieval + generation. Rejected: opaque,
  expensive per turn, hard to evaluate.
- Rasa-style policy + action server. Rejected: heavy, and the dialogue
  patterns we cover are simple enough that a finite-state graph is fine.
