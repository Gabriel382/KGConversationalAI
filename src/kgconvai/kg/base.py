"""Abstract interfaces for knowledge-graph backends.

Two concrete backends ship with the package: rdflib (in-process,
zero-install, used in CI) and Neo4j (production-grade, runs in Docker).
Both implement the same three interfaces:

* ``KnowledgeGraph`` -- query the graph (SPARQL or Cypher).
* ``KGImporter``     -- build the graph from canonical ``KGData``.
* ``KGExporter``     -- emit canonical ``KGData`` from the graph.

A backend that implements all three (``KGBackend``) round-trips JSON
losslessly: ``backend.export(backend.import_(data)) == data``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from kgconvai.kg.schema import KGData


class KnowledgeGraph(ABC):
    """A queryable knowledge graph."""

    @abstractmethod
    def query(self, query: str) -> list[dict[str, Any]]:
        """Run a query (SPARQL for RDF, Cypher for Neo4j) and return rows."""

    @abstractmethod
    def size(self) -> int:
        """Number of triples (RDF) or nodes+relationships (Neo4j)."""


class KGImporter(ABC):
    """Build a backend-specific graph from canonical KG data."""

    @abstractmethod
    def import_(self, data: KGData) -> KnowledgeGraph: ...


class KGExporter(ABC):
    """Extract canonical KG data from a backend-specific graph."""

    @abstractmethod
    def export(self, graph: KnowledgeGraph) -> KGData: ...


class KGBackend(KGImporter, KGExporter):
    """Composite of :class:`KGImporter` + :class:`KGExporter`.

    Implementations gain a free round-trip helper.
    """

    def roundtrip(self, data: KGData) -> KGData:
        """Import then immediately export. Useful in tests."""
        graph = self.import_(data)
        return self.export(graph)
