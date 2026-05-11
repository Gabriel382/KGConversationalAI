"""Neo4j-backed knowledge graph + bidirectional JSON <-> Cypher sync.

This backend speaks property-graph terms (labels, nodes, relationships) rather
than triples, but exposes the same ``KGImporter`` / ``KGExporter`` contracts.

To run locally:
    docker-compose -f docker/docker-compose.yml up -d neo4j
    KGCONVAI_NEO4J_URI=bolt://localhost:7687 \\
    KGCONVAI_NEO4J_USER=neo4j \\
    KGCONVAI_NEO4J_PASSWORD=kgconvai \\
    python -m kgconvai kg import --backend neo4j --from dialogue_graph/kg.json

The driver is imported lazily so ``import kgconvai.kg`` works without neo4j
installed.
"""

from __future__ import annotations

from typing import Any

from kgconvai.kg.base import KGBackend, KnowledgeGraph
from kgconvai.kg.schema import (
    DEFAULT_NAMESPACE,
    Entity,
    FAQEntry,
    Intent,
    KGData,
    Relation,
    State,
    Template,
    Transition,
)


class Neo4jKnowledgeGraph(KnowledgeGraph):
    """Wraps a Neo4j driver session and exposes Cypher queries."""

    def __init__(self, driver: Any, *, database: str = "neo4j") -> None:
        self.driver = driver
        self.database = database

    def query(self, query: str) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as s:
            return [r.data() for r in s.run(query)]

    def size(self) -> int:
        rows = self.query(
            "MATCH (n) RETURN count(n) AS nodes UNION ALL MATCH ()-[r]->() RETURN count(r) AS nodes"
        )
        return sum(int(r["nodes"]) for r in rows)


