import pytest

from kgconvai.dialogue.graph import DialogueGraph


def test_graph_requires_start_state():
    with pytest.raises(ValueError):
        DialogueGraph({"foo": {}})


def test_graph_candidate_intents_are_unique_and_sorted(sample_graph):
    labels = sample_graph.candidate_intents()
    assert labels == sorted(set(labels))
    assert "greet" in labels


def test_graph_transition_known_intent(sample_graph):
    node = sample_graph.transition("start", "greet")
    assert node.next_state == "ask_information"
    assert node.requires_kb is False


def test_graph_transition_marks_kb_state(sample_graph):
    node = sample_graph.transition("ask_information", "ask_information")
    assert node.next_state == "provide_information"
    assert node.requires_kb is True


def test_graph_transition_unknown_intent_stays(sample_graph):
    node = sample_graph.transition("start", "totally_unknown")
    assert node.next_state == "start"
