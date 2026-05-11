from kgconvai.dialogue.graph import ActionNode
from kgconvai.dialogue.templates import generate_response
from kgconvai.state import DialogueSession
from tests.conftest import FakeLLM


def test_response_generator_falls_back_to_templates_without_llm(sample_templates):
    session = DialogueSession()
    node = ActionNode(next_state="ask_information")
    out = generate_response(
        session, "greet", node, knowledge=None, templates=sample_templates, llm=None
    )
    assert out == "Say hello."


def test_response_generator_uses_knowledge_if_no_llm(sample_templates):
    session = DialogueSession()
    node = ActionNode(next_state="provide_information", requires_kb=True)
    out = generate_response(
        session,
        "ask_information",
        node,
        knowledge="We are open 9 to 6.",
        templates=sample_templates,
        llm=None,
    )
    assert "9 to 6" in out


def test_response_generator_prompt_format_llm(sample_templates):
    session = DialogueSession()
    session.add_user_turn("Hello")
    node = ActionNode(next_state="ask_information")
    llm = FakeLLM(reply="hi there", chat_format=False)
    out = generate_response(
        session, "greet", node, knowledge=None, templates=sample_templates, llm=llm
    )
    assert out == "hi there"
    # Prompt should be a single string
    assert isinstance(llm.calls[0], str)
    assert "Intent detected: greet" in llm.calls[0]


def test_response_generator_chat_format_llm(sample_templates):
    session = DialogueSession()
    session.add_user_turn("Hello")
    node = ActionNode(next_state="ask_information")
    llm = FakeLLM(reply="hello!", chat_format=True)
    out = generate_response(
        session, "greet", node, knowledge=None, templates=sample_templates, llm=llm
    )
    assert out == "hello!"
    # Messages should be a list of dicts with roles
    msgs = llm.calls[0]
    assert isinstance(msgs, list)
    assert msgs[0]["role"] == "system"
    # User's prior turn should be present
    assert any(m.get("content") == "Hello" for m in msgs)


def test_response_generator_empty_llm_reply_falls_back(sample_templates):
    """Regression: an empty LLM reply must not propagate as the user-visible string."""
    session = DialogueSession()
    node = ActionNode(next_state="ask_information")
    llm = FakeLLM(reply="   ", chat_format=False)
    out = generate_response(
        session, "greet", node, knowledge=None, templates=sample_templates, llm=llm
    )
    assert out == "Say hello."  # fell back to template
