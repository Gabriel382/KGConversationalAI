"""kgconvai - graph-driven voice agent with a Thought-Action-Observation loop.

Public API:
    >>> from kgconvai import Agent, DialogueSession, Settings

The high-level building blocks are intentionally small so the package can be
used either as a CLI tool (``python -m kgconvai`` / ``kgconvai run``) or as a
library inside another application.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _v

from kgconvai.agent import Agent
from kgconvai.config import Settings
from kgconvai.state import DialogueSession, Turn

try:
    __version__ = _v("kgconvai")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["Agent", "DialogueSession", "Settings", "Turn", "__version__"]
