"""sentence-transformer retriever tests using a fake encoder."""

from __future__ import annotations

import math

from kgconvai.nlu.embeddings import EmbeddingRetriever


class FakeEncoder:
    """Deterministic encoder: each unique character -> a basis vector."""

    def encode(self, texts: list[str]) -> list[list[float]]:
        alphabet = "abcdefghijklmnopqrstuvwxyz "
        vecs = []
        for t in texts:
            counts = [0.0] * len(alphabet)
            for ch in t.lower():
                if ch in alphabet:
                    counts[alphabet.index(ch)] += 1.0
            n = math.sqrt(sum(x * x for x in counts)) or 1.0
            vecs.append([x / n for x in counts])
        return vecs


def test_embedding_retriever_ranks_similar_higher():
    enc = FakeEncoder()
    retr = EmbeddingRetriever(enc)
    out = retr.classify(
        "what are your opening hours",
        ["opening hours", "where are you located", "cancel policy"],
    )
    assert out[0].label == "opening hours"
    # Scores monotonic
    assert out[0].score >= out[1].score >= out[2].score


def test_embedding_retriever_empty_inputs():
    retr = EmbeddingRetriever(FakeEncoder())
    assert retr.classify("", ["a"]) == []
    assert retr.classify("hi", []) == []


def test_embedding_retriever_caches_candidate_vectors():
    enc = FakeEncoder()

    calls = {"n": 0}
    original = enc.encode

    def counting_encode(texts):
        calls["n"] += 1
        return original(texts)

    enc.encode = counting_encode
    retr = EmbeddingRetriever(enc)
    candidates = ["a", "b", "c"]
    retr.classify("foo", candidates)
    retr.classify("bar", candidates)
    # 1 call to encode candidates + 2 calls for each query = 3 total
    assert calls["n"] == 3
