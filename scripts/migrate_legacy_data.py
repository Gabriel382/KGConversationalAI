"""One-shot migration from legacy dialogue_graph/*.json -> canonical kg.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kgconvai.kg.schema import (  # noqa: E402
    FAQEntry,
    Intent,
    KGData,
    State,
    Template,
    Transition,
)


def migrate(legacy_dir: Path, out_path: Path) -> KGData:
    graph_raw = json.loads((legacy_dir / "conversation_graph.json").read_text(encoding="utf-8"))
    faq_raw = json.loads((legacy_dir / "faq.json").read_text(encoding="utf-8"))
    templates_raw = json.loads((legacy_dir / "templates.json").read_text(encoding="utf-8"))

    state_ids = set(graph_raw.keys())
    for outgoing in graph_raw.values():
        state_ids.update(outgoing.values())
    states = [
        State(
            id=s,
            is_terminal=(s == "end"),
            requires_knowledge=(s == "provide_information"),
        )
        for s in sorted(state_ids)
    ]

    intent_ids: set[str] = set()
    for outgoing in graph_raw.values():
        intent_ids.update(outgoing.keys())
    intent_ids.update(faq_raw.keys())
    intent_ids.update(templates_raw.keys())
    intents = [Intent(id=i) for i in sorted(intent_ids)]

    transitions = [
        Transition(**{"from": frm, "intent": intent, "to": to})
        for frm, outgoing in graph_raw.items()
        for intent, to in outgoing.items()
    ]

    faqs = [
        FAQEntry(
            id=f"{intent}__{question}",
            intent=intent,
            question=question.replace("_", " "),
            answer=answer,
        )
        for intent, qs in faq_raw.items()
        for question, answer in qs.items()
    ]

    templates = [Template(intent=intent, text=text) for intent, text in templates_raw.items()]

    data = KGData(
        version="1.0",
        metadata={
            "title": "Default phone-assistant dialogue graph",
            "source": "migrated from legacy dialogue_graph/*.json",
        },
        states=states,
        intents=intents,
        transitions=transitions,
        faqs=faqs,
        templates=templates,
    )
    data.to_json(out_path)
    return data


if __name__ == "__main__":  # pragma: no cover
    legacy = Path("dialogue_graph")
    out = Path("dialogue_graph/kg.json")
    data = migrate(legacy, out)
    print(f"wrote {out}")
    print(
        f"  {len(data.states)} states, {len(data.intents)} intents,"
        f" {len(data.transitions)} transitions,"
        f" {len(data.faqs)} faqs, {len(data.templates)} templates"
    )