class Neo4jBackend(KGBackend):
    """Round-trip canonical ``KGData`` through a Neo4j database.

    Connection params:
        uri      : bolt URI, e.g. ``bolt://localhost:7687``
        user     : database user, default ``neo4j``
        password : database password
        database : database name, default ``neo4j``

    Each ``import_`` call wipes the database and reloads it from the KG data.
    Use a dedicated database for kgconvai content if that's not what you want.
    """

    def __init__(
        self,
        uri: str,
        user: str = "neo4j",
        password: str = "kgconvai",
        *,
        database: str = "neo4j",
        wipe_on_import: bool = True,
    ) -> None:
        # Lazy import so the package works without neo4j installed
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "The neo4j driver is required for Neo4jBackend. "
                "Install with: pip install kgconvai[neo4j]"
            ) from exc

        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.wipe_on_import = wipe_on_import

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> Neo4jBackend:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ---------------- import_ : KGData -> Neo4jKnowledgeGraph ------------ #

    def import_(self, data: KGData) -> Neo4jKnowledgeGraph:
        with self._driver.session(database=self.database) as s:
            if self.wipe_on_import:
                s.run("MATCH (n) DETACH DELETE n")

            # States
            for st in data.states:
                s.run(
                    "MERGE (n:State {id: $id}) SET "
                    " n.label = $label, "
                    " n.is_terminal = $is_terminal, "
                    " n.requires_knowledge = $requires_knowledge, "
                    " n.description = $description",
                    id=st.id,
                    label=st.label,
                    is_terminal=st.is_terminal,
                    requires_knowledge=st.requires_knowledge,
                    description=st.description,
                )

            # Intents
            for it in data.intents:
                s.run(
                    "MERGE (n:Intent {id: $id}) SET "
                    " n.label = $label, "
                    " n.description = $description, "
                    " n.examples = $examples",
                    id=it.id,
                    label=it.label,
                    description=it.description,
                    examples=it.examples,
                )

            # Transitions: (State)-[:TRANSITIONS {intent}]->(State)
            for tr in data.transitions:
                s.run(
                    "MATCH (a:State {id: $f}), (b:State {id: $t}) "
                    "MERGE (a)-[r:TRANSITIONS {intent: $i}]->(b) "
                    "SET r.description = $description",
                    f=tr.from_state,
                    t=tr.to,
                    i=tr.intent,
                    description=tr.description,
                )

            # FAQ entries
            for fq in data.faqs:
                s.run(
                    "MERGE (n:FAQ {id: $id}) SET "
                    " n.question = $question, n.answer = $answer, "
                    " n.intent_id = $intent, n.examples = $examples",
                    id=fq.id,
                    question=fq.question,
                    answer=fq.answer,
                    intent=fq.intent,
                    examples=fq.examples,
                )
                s.run(
                    "MATCH (q:FAQ {id: $id}), (i:Intent {id: $intent}) "
                    "MERGE (q)-[:HAS_INTENT]->(i)",
                    id=fq.id,
                    intent=fq.intent,
                )

            # Templates
            for idx, tpl in enumerate(data.templates):
                tid = f"template_{idx:04d}_{tpl.intent}_{tpl.locale}"
                s.run(
                    "MERGE (n:Template {id: $id}) SET "
                    " n.text = $text, n.locale = $locale, n.intent_id = $intent",
                    id=tid,
                    text=tpl.text,
                    locale=tpl.locale,
                    intent=tpl.intent,
                )
                s.run(
                    "MATCH (t:Template {id: $id}), (i:Intent {id: $intent}) "
                    "MERGE (t)-[:HAS_INTENT]->(i)",
                    id=tid,
                    intent=tpl.intent,
                )

            # Domain entities — labels derived from `type`
            for e in data.entities:
                s.run(
                    f"MERGE (n:`{e.type}` {{id: $id}}) SET n.label = $label, n += $props",
                    id=e.id,
                    label=e.label,
                    props=e.properties,
                )

            # Domain relations
            for r in data.relations:
                s.run(
                    f"MATCH (a {{id: $f}}), (b {{id: $t}}) MERGE (a)-[:`{r.type}`]->(b)",
                    f=r.from_entity,
                    t=r.to,
                )

        return Neo4jKnowledgeGraph(self._driver, database=self.database)

    # ---------------- export : Neo4jKnowledgeGraph -> KGData ------------- #

    def export(self, graph: KnowledgeGraph) -> KGData:
        if not isinstance(graph, Neo4jKnowledgeGraph):
            raise TypeError("Neo4jBackend.export expects a Neo4jKnowledgeGraph")

        def rows(q: str) -> list[dict]:
            return graph.query(q)

        states = [
            State(
                id=r["id"],
                label=r.get("label"),
                description=r.get("description"),
                is_terminal=bool(r.get("is_terminal", False)),
                requires_knowledge=bool(r.get("requires_knowledge", False)),
            )
            for r in rows(
                "MATCH (n:State) RETURN n.id AS id, n.label AS label, "
                "n.description AS description, n.is_terminal AS is_terminal, "
                "n.requires_knowledge AS requires_knowledge ORDER BY n.id"
            )
        ]

        intents = [
            Intent(
                id=r["id"],
                label=r.get("label"),
                description=r.get("description"),
                examples=list(r.get("examples") or []),
            )
            for r in rows(
                "MATCH (n:Intent) RETURN n.id AS id, n.label AS label, "
                "n.description AS description, n.examples AS examples ORDER BY n.id"
            )
        ]

        transitions_raw = rows(
            "MATCH (a:State)-[r:TRANSITIONS]->(b:State) "
            "RETURN a.id AS frm, r.intent AS intent, b.id AS to, "
            "       r.description AS description "
            "ORDER BY a.id, r.intent, b.id"
        )
        transitions = [
            Transition(
                **{
                    "from": r["frm"],
                    "intent": r["intent"],
                    "to": r["to"],
                    "description": r.get("description"),
                }
            )
            for r in transitions_raw
        ]

        faqs = [
            FAQEntry(
                id=r["id"],
                intent=r["intent"],
                question=r["question"],
                answer=r["answer"],
                examples=list(r.get("examples") or []),
            )
            for r in rows(
                "MATCH (n:FAQ) RETURN n.id AS id, n.intent_id AS intent, "
                "n.question AS question, n.answer AS answer, n.examples AS examples "
                "ORDER BY n.id"
            )
        ]

        templates = [
            Template(intent=r["intent"], text=r["text"], locale=r.get("locale", "en"))
            for r in rows(
                "MATCH (n:Template) RETURN n.intent_id AS intent, "
                "n.text AS text, n.locale AS locale ORDER BY n.intent_id, n.locale"
            )
        ]

        # Domain entities: any node whose labels are NOT one of the core kinds
        core = {"State", "Intent", "Transition", "FAQ", "Template"}
        ent_rows = rows("MATCH (n) RETURN labels(n) AS labels, n.id AS id, n AS node")
        entities: list[Entity] = []
        for er in ent_rows:
            labels = [lbl for lbl in er["labels"] if lbl not in core]
            if not labels or not er.get("id"):
                continue
            node = er["node"]
            props = {k: v for k, v in node.items() if k not in ("id", "label") and v is not None}
            entities.append(
                Entity(
                    id=er["id"],
                    type=labels[0],
                    label=node.get("label"),
                    properties=props,
                )
            )

        relation_rows = rows(
            "MATCH (a)-[r]->(b) WHERE type(r) <> 'TRANSITIONS' AND type(r) <> 'HAS_INTENT' "
            "RETURN a.id AS frm, type(r) AS type, b.id AS to "
            "ORDER BY a.id, type(r), b.id"
        )
        relations = [
            Relation(**{"from": r["frm"], "type": r["type"], "to": r["to"]}) for r in relation_rows
        ]

        return KGData(
            version="1.0",
            namespace=DEFAULT_NAMESPACE,
            states=states,
            intents=intents,
            transitions=transitions,
            faqs=faqs,
            templates=templates,
            entities=entities,
            relations=relations,
        )
