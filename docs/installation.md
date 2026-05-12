# Installation

## From source (development)

```bash
git clone https://github.com/Gabriel382/KGConversationalAI
cd KGConversationalAI
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Optional extras

| Extra         | What it brings                              |
|---------------|---------------------------------------------|
| `[voice]`     | Whisper, sounddevice, WebRTC VAD, pyttsx3   |
| `[nlu]`       | Transformers (for zero-shot intent)         |
| `[embeddings]`| sentence-transformers + MiniLM model        |
| `[kg]`        | rdflib + jsonschema                         |
| `[neo4j]`     | Neo4j Python driver                         |
| `[web]`       | Gradio + Streamlit + PyVis                  |
| `[api]`       | OpenRouter (none currently — pure requests) |
| `[dev]`       | All of the above + pytest/ruff/mypy         |

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d
# chat:  http://localhost:7860
# admin: http://localhost:8501
# neo4j: http://localhost:7474   (neo4j / kgconvai)
```
