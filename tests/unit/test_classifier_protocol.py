from tests.conftest import FakeClassifier


def test_fake_classifier_top_label_obeys_rule():
    clf = FakeClassifier(rules={"hi": "greet"})
    out = clf.classify("hi", ["greet", "goodbye"])
    assert out[0].label == "greet"
    assert out[0].score == 0.99


def test_fake_classifier_empty_inputs_return_empty():
    clf = FakeClassifier()
    assert clf.classify("", ["a"]) == []
    assert clf.classify("hi", []) == []
