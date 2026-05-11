"""Embedding-based FAQ retrieval.

Replaces BART-MNLI zero-shot classification (the wrong tool for semantic
similarity) with sentence-transformer embeddings + cosine similarity, which is:

* roughly **10x smaller** in model size (80 MB MiniLM vs 1.6 GB BART);
* substantially **faster** at inference time (no per-pair forward pass);
* more accurate for FAQ matching because the model is trained directly on
  semantic similarity rather than NLI.

Heavy imports are deferred so the package keeps working when
``sentence-transformers`` is not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from kgconvai.logging import get_logger
from kgconvai.nlu.classifier import Classification, Classifier

if TYPE_CHECKING:  # pragma: no cover
    pass

log = get_logger(__name__)


class TextEncoder(Protocol):
    """Anything that can produce a fixed-size numeric embedding for a string."""

    def encode(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(slots=True)
class _Cached:
    text: str
    vec: list[float]


def _cosine(a: list[float], b: list[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class SentenceTransformerEncoder:
    """Thin wrapper around ``sentence-transformers`` to satisfy ``TextEncoder``.

    Lazy-loads the model on first use.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _ensure_model(self):  # pragma: no cover - external download
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            log.info("embeddings.loading_model", model=self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        model = self._ensure_model()
        return [list(v) for v in model.encode(texts)]


class EmbeddingRetriever(Classifier):
    """Cosine-similarity retriever that implements the :class:`Classifier` protocol.

    Drop-in replacement for ``ZeroShotClassifier`` in FAQ retrieval. The
    embeddings of the *candidates* are cached on the first call with a given
    candidate set, so subsequent classifications over the same set are fast.
    """

    def __init__(self, encoder: TextEncoder) -> None:
        self.encoder = encoder
        self._cache: dict[tuple[str, ...], list[list[float]]] = {}

    def classify(self, text: str, candidates: list[str]) -> list[Classification]:
        if not text.strip() or not candidates:
            return []
        key = tuple(candidates)
        cand_vecs = self._cache.get(key)
        if cand_vecs is None:
            cand_vecs = self.encoder.encode(candidates)
            self._cache[key] = cand_vecs
        query_vec = self.encoder.encode([text])[0]
        scored = [
            Classification(label=c, score=_cosine(query_vec, v))
            for c, v in zip(candidates, cand_vecs, strict=True)
        ]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
