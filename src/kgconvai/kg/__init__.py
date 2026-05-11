"""Knowledge-graph layer.

Three abstractions:

* :class:`KGData` is the canonical Pydantic-backed in-memory representation
  of a dialogue knowledge graph (states, intents, transitions, FAQ entries,
  templates, optional domain entities/relations).
* :class:`KnowledgeGraph` is the runtime view (RDF, Neo4j, …) that supports
  graph queries (SPARQL or Cypher).
* :class:`KGImporter` / :class:`KGExporter` round-trip between canonical
  JSON and a backend-specific graph.
"""

from kgconvai.kg.base import KGExporter, KGImporter, KnowledgeGraph
from kgconvai.kg.schema import (
    Entity,
    FAQEntry,
    Intent,
    KGData,
    Relation,
    State,
    Template,
    Transition,
)

__all__ = [
    "Entity",
    "FAQEntry",
    "Intent",
    "KGData",
    "KGExporter",
    "KGImporter",
    "KnowledgeGraph",
    "Relation",
    "State",
    "Template",
    "Transition",
]
