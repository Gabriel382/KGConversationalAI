"""Hugging Face Space entry point.

This file is what HF Spaces runs. It builds the Gradio chat demo with the
default canonical dialogue graph and launches it. To deploy:

1. Create a new Space (SDK: Gradio).
2. Copy the contents of this folder into the Space repo.
3. Add the repo as a Git remote and push.

See huggingface/README.md for the full deployment guide.
"""

from __future__ import annotations

import os
from pathlib import Path

from kgconvai.web.chat import build_chat

DATA = Path(os.environ.get("KGCONVAI_DATA", "dialogue_graph/kg.json"))
MODE = os.environ.get("KGCONVAI_LLM_MODE", "template")

demo = build_chat(DATA, mode=MODE)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
