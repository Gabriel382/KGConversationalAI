# Backends

## RDFBackend (rdflib)

```python
from kgconvai.kg.schema import KGData
from kgconvai.kg.rdf_backend import RDFBackend

data = KGData.from_json("dialogue_graph/kg.json")
graph = RDFBackend(ontology_paths=["ontology/core.ttl"]).import_(data)

rows = graph.query("""
  PREFIX kgc: <http://kgconvai.org/core#>
  SELECT ?from ?intent ?to WHERE {
    ?t a kgc:Transition ;
       kgc:hasFromState ?from ;
       kgc:triggersIntent ?intent ;
       kgc:hasToState ?to .
  }
""")
```

## Neo4jBackend

```python
from kgconvai.kg.schema import KGData
from kgconvai.kg.neo4j_backend import Neo4jBackend

data = KGData.from_json("dialogue_graph/kg.json")
with Neo4jBackend("bolt://localhost:7687", "neo4j", "kgconvai") as be:
    g = be.import_(data)
    rows = g.query(
        "MATCH (a:State)-[r:TRANSITIONS]->(b:State) "
        "RETURN a.id AS from, r.intent AS intent, b.id AS to"
    )
```

## Round-trip

```bash
kgconvai kg export --backend rdf --from dialogue_graph/kg.json --to /tmp/rt.json
kgconvai kg diff dialogue_graph/kg.json /tmp/rt.json
# -> identical
```
