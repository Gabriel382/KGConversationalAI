import pytest
import requests

from kgconvai.llm.ollama import OllamaLLM
from kgconvai.llm.openrouter import OpenRouterLLM


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_ollama_generate_success(monkeypatch):
    captured = {}

    def fake_post(url, **kw):
        captured["url"] = url
        captured["json"] = kw["json"]
        return _FakeResp({"response": "hello"})

    monkeypatch.setattr(requests, "post", fake_post)
    out = OllamaLLM().generate("hi", model="llama3")
    assert out == "hello"
    assert captured["url"].endswith("/api/generate")
    assert captured["json"]["model"] == "llama3"


def test_ollama_generate_error_returns_fallback(monkeypatch):
    def fake_post(*a, **kw):
        raise requests.ConnectionError("nope")

    monkeypatch.setattr(requests, "post", fake_post)
    out = OllamaLLM().generate("hi")
    assert "couldn't generate" in out.lower()


def test_openrouter_requires_api_key():
    with pytest.raises(ValueError):
        OpenRouterLLM(api_key="")


def test_openrouter_generate_success(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: _FakeResp({"choices": [{"message": {"content": "hi there"}}]}),
    )
    out = OpenRouterLLM(api_key="sk-test").generate([{"role": "user", "content": "hi"}])
    assert out == "hi there"


def test_openrouter_generate_handles_empty_choices(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResp({"choices": []}))
    out = OpenRouterLLM(api_key="sk-test").generate([{"role": "user", "content": "hi"}])
    assert "couldn't generate" in out.lower()
