"""Tests for the improved OpenRouter error messages."""

from __future__ import annotations

import requests

from kgconvai.llm.openrouter import OpenRouterLLM


class _FakeResp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_429_returns_rate_limit_message(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResp(429))
    out = OpenRouterLLM(api_key="sk-or-v1-test").generate([{"role": "user", "content": "hi"}])
    assert "rate-limit" in out.lower() or "rate" in out.lower()


def test_401_returns_unauthorized_message(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResp(401))
    out = OpenRouterLLM(api_key="sk-or-v1-test").generate([{"role": "user", "content": "hi"}])
    assert "key" in out.lower() or "unauthor" in out.lower()


def test_404_returns_model_not_found_message(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResp(404))
    out = OpenRouterLLM(api_key="sk-or-v1-test", default_model="bogus/model").generate(
        [{"role": "user", "content": "hi"}], model="bogus/model"
    )
    assert "bogus/model" in out
