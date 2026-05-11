from kgconvai.nlu.faq import retrieve_answer
from tests.conftest import FakeClassifier


def test_retrieve_answer_empty_text(sample_faq):
    out = retrieve_answer("", "ask_information", sample_faq, FakeClassifier())
    assert "didn't catch" in out


def test_retrieve_answer_unknown_intent(sample_faq):
    out = retrieve_answer("hi", "nope", sample_faq, FakeClassifier())
    assert "not sure about that topic" in out.lower()


def test_retrieve_answer_high_confidence_returns_answer(sample_faq):
    clf = FakeClassifier(rules={"when do you open": "what_are_your_opening_hours"})
    out = retrieve_answer("when do you open", "ask_information", sample_faq, clf)
    assert "9 to 6" in out


def test_retrieve_answer_low_confidence_returns_hedge(sample_faq, monkeypatch):
    # FakeClassifier(no rule) tops out at 0.30; threshold 0.4 -> hedge
    out = retrieve_answer(
        "something weird",
        "ask_information",
        sample_faq,
        FakeClassifier(),
        confidence_threshold=0.4,
    )
    assert "not fully sure" in out.lower()
