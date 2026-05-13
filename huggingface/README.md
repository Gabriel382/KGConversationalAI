---
title: KGConvAI Demo
emoji: 🎤
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.49.0
app_file: app.py
pinned: false
license: mit
short_description: Graph-driven voice agent with a TAO control loop.
---

# KGConvAI demo on Hugging Face Spaces

This Space wraps the [Gabriel382/KGConversationalAI](https://github.com/Gabriel382/KGConversationalAI)
agent in a Gradio chat UI. Type a message and the agent walks the dialogue
graph (greet → ask information → provide information → end, etc.).

## What's running

The default deployment uses:

- The canonical `dialogue_graph/kg.json` bundled with the package.
- `--mode template` (no external LLM calls). For Ollama or OpenRouter, set
  `KGCONVAI_LLM_MODE=local` or `api` in the Space secrets.

## Deploying your own copy

```bash
git clone https://huggingface.co/spaces/<your-user>/<your-space>
cd <your-space>
# Copy our app.py + requirements.txt + this README
cp ../KGConversationalAI/huggingface/{app.py,requirements.txt,README.md} .
git add . && git commit -m "Initial deploy"
git push
```

The Space will build automatically (~3 minutes) and the URL becomes live.

## Switching to API mode

In the Space settings, add a repository secret:

| Name                            | Value              |
|---------------------------------|--------------------|
| `KGCONVAI_LLM_MODE`             | `api`              |
| `KGCONVAI_OPENROUTER_API_KEY`   | `sk-or-v1-...`     |

Then restart the Space.
