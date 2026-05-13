"""Live OpenRouter model catalogue.

The chat UI's model dropdown is populated from this rather than a hardcoded
list, so it stays accurate as OpenRouter adds, removes, or renames models.

If the fetch fails (no network, rate-limited, ...) we fall back to a known
set of free models so the UI is always usable.
"""

from __future__ import annotations

import requests

from kgconvai.logging import get_logger

log = get_logger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Known-working free models, used as a fallback when the live fetch fails.
FALLBACK_MODELS: list[str] = [
    "deepseek/deepseek-chat-v3.1:free",
    "deepseek/deepseek-r1:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-2-9b-it:free",
    "mistralai/mistral-7b-instruct:free",
]


def fetch_openrouter_models(
    api_key: str | None = None,
    *,
    free_only: bool = False,
    timeout_s: float = 10.0,
) -> list[str]:
    """Return the list of OpenRouter model IDs, sorted.

    Args:
        api_key: Optional OpenRouter key. If provided, the result reflects
            the models available to that account. Without a key the public
            catalogue is returned.
        free_only: If True, keep only models whose id ends in ``:free``.
        timeout_s: HTTP timeout in seconds.

    On error, returns :data:`FALLBACK_MODELS` (optionally filtered).
    """
    headers: dict[str, str] = {"User-Agent": "kgconvai/0.6"}
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    try:
        r = requests.get(OPENROUTER_MODELS_URL, headers=headers, timeout=timeout_s)
        r.raise_for_status()
        payload = r.json()
        ids = [str(m["id"]) for m in payload.get("data", []) if "id" in m]
        if not ids:
            raise ValueError("empty model list")
        if free_only:
            ids = [m for m in ids if m.endswith(":free")]
        ids.sort()
        log.info("openrouter.models.fetched", n=len(ids))
        return ids
    except Exception as exc:
        log.warning("openrouter.models.fallback", err=str(exc))
        return [m for m in FALLBACK_MODELS if not free_only or m.endswith(":free")]
