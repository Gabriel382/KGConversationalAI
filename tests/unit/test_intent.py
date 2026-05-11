from kgconvai.nlu.intent import detect_intent
from tests.conftest import FakeClassifier


def test_detect_intent_empty_text_returns_unknown():
    assert detect_intent("", FakeClassifier(), ["greet"]) == "unknown"


def test_detect_intent_returns_top_label():
    clf = FakeClassifier(rules={"hello there": "greet"})
    assert detect_intent("Hello there", clf, ["greet", "goodbye"]) == "greet"
