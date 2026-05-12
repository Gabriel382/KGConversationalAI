"""End-to-end eval runner tests with a deterministic classifier."""

from __future__ import annotations

from kgconvai.eval import IntentDataset, IntentExample, run_intent_eval
from kgconvai.eval.dataset import FAQDataset, FAQExample
from kgconvai.eval.runner import run_faq_eval
from kgconvai.nlu.classifier import Classification, Classifier


class PerfectClassifier(Classifier):
    """Always ranks the expected label first."""

    def __init__(self, gold: dict[str, str]) -> None:
        self.gold = gold

    def classify(self, text: str, candidates: list[str]) -> list[Classification]:
        expected = self.gold.get(text)
        scored = [Classification(c, 1.0 if c == expected else 0.0) for c in candidates]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored


def test_intent_eval_perfect_run():
    gold = {"hi": "greet", "bye": "goodbye"}
    ds = IntentDataset(
        version="1.0",
        candidates=["greet", "goodbye", "cancel"],
        examples=[
            IntentExample("hi", "greet"),
            IntentExample("bye", "goodbye"),
        ],
    )
    report = run_intent_eval(ds, PerfectClassifier(gold), classifier_name="perfect")
    assert report.metrics.n == 2
    assert report.metrics.accuracy == 1.0
    assert report.metrics.p_at_3 == 1.0
    assert report.metrics.mrr == 1.0
    assert len(report.examples) == 2
    assert all(e.correct for e in report.examples)


def test_intent_eval_all_wrong():
    ds = IntentDataset(
        version="1.0",
        candidates=["greet", "goodbye"],
        examples=[
            IntentExample("only-known-to-wrong-classifier", "greet"),
        ],
    )

    class WrongClassifier(Classifier):
        def classify(self, text, candidates):
            return [Classification("goodbye", 0.99), Classification("greet", 0.01)]

    report = run_intent_eval(ds, WrongClassifier(), classifier_name="wrong")
    assert report.metrics.accuracy == 0.0
    assert report.metrics.mrr == 0.5  # expected was rank 2 -> 1/2


def test_faq_eval_uses_per_intent_candidates():
    ds = FAQDataset(
        version="1.0",
        examples=[
            FAQExample("when do you open", "ask_information", "hours"),
            FAQExample("how to book", "book_meeting", "book"),
        ],
    )
    cands = {
        "ask_information": ["hours", "address"],
        "book_meeting": ["book"],
    }

    class FlatClassifier(Classifier):
        def classify(self, text, candidates):
            return [Classification(c, 1.0 / (i + 1)) for i, c in enumerate(candidates)]

    report = run_faq_eval(ds, FlatClassifier(), cands, classifier_name="flat")
    assert report.metrics.n == 2
    # Flat-classifier ranks candidates in their input order;
    # 'hours' is first in ask_information and 'book' is the only option, so both correct.
    assert report.metrics.accuracy == 1.0


def test_run_report_to_json(tmp_path):
    ds = IntentDataset(version="1.0", candidates=["a"], examples=[IntentExample("x", "a")])
    rep = run_intent_eval(ds, PerfectClassifier({"x": "a"}), classifier_name="perfect")
    p = tmp_path / "rep.json"
    rep.to_json(p)
    text = p.read_text(encoding="utf-8")
    assert '"accuracy"' in text
    assert '"perfect"' in text
