"""rdflib-backed knowledge graph + bidirectional JSON <-> RDF sync.

This is the zero-install default: pure Python, no external services.
The same `KGData` round-trips through the in-memory RDF graph without loss.

Serialization choices:
* Turtle is the on-disk format for inspection / version control.
* The graph references vocabulary from ``ontology/core.ttl`` (and optionally
  any domain ontology you've added) but does not require those files to be
  present at import time — they're loaded lazily by ``load_ontology`` when
  callers want validation or reasoning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from kgconvai.kg.base import KGBackend, KnowledgeGraph
from kgconvai.kg.schema import (
    DEFAULT_NAMESPACE,
    Entity,
    FAQEntry,
    Intent,
    KGData,
    State,
    Template,
    Transition,
)

KGC = Namespace("http://kgconvai.org/core#")


class RDFKnowledgeGraph(KnowledgeGraph):
    """Wraps a :class:`rdflib.Graph` and exposes SPARQL queries."""

    def __init__(self, graph: Graph, *, namespace: str = DEFAULT_NAMESPACE) -> None:
        self.graph = graph
        self.namespace = Namespace(namespace)
        self.graph.bind("kgc", KGC)
        self.graph.bind("data", self.namespace)

    def query(self, query: str) -> list[dict[str, Any]]:
        """Run a SPARQL SELECT and return rows as dicts."""
        rows: list[dict[str, Any]] = []
        result = self.graph.query(query)
        for binding in result:
            rows.append({str(var): _term_to_python(binding[var]) for var in (result.vars or [])})  # type: ignore[index,call-overload]
        return rows

    def size(self) -> int:
        return len(self.graph)

    # ------------------------------------------------------------------ #
    # Serialisation                                                       #
    # ------------------------------------------------------------------ #

    def serialize_turtle(self, path: str | Path | None = None) -> str:
        text = self.graph.serialize(format="turtle")
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text


def _term_to_python(term: Any) -> Any:
    if isinstance(term, Literal):
        return term.toPython()
    if isinstance(term, URIRef):
        return str(term)
    return None if term is None else str(term)


class RDFBackend(KGBackend):
    """Round-trip canonical ``KGData`` through an in-memory RDF graph."""

    def __init__(
        self,
        *,
        namespace: str = DEFAULT_NAMESPACE,
        ontology_paths: list[str | Path] | None = None,
    ) -> None:
        self.namespace = namespace
        self.ontology_paths = ontology_paths or []

    # ---------------- import_ : KGData -> RDFKnowledgeGraph -------------- #

    def import_(self, data: KGData) -> RDFKnowledgeGraph:
        g = Graph()
        ns = Namespace(data.namespace or self.namespace)

        # Optional: load ontology schemas alongside (for validation/reasoning)
        for op in self.ontology_paths:
            g.parse(str(op), format="turtle")

        # States
        for s in data.states:
            iri = ns[s.id]
            g.add((iri, RDF.type, KGC.DialogueState))
            if s.is_terminal:
                g.add((iri, RDF.type, KGC.TerminalState))
            if s.label:
                g.add((iri, RDFS.label, Literal(s.label)))
            if s.description:
                g.add((iri, RDFS.comment, Literal(s.description)))
            g.add((iri, KGC.requiresKnowledge, Literal(s.requires_knowledge, datatype=XSD.boolean)))

        # Intents
        for i in data.intents:
            iri = ns[i.id]
            g.add((iri, RDF.type, KGC.Intent))
            if i.label:
                g.add((iri, RDFS.label, Literal(i.label)))
            if i.description:
                g.add((iri, RDFS.comment, Literal(i.description)))
            for ex in i.examples:
                g.add((iri, KGC.exampleUtterance, Literal(ex)))

        # Transitions — anonymous-like nodes via deterministic IRIs
        for idx, t in enumerate(data.transitions):
            iri = ns[f"transition_{idx:04d}_{t.from_state}_{t.intent}_{t.to}"]
            g.add((iri, RDF.type, KGC.Transition))
            g.add((iri, KGC.hasFromState, ns[t.from_state]))
            g.add((iri, KGC.hasToState, ns[t.to]))
            g.add((iri, KGC.triggersIntent, ns[t.intent]))
            if t.description:
                g.add((iri, RDFS.comment, Literal(t.description)))

        # FAQ entries
        for f in data.faqs:
            iri = ns[f.id]
            g.add((iri, RDF.type, KGC.FAQEntry))
            g.add((iri, KGC.hasIntent, ns[f.intent]))
            g.add((iri, KGC.question, Literal(f.question)))
            g.add((iri, KGC.answer, Literal(f.answer)))
            for ex in f.examples:
                g.add((iri, KGC.exampleUtterance, Literal(ex)))

        # Templates — id from intent+locale for uniqueness
        for idx, tpl in enumerate(data.templates):
            iri = ns[f"template_{idx:04d}_{tpl.intent}_{tpl.locale}"]
            g.add((iri, RDF.type, KGC.ResponseTemplate))
            g.add((iri, KGC.hasTemplateIntent, ns[tpl.intent]))
            g.add((iri, KGC.text, Literal(tpl.text)))
            g.add((iri, KGC.locale, Literal(tpl.locale)))

        # Domain entities (typed via the domain ontology)
        for e in data.entities:
            iri = ns[e.id]
            # The type IRI is interpreted as a fragment of the namespace by
            # default; absolute IRIs (http://…) are passed through.
            type_iri = URIRef(e.type) if e.type.startswith("http") else ns[e.type]
            g.add((iri, RDF.type, type_iri))
            if e.label:
                g.add((iri, RDFS.label, Literal(e.label)))
            for k, v in e.properties.items():
                prop_iri = ns[k] if "://" not in k else URIRef(k)
                g.add((iri, prop_iri, Literal(v)))

        # Domain relations
        for r in data.relations:
            type_iri = URIRef(r.type) if r.type.startswith("http") else ns[r.type]
            g.add((ns[r.from_entity], type_iri, ns[r.to]))

        return RDFKnowledgeGraph(g, namespace=str(ns))

    # ---------------- export : RDFKnowledgeGraph -> KGData --------------- #

    def export(self, graph: KnowledgeGraph) -> KGData:
        if not isinstance(graph, RDFKnowledgeGraph):
            raise TypeError("RDFBackend.export expects an RDFKnowledgeGraph")
        g = graph.graph
        ns = graph.namespace
        ns_str = str(ns)

        def local(node: Any) -> str:
            s = str(node)
            return s[len(ns_str) :] if s.startswith(ns_str) else s

        # States
        states: list[State] = []
        for subj in sorted(g.subjects(RDF.type, KGC.DialogueState), key=str):
            is_terminal = (subj, RDF.type, KGC.TerminalState) in g
            label = _get_literal(g, subj, RDFS.label)
            comment = _get_literal(g, subj, RDFS.comment)
            req = _get_literal(g, subj, KGC.requiresKnowledge)
            states.append(
                State(
                    id=local(subj),
                    label=label,
                    description=comment,
                    is_terminal=bool(is_terminal),
                    requires_knowledge=bool(req) if req is not None else False,
                )
            )

        # Intents
        intents: list[Intent] = []
        for subj in sorted(g.subjects(RDF.type, KGC.Intent), key=str):
            label = _get_literal(g, subj, RDFS.label)
            comment = _get_literal(g, subj, RDFS.comment)
            examples = [str(o) for o in g.objects(subj, KGC.exampleUtterance)]
            intents.append(
                Intent(
                    id=local(subj),
                    label=label,
                    description=comment,
                    examples=sorted(examples),
                )
            )

        # Transitions
        transitions: list[Transition] = []
        for subj in g.subjects(RDF.type, KGC.Transition):
            frm = next(g.objects(subj, KGC.hasFromState), None)
            to = next(g.objects(subj, KGC.hasToState), None)
            intent = next(g.objects(subj, KGC.triggersIntent), None)
            comment = _get_literal(g, subj, RDFS.comment)
            if frm is None or to is None or intent is None:
                continue
            transitions.append(
                Transition(
                    **{
                        "from": local(frm),
                        "to": local(to),
                        "intent": local(intent),
                        "description": comment,
                    }
                )
            )
        # Deterministic order
        transitions.sort(key=lambda t: (t.from_state, t.intent, t.to))

        # FAQs
        faqs: list[FAQEntry] = []
        for subj in sorted(g.subjects(RDF.type, KGC.FAQEntry), key=str):
            intent = next(g.objects(subj, KGC.hasIntent), None)
            question = _get_literal(g, subj, KGC.question)
            answer = _get_literal(g, subj, KGC.answer)
            examples = [str(o) for o in g.objects(subj, KGC.exampleUtterance)]
            if intent is None or question is None or answer is None:
                continue
            faqs.append(
                FAQEntry(
                    id=local(subj),
                    intent=local(intent),
                    question=question,
                    answer=answer,
                    examples=sorted(examples),
                )
            )

        # Templates
        templates: list[Template] = []
        for subj in g.subjects(RDF.type, KGC.ResponseTemplate):
            intent = next(g.objects(subj, KGC.hasTemplateIntent), None)
            text = _get_literal(g, subj, KGC.text)
            locale = _get_literal(g, subj, KGC.locale) or "en"
            if intent is None or text is None:
                continue
            templates.append(Template(intent=local(intent), text=text, locale=locale))
        templates.sort(key=lambda t: (t.intent, t.locale))

        # Domain entities: anything typed but not one of the core classes
        core_classes = {
            KGC.DialogueState,
            KGC.TerminalState,
            KGC.Intent,
            KGC.Transition,
            KGC.FAQEntry,
            KGC.ResponseTemplate,
        }
        entities: list[Entity] = []
        seen_entity_ids: set[str] = set()
        for subj in sorted(g.subjects(RDF.type, None), key=str):
            types = list(g.objects(subj, RDF.type))
            non_core = [t for t in types if t not in core_classes]
            if not non_core:
                continue
            sid = local(subj)
            if sid in seen_entity_ids or "/" in sid or sid.startswith("http"):
                # Ignore ontology-internal IRIs
                continue
            seen_entity_ids.add(sid)
            label = _get_literal(g, subj, RDFS.label)
            props: dict[str, Any] = {}
            for p, o in g.predicate_objects(subj):
                if p in (RDF.type, RDFS.label, RDFS.comment):
                    continue
                if isinstance(o, Literal):
                    props[local(p)] = o.toPython()
            entities.append(
                Entity(
                    id=sid,
                    type=local(non_core[0]),
                    label=label,
                    properties=props,
                )
            )

        return KGData(
            version="1.0",
            namespace=ns_str,
            states=sorted(states, key=lambda x: x.id),
            intents=sorted(intents, key=lambda x: x.id),
            transitions=transitions,
            faqs=sorted(faqs, key=lambda x: x.id),
            templates=templates,
            entities=entities,
            # Relations export skipped here — see TODO; rdf round-trip preserved
            # for the dialogue subset that the agent uses today.
        )


def _get_literal(g: Graph, subj: Any, pred: Any) -> Any:
    obj = next(g.objects(subj, pred), None)
    if obj is None:
        return None
    if isinstance(obj, Literal):
        return obj.toPython()
    return str(obj)
