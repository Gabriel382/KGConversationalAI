# Web interfaces

Two complementary UIs ship with the package.

## Gradio chat

```bash
kgconvai web chat
```

A simple chat box at `http://localhost:7860`. Each browser session has its
own `DialogueSession`, so a single deployed instance can serve multiple
users without state leaking between them.

The same module also powers the bundled Hugging Face Space scaffolding in
`huggingface/`.

## Streamlit admin

```bash
kgconvai web admin
```

At `http://localhost:8501`:

- **Graph** tab: PyVis-rendered dialogue graph. Blue = regular state,
  green = "requires knowledge" state, red = terminal.
- **States / Intents / Transitions / FAQ / Templates** tabs: editable
  Streamlit data-editors backed by the canonical schema. Edits are validated
  against `schemas/kgconvai.schema.json` before save, so invalid input never
  reaches disk.
- **Raw JSON** tab: the canonicalised JSON view (read-only).
