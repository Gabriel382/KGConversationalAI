"""rdflib backend + JSON <-> RDF round-trip tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kgconvai.kg.rdf_backend import RDFBackend
from kgconvai.kg.schema import KGData

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def kg_data() -> KGData:
    return KGData.from_json(ROOT / "dialogue_graph" / "kg.json")


def test_rdf_backend_imports_triples(kg_data):
    be = RDFBackend()
    graph = be.import_(kg_data)
    assert graph.size() > 0
    # At least one DialogueState should be queryable
    rows = graph.query(
        "PREFIX kgc: <http://kgconvai.org/core#> "
        "SELECT (COUNT(?s) AS ?n) WHERE { ?s a kgc:DialogueState }"
    )
    assert int(rows[0]["n"]) == len(kg_data.states)


def test_rdf_roundtrip_preserves_dialogue_sections(kg_data):
    """JSON -> RDF -> JSON preserves the dialogue subset (sans metadata)."""
    be = RDFBackend()
    graph = be.import_(kg_data)
    exported = be.export(graph)

    left = json.loads(kg_data.to_json())
    right = json.loads(exported.to_json())
    for k in ("metadata", "namespace"):
        left.pop(k, None)
        right.pop(k, None)
    assert left == right


def test_rdf_sparql_traversal(kg_data):
    """SPARQL queries can chase transitions through the graph."""
    be = RDFBackend()
    graph = be.import_(kg_data)
    rows = graph.query(
        """
        PREFIX kgc: <http://kgconvai.org/core#>
        SELECT ?from ?intent ?to WHERE {
            ?t a kgc:Transition ;
               kgc:hasFromState ?from ;
               kgc:triggersIntent ?intent ;
               kgc:hasToState ?to .
        }
        """
    )
    assert len(rows) == len(kg_data.transitions)


def test_rdf_loads_ontology(tmp_path, kg_data):
    """When an ontology is supplied, its triples appear in the graph."""
    ttl = tmp_path / "core.ttl"
    ttl.write_text(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "<http://kgconvai.org/core> a owl:Ontology .\n",
        encoding="utf-8",
    )
    be = RDFBackend(ontology_paths=[ttl])
    graph = be.import_(kg_data)
    rows = graph.query(
        "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT ?o WHERE { ?o a owl:Ontology }"
    )
    assert rows
