from kgconvai.dialogue.manager import DialogueManager
from kgconvai.state import DialogueSession


def test_manager_advances_session_state(sample_graph):
    mgr = DialogueManager(sample_graph)
    session = DialogueSession()
    node = mgr.step(session, "greet")
    assert node.next_state == "ask_information"
    assert session.current_state == "ask_information"


def test_manager_falls_back_to_start_on_unknown_state(sample_graph):
    mgr = DialogueManager(sample_graph)
    session = DialogueSession(current_state="not_in_graph")
    mgr.step(session, "greet")
    # After resetting to 'start', a 'greet' moves it to 'ask_information'
    assert session.current_state == "ask_information"
