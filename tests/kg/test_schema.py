"""Canonical schema + Pydantic model tests."""

from __future__ import annotations

import json

import jsonschema
import pytest

from kgconvai.kg.schema import (
    Intent,
    KGData,
    State,
    Template,
    Transition,
    validate_against_schema,
)


def _minimal_data() -> KGData:
    return KGData(
        states=[State(id="start"), State(id="end", is_terminal=True)],
        intents=[Intent(id="greet"), Intent(id="goodbye")],
        transitions=[
            Transition(**{"from": "start", "intent": "greet", "to": "end"}),
            Transition(**{"from": "start", "intent": "goodbye", "to": "end"}),
        ],
        faqs=[],
        templates=[Template(intent="greet", text="Hi!")],
    )


def test_kgdata_roundtrip_to_dict():
    """to_json canonicalises ordering, so compare as sorted sets."""
    data = _minimal_data()
    j = data.to_json()
    restored = KGData.model_validate_json(j)
    assert {s.id for s in restored.states} == {s.id for s in data.states}
    assert {(t.from_state, t.intent, t.to) for t in restored.transitions} == {
        (t.from_state, t.intent, t.to) for t in data.transitions
    }


def test_kgdata_to_json_is_canonical(tmp_path):
    """to_json must produce deterministic output regardless of input order."""
    data_a = KGData(
        states=[State(id="b"), State(id="a")],
        intents=[Intent(id="z"), Intent(id="a")],
        transitions=[
            Transition(**{"from": "a", "intent": "z", "to": "b"}),
            Transition(**{"from": "a", "intent": "a", "to": "b"}),
        ],
        faqs=[],
        templates=[],
    )
    text = data_a.to_json()
    payload = json.loads(text)
    assert [s["id"] for s in payload["states"]] == ["a", "b"]
    assert [i["id"] for i in payload["intents"]] == ["a", "z"]
    assert [t["intent"] for t in payload["transitions"]] == ["a", "z"]


def test_invalid_id_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        State(id="has space")
    with pytest.raises(ValidationError):
        State(id="1leading_digit")


def test_invalid_version_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        KGData(version="not-semver")


def test_json_schema_validates_minimal():
    payload = json.loads(_minimal_data().to_json())
    validate_against_schema(payload)


def test_json_schema_rejects_missing_required():
    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(
            {
                "version": "1.0",
                "states": [],
                "intents": [],
                "transitions": [],
                "faqs": [],
                "templates": [],
                "extra_field": "not allowed",
            }
        )
