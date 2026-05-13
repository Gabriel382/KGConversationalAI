"""Tests for the live OpenRouter model fetcher."""

from __future__ import annotations

import requests

from kgconvai.web._openrouter_models import (
    FALLBACK_MODELS,
    fetch_openrouter_models,
)


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_fetch_models_parses_id_field(monkeypatch):
    fake = {
        "data": [
            {"id": "openai/gpt-4o-mini"},
            {"id": "deepseek/deepseek-chat-v3.1:free"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free"},
        ]
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResp(fake))
    out = fetch_openrouter_models()
    # Sorted alphabetically
    assert out == sorted(out)
    assert "openai/gpt-4o-mini" in out
    assert "deepseek/deepseek-chat-v3.1:free" in out


def test_fetch_models_free_only_filter(monkeypatch):
    fake = {
        "data": [
            {"id": "openai/gpt-4o-mini"},
            {"id": "deepseek/deepseek-chat-v3.1:free"},
        ]
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResp(fake))
    out = fetch_openrouter_models(free_only=True)
    assert all(m.endswith(":free") for m in out)
    assert "openai/gpt-4o-mini" not in out


def test_fetch_models_falls_back_on_network_error(monkeypatch):
    def boom(*a, **kw):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", boom)
    out = fetch_openrouter_models()
    assert out == FALLBACK_MODELS


def test_fetch_models_falls_back_on_empty_response(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResp({"data": []}))
    out = fetch_openrouter_models()
    assert out == FALLBACK_MODELS


def test_fetch_models_uses_api_key_in_header(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, timeout=None):
        captured["headers"] = headers or {}
        return _FakeResp({"data": [{"id": "a"}]})

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_openrouter_models(api_key="sk-or-v1-test")
    assert captured["headers"].get("Authorization") == "Bearer sk-or-v1-test"


def test_fetch_models_omits_auth_header_when_no_key(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, timeout=None):
        captured["headers"] = headers or {}
        return _FakeResp({"data": [{"id": "a"}]})

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_openrouter_models(api_key=None)
    assert "Authorization" not in captured["headers"]
