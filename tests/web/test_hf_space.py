"""Hugging Face Space sanity tests: app.py is syntactically valid and the
Space README has the required YAML frontmatter for HF to render the metadata."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HF = ROOT / "huggingface"


def test_app_py_compiles():
    import py_compile

    py_compile.compile(str(HF / "app.py"), doraise=True)


def test_space_readme_has_required_metadata():
    text = (HF / "README.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    metadata, _ = text.split("---", 2)[1:]  # naive but enough for this check
    # Required fields for an HF Space
    for key in ("title", "sdk", "app_file"):
        assert re.search(rf"^{key}\s*:", metadata, re.MULTILINE), f"missing '{key}'"
