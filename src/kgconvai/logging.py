"""Structured logging via structlog.

Call :func:`configure_logging` once at process start (the CLI does this for
you). The library itself emits events with ``log.info(event, **kwargs)``; the
configured renderer turns those into pretty console output in interactive
sessions or JSON lines in production.
"""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog

LogFormat = Literal["console", "json"]


def configure_logging(level: str = "INFO", fmt: LogFormat = "console") -> None:
    """Configure stdlib logging + structlog with a single processor chain."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level.upper(),
    )

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: object  # narrow renderer types; just need __call__ for structlog
    if fmt == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger; ``name`` is conventionally ``__name__``."""
    return structlog.get_logger(name)
