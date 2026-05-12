"""Neo4j backend tests.

Skipped unless a Neo4j server is reachable at the URI specified by
``KGCONVAI_NEO4J_URI`` (default bolt://localhost:7687). To run them:

    docker-compose -f docker/docker-compose.yml up -d neo4j
    pytest tests/kg/test_neo4j_backend.py -m neo4j
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from kgconvai.kg.schema import KGData

ROOT = Path(__file__).resolve().parents[2]


def _neo4j_available() -> bool:
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return False
    uri = os.environ.get("KGCONVAI_NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("KGCONVAI_NEO4J_USER", "neo4j")
    pw = os.environ.get("KGCONVAI_NEO4J_PASSWORD", "kgconvai")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.neo4j,
    pytest.mark.skipif(not _neo4j_available(), reason="Neo4j not reachable"),
]


@pytest.fixture()
def backend():
    from kgconvai.kg.neo4j_backend import Neo4jBackend

    with Neo4jBackend(
        os.environ.get("KGCONVAI_NEO4J_URI", "bolt://localhost:7687"),
        os.environ.get("KGCONVAI_NEO4J_USER", "neo4j"),
        os.environ.get("KGCONVAI_NEO4J_PASSWORD", "kgconvai"),
    ) as be:
        yield be


def test_neo4j_roundtrip(backend):
    data = KGData.from_json(ROOT / "dialogue_graph" / "kg.json")
    graph = backend.import_(data)
    exported = backend.export(graph)

    left = json.loads(data.to_json())
    right = json.loads(exported.to_json())
    for k in ("metadata", "namespace"):
        left.pop(k, None)
        right.pop(k, None)
    assert left["states"] == right["states"]
    assert left["intents"] == right["intents"]
    assert left["transitions"] == right["transitions"]
    assert left["faqs"] == right["faqs"]
    assert left["templates"] == right["templates"]
