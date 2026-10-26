from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import types

from lab.config import Settings
from lab.providers.base import CompletionResult


class GeminiProvider:
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def complete(self, *, system: str, user: str) -> CompletionResult:
        started = time.perf_counter()
        try:
            config_kwargs: dict[str, Any] = {
                "system_instruction": system,
                "temperature": self._settings.temperature,
                "top_p": self._settings.top_p,
            }
            if self._settings.max_output_tokens is not None:
                config_kwargs["max_output_tokens"] = self._settings.max_output_tokens
            response = self._client.models.generate_content(
                model=self._settings.gemini_model,
                contents=user,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            return CompletionResult(
                text=response.text or "",
                latency_ms=latency_ms,
                usage=_usage_from_gemini(response.usage_metadata),
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return CompletionResult(text="", latency_ms=latency_ms, error=type(exc).__name__)


def _usage_from_gemini(metadata: Any) -> dict[str, Any]:
    if metadata is None:
        return {}
    return {
        "prompt_tokens": getattr(metadata, "prompt_token_count", None),
        "completion_tokens": getattr(metadata, "candidates_token_count", None),
        "total_tokens": getattr(metadata, "total_token_count", None),
    }
