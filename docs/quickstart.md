# Quickstart

## Install

```bash
pip install -e ".[dev,web]"
```

That gives you the package, the dev tools, and the Gradio + Streamlit
front-ends. For voice, add `[voice]`. For Neo4j, add `[neo4j]`.

## Validate the bundled knowledge graph

```bash
kgconvai kg validate dialogue_graph/kg.json
```

Output:

```
ok dialogue_graph/kg.json: 6 states, 9 intents, 13 transitions, 9 faqs, 7 templates
```

## Talk to the agent in the browser

```bash
kgconvai web chat
```

Opens at `http://localhost:7860`. Each browser session has its own
`DialogueSession`, so you can have multiple parallel conversations.

## Edit the knowledge graph visually

```bash
kgconvai web admin
```

Opens at `http://localhost:8501`. You get tabs for every section of
`kg.json`, a PyVis dialogue-graph visualisation, and validate-before-save.

## Round-trip JSON through Neo4j

```bash
docker compose -f docker/docker-compose.yml up -d
kgconvai kg export --backend neo4j --from dialogue_graph/kg.json --to /tmp/rt.json
kgconvai kg diff dialogue_graph/kg.json /tmp/rt.json
# -> identical
```

Browse the imported graph at `http://localhost:7474` (login: neo4j / kgconvai).

## Run the evaluation

```bash
kgconvai eval intents --classifier substring --no-show-examples
kgconvai eval faq --classifier substring --no-show-examples
```
