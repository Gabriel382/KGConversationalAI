"""Evaluation harness.

* :class:`IntentExample` / :class:`FAQExample` -- typed labelled examples.
* :func:`load_intent_dataset` / :func:`load_faq_dataset` -- read YAML files.
* :func:`run_intent_eval` / :func:`run_faq_eval` -- run a Classifier against
  a labelled set and return a :class:`RunReport` with metrics + per-example
  outcomes.
* :func:`format_report` -- pretty rich.Table output.
* JSON export so CI can post the metrics as a PR comment.
"""

from kgconvai.eval.dataset import (
    FAQDataset,
    FAQExample,
    IntentDataset,
    IntentExample,
    load_faq_dataset,
    load_intent_dataset,
)
from kgconvai.eval.runner import (
    Metrics,
    RunReport,
    format_report,
    run_faq_eval,
    run_intent_eval,
)

__all__ = [
    "FAQDataset",
    "FAQExample",
    "IntentDataset",
    "IntentExample",
    "Metrics",
    "RunReport",
    "format_report",
    "load_faq_dataset",
    "load_intent_dataset",
    "run_faq_eval",
    "run_intent_eval",
]
