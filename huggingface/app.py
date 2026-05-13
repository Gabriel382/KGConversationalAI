"""Hugging Face Space entry point.

Builds the Gradio chat demo with the default canonical dialogue graph and
launches it. Visitors can paste their own OpenRouter API key in the UI to
get LLM-generated replies; the Space defaults to template mode otherwise.

To deploy: see huggingface/README.md.
"""

from __future__ import annotations

import os
from pathlib import Path

from kgconvai.web.chat import build_chat

DATA = Path(os.environ.get("KGCONVAI_DATA", "dialogue_graph/kg.json"))
MODE = os.environ.get("KGCONVAI_LLM_MODE", "template")

demo = build_chat(DATA, mode=MODE)
# Disable the auto-generated API info / OpenAPI introspection so Gradio
# doesn't trip over the schemas it derives from our Pydantic models.
demo.queue(api_open=False)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
    )
