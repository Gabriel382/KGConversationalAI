"""Pydantic models mirroring the canonical JSON schema.

The shapes are intentionally close to the JSON Schema in
``schemas/kgconvai.schema.json`` so validation by either tool produces
equivalent results.
"""

from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, field_validator

# RFC 3987-style local IDs, kept simple for IRI fragment safety.
_ID_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
DEFAULT_NAMESPACE = "http://kgconvai.local/data#"


def _check_id(value: str) -> str:
    if not _ID_PATTERN.match(value):
        raise ValueError(f"invalid identifier: {value!r}")
    return value


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False, populate_by_name=True)


class State(_Base):
    id: str
    label: str | None = None
    is_terminal: bool = False
    requires_knowledge: bool = False
    description: str | None = None

    @field_validator("id")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class Intent(_Base):
    id: str
    label: str | None = None
    description: str | None = None
    examples: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class Transition(_Base):
    # `from` is a Python keyword; use Field alias.
    from_state: str = Field(alias="from")
    intent: str
    to: str
    description: str | None = None

    @field_validator("from_state", "intent", "to")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class FAQEntry(_Base):
    id: str
    intent: str
    question: str
    answer: str
    examples: list[str] = Field(default_factory=list)

    @field_validator("id", "intent")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class Template(_Base):
    intent: str
    text: str
    locale: str = "en"

    @field_validator("intent")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class Entity(_Base):
    id: str
    type: str
    label: str | None = None
    properties: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class Relation(_Base):
    from_entity: str = Field(alias="from")
    type: str
    to: str

    @field_validator("from_entity", "to")
    @classmethod
    def _v(cls, v: str) -> str:
        return _check_id(v)


class KGData(_Base):
    """Canonical in-memory representation of a dialogue knowledge graph."""

    version: str = "1.0"
    metadata: dict[str, object] = Field(default_factory=dict)
    namespace: str = DEFAULT_NAMESPACE
    states: list[State] = Field(default_factory=list)
    intents: list[Intent] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    faqs: list[FAQEntry] = Field(default_factory=list)
    templates: list[Template] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def _version_pattern(cls, v: str) -> str:
        if not _VERSION_PATTERN.match(v):
            raise ValueError(f"version must match MAJOR.MINOR (got {v!r})")
        return v

    # ------------------------------------------------------------------ #
    # IO                                                                  #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_json(cls, path: str | Path) -> KGData:
        """Load and validate a canonical JSON file."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        validate_against_schema(raw)
        return cls.model_validate(raw)

    def to_json(self, path: str | Path | None = None, *, indent: int = 2) -> str:
        """Serialise to canonical JSON. Writes to ``path`` if given.

        Output is canonicalised (lists sorted, dict keys sorted) so round-trips
        through any KG backend produce byte-identical output.
        """
        payload = self.model_dump(by_alias=True, exclude_none=True)
        _canonicalise_lists(payload)
        text = json.dumps(payload, indent=indent, sort_keys=True, ensure_ascii=False)
        if path is not None:
            Path(path).write_text(text + "\n", encoding="utf-8")
        return text

    # ------------------------------------------------------------------ #
    # Convenience accessors                                               #
    # ------------------------------------------------------------------ #

    def candidate_intents(self) -> list[str]:
        return sorted({t.intent for t in self.transitions})

    def state_ids(self) -> set[str]:
        return {s.id for s in self.states}

    def intent_ids(self) -> set[str]:
        return {i.id for i in self.intents}


# ---------------------------------------------------------------------------- #
# JSON Schema validation                                                       #
# ---------------------------------------------------------------------------- #


def _load_schema() -> dict:
    """Locate schemas/kgconvai.schema.json relative to the repo or package."""
    # Try repo layout first (development install)
    candidates = [
        Path(__file__).resolve().parents[3] / "schemas" / "kgconvai.schema.json",
        Path("schemas/kgconvai.schema.json"),
    ]
    # Also try as a packaged resource
    try:
        with resources.files("kgconvai").joinpath("kgconvai.schema.json").open("rb") as f:
            return json.load(f)
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass
    for c in candidates:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "Could not find schemas/kgconvai.schema.json — install the package "
        "or run from the repo root."
    )


def validate_against_schema(data: dict) -> None:
    """Raise ``jsonschema.ValidationError`` if data is not a valid KG document."""
    schema = _load_schema()
    jsonschema.validate(data, schema)


def _canonicalise_lists(payload: dict) -> None:
    """Sort list-valued sections by a stable key for deterministic output."""

    def _key_state(s: dict) -> tuple:
        return (s["id"],)

    def _key_intent(i: dict) -> tuple:
        return (i["id"],)

    def _key_transition(t: dict) -> tuple:
        return (t["from"], t["intent"], t["to"])

    def _key_faq(f: dict) -> tuple:
        return (f["id"],)

    def _key_template(t: dict) -> tuple:
        return (t["intent"], t.get("locale", "en"))

    def _key_entity(e: dict) -> tuple:
        return (e["id"],)

    def _key_relation(r: dict) -> tuple:
        return (r["from"], r["type"], r["to"])

    for key, keyfn in [
        ("states", _key_state),
        ("intents", _key_intent),
        ("transitions", _key_transition),
        ("faqs", _key_faq),
        ("templates", _key_template),
        ("entities", _key_entity),
        ("relations", _key_relation),
    ]:
        if key in payload and isinstance(payload[key], list):
            payload[key] = sorted(payload[key], key=keyfn)
